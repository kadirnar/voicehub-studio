"""Hardware and dependency inspection without allocating a model."""

from __future__ import annotations

import platform
import shutil
import subprocess
import sys
from importlib import metadata
from pathlib import Path
from typing import Any


def _package_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def _command_output(arguments: list[str], timeout: float = 3.0) -> str | None:
    try:
        completed = subprocess.run(
            arguments,
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return completed.stdout.strip()
    except (FileNotFoundError, subprocess.SubprocessError):
        return None


def _nvidia_devices() -> list[dict[str, Any]]:
    output = _command_output(
        [
            "nvidia-smi",
            "--query-gpu=index,name,memory.total,memory.free,driver_version,temperature.gpu,utilization.gpu",
            "--format=csv,noheader,nounits",
        ]
    )
    if not output:
        return []
    devices = []
    for line in output.splitlines():
        parts = [part.strip() for part in line.split(",")]
        if len(parts) < 7:
            continue
        devices.append(
            {
                "backend": "cuda",
                "index": int(parts[0]),
                "name": parts[1],
                "memory_total_mb": int(parts[2]),
                "memory_free_mb": int(parts[3]),
                "driver": parts[4],
                "temperature_c": int(parts[5]),
                "utilization_percent": int(parts[6]),
                "available_to_torch": False,
            }
        )
    return devices


def inspect_hardware(data_path: str | Path | None = None) -> dict[str, Any]:
    """Return CPU, accelerator, dependency, and storage status."""
    accelerators = _nvidia_devices()
    torch_info: dict[str, Any] = {
        "installed": False,
        "version": _package_version("torch"),
        "cuda_version": None,
        "hip_version": None,
    }
    try:
        import torch

        torch_info.update(
            {
                "installed": True,
                "version": torch.__version__,
                "cuda_version": getattr(torch.version, "cuda", None),
                "hip_version": getattr(torch.version, "hip", None),
                "cuda_available": bool(torch.cuda.is_available()),
                "mps_available": bool(
                    hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
                ),
                "xpu_available": bool(
                    hasattr(torch, "xpu") and torch.xpu.is_available()
                ),
            }
        )
        if torch.cuda.is_available():
            torch_devices: list[dict[str, Any]] = []
            for index in range(torch.cuda.device_count()):
                properties = torch.cuda.get_device_properties(index)
                free_bytes, total_bytes = torch.cuda.mem_get_info(index)
                torch_devices.append(
                    {
                        "backend": "cuda",
                        "index": index,
                        "name": properties.name,
                        "memory_total_mb": round(total_bytes / 1024**2),
                        "memory_free_mb": round(free_bytes / 1024**2),
                        "compute_capability": f"{properties.major}.{properties.minor}",
                        "bf16": bool(torch.cuda.is_bf16_supported()),
                        "available_to_torch": True,
                    }
                )
            by_index = {item["index"]: item for item in accelerators}
            for device in torch_devices:
                previous = by_index.get(device["index"], {})
                previous.update(device)
                by_index[device["index"]] = previous
            accelerators = list(by_index.values())
    except Exception as error:
        torch_info["error"] = str(error)

    ffmpeg_version = _command_output(["ffmpeg", "-version"])
    ffprobe_version = _command_output(["ffprobe", "-version"])
    disk: dict[str, Any] | None = None
    if data_path is not None:
        target = Path(data_path)
        target.mkdir(parents=True, exist_ok=True)
        usage = shutil.disk_usage(target)
        disk = {
            "path": str(target),
            "total_bytes": usage.total,
            "used_bytes": usage.used,
            "free_bytes": usage.free,
        }

    cpu_count = __import__("os").cpu_count() or 1
    return {
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "python": sys.version.split()[0],
            "cpu": platform.processor() or platform.machine(),
            "cpu_threads": cpu_count,
            "memory_total_bytes": _linux_memory_total(),
        },
        "torch": torch_info,
        "accelerators": accelerators,
        "devices": _device_choices(torch_info, accelerators),
        "dependencies": {
            "voicehub": _package_version("voicehub"),
            "fastapi": _package_version("fastapi"),
            "ffmpeg": ffmpeg_version.splitlines()[0] if ffmpeg_version else None,
            "ffprobe": ffprobe_version.splitlines()[0] if ffprobe_version else None,
            "pywebview": _package_version("pywebview"),
        },
        "disk": disk,
    }


def _linux_memory_total() -> int | None:
    try:
        for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
            if line.startswith("MemTotal:"):
                return int(line.split()[1]) * 1024
    except (OSError, ValueError, IndexError):
        pass
    return None


def _device_choices(
    torch_info: dict[str, Any], accelerators: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    choices = [
        {
            "id": "cpu",
            "label": "CPU",
            "available": True,
            "recommended_dtype": "float32",
        }
    ]
    if accelerators:
        for accelerator in accelerators:
            index = accelerator.get("index", 0)
            choices.append(
                {
                    "id": "cuda" if index == 0 else f"cuda:{index}",
                    "label": accelerator.get("name", f"CUDA GPU {index}"),
                    "available": bool(accelerator.get("available_to_torch")),
                    "detected_by_driver": True,
                    "recommended_dtype": "bfloat16"
                    if accelerator.get("bf16", True)
                    else "float16",
                    "memory_total_mb": accelerator.get("memory_total_mb"),
                    "memory_free_mb": accelerator.get("memory_free_mb"),
                }
            )
    if torch_info.get("mps_available"):
        choices.append(
            {
                "id": "mps",
                "label": "Apple Metal",
                "available": True,
                "recommended_dtype": "float16",
            }
        )
    if torch_info.get("xpu_available"):
        choices.append(
            {
                "id": "xpu",
                "label": "Intel XPU",
                "available": True,
                "recommended_dtype": "bfloat16",
            }
        )
    return choices


def resolve_device(requested: str) -> str:
    if requested != "auto":
        return requested
    try:
        import torch

        if torch.cuda.is_available():
            return "cuda"
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
        if hasattr(torch, "xpu") and torch.xpu.is_available():
            return "xpu"
    except Exception:
        pass
    return "cpu"
