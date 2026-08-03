"""VoiceHub fine-tuning job orchestration."""

from __future__ import annotations

import gc
from pathlib import Path
from typing import Any

from voicehub_studio.config import AppPaths
from voicehub_studio.db import Database, utc_now
from voicehub_studio.services.hardware import resolve_device
from voicehub_studio.services.jobs import EventBus, JobCancelled, JobContext
from voicehub_studio.services.runtime import VoiceHubRuntimeManager


class TrainingService:
    """Runs model-owned VoiceHub datasets and Trainer contracts."""

    def __init__(
        self,
        database: Database,
        paths: AppPaths,
        runtime: VoiceHubRuntimeManager,
        events: EventBus,
    ):
        self.database = database
        self.paths = paths
        self.runtime = runtime
        self.events = events

    def handle(self, context: JobContext, payload: dict[str, Any]) -> dict[str, Any]:
        training_id = payload["training_id"]
        run = self.database.get("training_runs", training_id)
        if run is None:
            raise KeyError(f"Training run {training_id!r} no longer exists.")
        self._update(training_id, status="running", started_at=utc_now(), error=None)
        config = dict(run["config"])
        model = None
        trainer = None
        try:
            context.update(0.02, "Validating manifests")
            train_manifest = Path(run["train_manifest"]).expanduser().resolve()
            if not train_manifest.is_file():
                raise FileNotFoundError(
                    f"Training manifest was not found: {train_manifest}"
                )
            eval_manifest = None
            if run.get("eval_manifest"):
                eval_manifest = Path(run["eval_manifest"]).expanduser().resolve()
                if not eval_manifest.is_file():
                    raise FileNotFoundError(
                        f"Evaluation manifest was not found: {eval_manifest}"
                    )
            output_dir = Path(run["output_dir"]).expanduser().resolve()
            output_dir.mkdir(parents=True, exist_ok=True)
            device = resolve_device(run["device"])

            # Training and inference weights should not compete for accelerator memory.
            self.runtime.unload()
            context.update(0.06, "Loading VoiceHub training contract")
            from voicehub import (
                AutoModelForTextToSpeech,
                Trainer,
                TrainerCallback,
                TrainingArguments,
                TTSOptimizationConfig,
            )

            model_config = dict(config.get("model_config", {}))
            optimization_values = dict(config.get("optimization", {}))
            load_kwargs: dict[str, Any] = {
                "model_type": run["model_type"],
                "device": device,
                "lazy_load": True,
            }
            if model_config:
                load_kwargs["config_kwargs"] = model_config
            model = AutoModelForTextToSpeech.from_pretrained(
                run["checkpoint"], **load_kwargs
            )
            model.validate_training_support()
            context.update(0.14, "Preparing training data")
            dataset_kwargs = dict(config.get("dataset", {}))
            train_dataset = model.create_training_dataset(
                train_manifest,
                validate_audio_files=bool(
                    dataset_kwargs.pop("validate_audio_files", True)
                ),
                **dataset_kwargs,
            )
            eval_dataset = (
                model.create_training_dataset(eval_manifest, validate_audio_files=True)
                if eval_manifest is not None
                else None
            )
            if len(train_dataset) == 0:
                raise ValueError("The training manifest produced an empty dataset.")

            argument_values = dict(config.get("training_arguments", {}))
            if (
                "max_steps" not in argument_values
                and "num_train_epochs" not in argument_values
            ):
                argument_values["max_steps"] = 1
            argument_values.setdefault("per_device_train_batch_size", 1)
            argument_values.setdefault("per_device_eval_batch_size", 1)
            argument_values.setdefault("gradient_accumulation_steps", 1)
            argument_values.setdefault("learning_rate", 5e-5)
            argument_values.setdefault("logging_steps", 1)
            argument_values.setdefault("logging_first_step", True)
            argument_values.setdefault("save_strategy", "steps")
            argument_values.setdefault(
                "save_steps", max(1, int(argument_values.get("max_steps", 1)))
            )
            argument_values.setdefault("save_total_limit", 2)
            argument_values.setdefault("report_to", [])
            argument_values.setdefault("seed", 42)
            argument_values.setdefault("data_seed", argument_values["seed"])
            argument_values.setdefault("use_cpu", device == "cpu")
            if eval_dataset is not None:
                argument_values.setdefault("eval_strategy", "steps")
                argument_values.setdefault(
                    "eval_steps", argument_values["logging_steps"]
                )
            arguments = TrainingArguments(output_dir=str(output_dir), **argument_values)
            total_steps = arguments.max_steps if arguments.max_steps > 0 else None
            self._update(training_id, total_steps=total_steps)

            service = self

            class ProgressCallback(TrainerCallback):
                def on_train_begin(self, args, state, control, **kwargs):
                    service._update(
                        training_id, total_steps=state.max_steps or total_steps
                    )
                    context.update(0.24, "Training started")
                    return control

                def on_step_end(self, args, state, control, **kwargs):
                    denominator = max(1, state.max_steps or total_steps or 1)
                    fractional = min(1.0, state.global_step / denominator)
                    service._update(
                        training_id,
                        current_step=state.global_step,
                        total_steps=denominator,
                        progress=fractional,
                    )
                    context.update(
                        0.25 + fractional * 0.65,
                        f"Training step {state.global_step}/{denominator}",
                    )
                    return control

                def on_log(self, args, state, control, logs=None, **kwargs):
                    if logs and "loss" in logs:
                        service._update(training_id, training_loss=float(logs["loss"]))
                    return control

            optimization_config = (
                TTSOptimizationConfig(**optimization_values)
                if optimization_values
                else None
            )
            trainer = Trainer(
                model=model,
                args=arguments,
                train_dataset=train_dataset,
                eval_dataset=eval_dataset,
                callbacks=[ProgressCallback()],
                optimization_config=optimization_config,
            )
            context.update(0.22, "Loading trainable model graph")
            result = trainer.train(
                resume_from_checkpoint=config.get("resume_from_checkpoint", False)
            )
            context.update(0.92, "Saving portable model")
            final_path = output_dir / "final"
            trainer.save_model(final_path)
            metrics = dict(getattr(result, "metrics", {}) or {})
            loss = float(result.training_loss)
            updated = self._update(
                training_id,
                status="completed",
                progress=1.0,
                current_step=int(getattr(trainer.state, "global_step", 0)),
                total_steps=int(getattr(trainer.state, "max_steps", 0)) or total_steps,
                training_loss=loss,
                completed_at=utc_now(),
            )
            return {
                "training_id": training_id,
                "artifact": str(final_path),
                "training_loss": loss,
                "metrics": metrics,
                "training": updated,
            }
        except Exception as error:
            self._update(
                training_id,
                status="cancelled" if isinstance(error, JobCancelled) else "failed",
                error=str(error)[-8000:],
                completed_at=utc_now(),
            )
            raise
        finally:
            del trainer
            del model
            gc.collect()
            try:
                import torch

                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except Exception:
                pass

    def _update(self, training_id: str, **values: Any) -> dict[str, Any] | None:
        updated = self.database.update("training_runs", training_id, values)
        if updated:
            self.events.publish("training.updated", updated)
        return updated
