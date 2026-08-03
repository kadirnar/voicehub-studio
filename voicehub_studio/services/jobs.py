"""Persistent background queue with a lightweight event stream."""

from __future__ import annotations

import queue
import threading
import traceback
from collections import deque
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from voicehub_studio.db import Database, utc_now

JobHandler = Callable[["JobContext", dict[str, Any]], Mapping[str, Any] | None]


class JobCancelled(RuntimeError):
    pass


class EventBus:
    """Bounded event log suitable for polling and server-sent events."""

    def __init__(self, maximum: int = 2000):
        self._events: deque[dict[str, Any]] = deque(maxlen=maximum)
        self._sequence = 0
        self._lock = threading.RLock()

    def publish(self, kind: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        with self._lock:
            self._sequence += 1
            event = {
                "id": self._sequence,
                "kind": kind,
                "payload": dict(payload),
                "created_at": utc_now(),
            }
            self._events.append(event)
            return event

    def since(self, sequence: int) -> list[dict[str, Any]]:
        with self._lock:
            return [dict(event) for event in self._events if event["id"] > sequence]

    @property
    def sequence(self) -> int:
        with self._lock:
            return self._sequence


@dataclass
class JobContext:
    queue: JobQueue
    job_id: str

    def update(
        self, progress: float, stage: str, **values: Any
    ) -> dict[str, Any] | None:
        normalized = min(1.0, max(0.0, float(progress)))
        updated = self.queue.database.update(
            "jobs",
            self.job_id,
            {"progress": normalized, "stage": stage, **values},
        )
        if updated:
            self.queue.events.publish("job.updated", updated)
        self.check_cancelled()
        return updated

    def check_cancelled(self) -> None:
        job = self.queue.database.get("jobs", self.job_id)
        if job and job.get("cancel_requested"):
            raise JobCancelled("Job cancellation was requested.")


class JobQueue:
    """Serial-by-default worker queue to avoid competing GPU allocations."""

    def __init__(self, database: Database, events: EventBus, workers: int = 1):
        if not 1 <= workers <= 8:
            raise ValueError("workers must be between 1 and 8")
        self.database = database
        self.events = events
        self.workers = workers
        self._handlers: dict[str, JobHandler] = {}
        self._queue: queue.Queue[str | None] = queue.Queue()
        self._threads: list[threading.Thread] = []
        self._started = False
        self._lock = threading.RLock()

    def register(self, kind: str, handler: JobHandler) -> None:
        with self._lock:
            if kind in self._handlers:
                raise ValueError(f"A handler is already registered for {kind!r}.")
            self._handlers[kind] = handler

    def start(self) -> None:
        with self._lock:
            if self._started:
                return
            self._started = True
            for index in range(self.workers):
                thread = threading.Thread(
                    target=self._worker,
                    name=f"voicehub-job-{index + 1}",
                    daemon=True,
                )
                self._threads.append(thread)
                thread.start()
            self._recover_interrupted_jobs()

    def _recover_interrupted_jobs(self) -> None:
        message = "Application stopped while this job was running."
        interrupted = self.database.list(
            "jobs", limit=1000, where="status = ?", parameters=("running",)
        )
        for job in interrupted:
            updated = self.database.update(
                "jobs",
                job["id"],
                {
                    "status": "failed",
                    "stage": "Interrupted",
                    "error": message,
                    "completed_at": utc_now(),
                },
            )
            self._sync_owner_status(job, "failed", message)
            if updated:
                self.events.publish("job.updated", updated)

        # Jobs that had not started are safe to resume after handlers are registered.
        queued = self.database.list(
            "jobs", limit=1000, where="status = ?", parameters=("queued",)
        )
        for job in reversed(queued):
            self._queue.put(job["id"])

    def submit(self, kind: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        if kind not in self._handlers:
            raise ValueError(f"No job handler is registered for {kind!r}.")
        if not self._started:
            self.start()
        job = self.database.create_job(kind, payload)
        self._queue.put(job["id"])
        self.events.publish("job.created", job)
        return job

    def cancel(self, job_id: str) -> dict[str, Any]:
        job = self.database.get("jobs", job_id)
        if job is None:
            raise KeyError(job_id)
        if job["status"] in {"completed", "failed", "cancelled"}:
            return job
        updated = self.database.update(
            "jobs",
            job_id,
            {"cancel_requested": 1, "stage": "Cancellation requested"},
        )
        assert updated is not None
        self.events.publish("job.updated", updated)
        return updated

    def _worker(self) -> None:
        while True:
            job_id = self._queue.get()
            if job_id is None:
                self._queue.task_done()
                return
            try:
                self._run_job(job_id)
            finally:
                self._queue.task_done()

    def _run_job(self, job_id: str) -> None:
        job = self.database.get("jobs", job_id)
        if job is None:
            return
        if job.get("cancel_requested"):
            updated = self.database.update(
                "jobs",
                job_id,
                {
                    "status": "cancelled",
                    "progress": 0.0,
                    "stage": "Cancelled",
                    "completed_at": utc_now(),
                },
            )
            if updated:
                self.events.publish("job.updated", updated)
            self._sync_owner_status(job, "cancelled", "Job cancellation was requested.")
            return
        handler = self._handlers.get(job["kind"])
        if handler is None:
            self._fail(job_id, f"No handler is registered for {job['kind']!r}.")
            return
        updated = self.database.update(
            "jobs",
            job_id,
            {
                "status": "running",
                "progress": 0.01,
                "stage": "Starting",
                "started_at": utc_now(),
            },
        )
        if updated:
            self.events.publish("job.updated", updated)
        context = JobContext(self, job_id)
        try:
            result = dict(handler(context, dict(job["payload"])) or {})
            context.check_cancelled()
            updated = self.database.update(
                "jobs",
                job_id,
                {
                    "status": "completed",
                    "progress": 1.0,
                    "stage": "Complete",
                    "result": result,
                    "completed_at": utc_now(),
                },
            )
        except JobCancelled as error:
            updated = self.database.update(
                "jobs",
                job_id,
                {
                    "status": "cancelled",
                    "stage": "Cancelled",
                    "error": str(error),
                    "completed_at": utc_now(),
                },
            )
            self._sync_owner_status(job, "cancelled", str(error))
        except Exception as error:
            details = "".join(
                traceback.format_exception_only(type(error), error)
            ).strip()
            updated = self.database.update(
                "jobs",
                job_id,
                {
                    "status": "failed",
                    "stage": "Failed",
                    "error": details[-8000:],
                    "completed_at": utc_now(),
                },
            )
        if updated:
            self.events.publish("job.updated", updated)

    def _sync_owner_status(
        self, job: Mapping[str, Any], status: str, error: str
    ) -> None:
        """Keep generation/training records aligned with terminal queue states."""
        payload = dict(job.get("payload") or {})
        if job.get("kind") == "tts.generate" and payload.get("generation_id"):
            updated = self.database.update(
                "generations",
                payload["generation_id"],
                {"status": status, "error": error, "completed_at": utc_now()},
            )
            if updated:
                self.events.publish("generation.updated", updated)
        elif job.get("kind") == "model.train" and payload.get("training_id"):
            updated = self.database.update(
                "training_runs",
                payload["training_id"],
                {"status": status, "error": error, "completed_at": utc_now()},
            )
            if updated:
                self.events.publish("training.updated", updated)

    def _fail(self, job_id: str, message: str) -> None:
        updated = self.database.update(
            "jobs",
            job_id,
            {
                "status": "failed",
                "stage": "Failed",
                "error": message,
                "completed_at": utc_now(),
            },
        )
        if updated:
            self.events.publish("job.updated", updated)

    def shutdown(self, wait: bool = False) -> None:
        with self._lock:
            if not self._started:
                return
            for _ in self._threads:
                self._queue.put(None)
            if wait:
                for thread in self._threads:
                    thread.join(timeout=10)
            self._threads.clear()
            self._started = False
