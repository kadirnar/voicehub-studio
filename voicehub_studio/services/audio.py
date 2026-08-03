"""Non-destructive audio inspection, cutting, effects, and assembly."""

from __future__ import annotations

import json
import math
import mimetypes
import re
import shutil
import struct
import subprocess
import uuid
from pathlib import Path
from typing import Any

SUPPORTED_AUDIO_EXTENSIONS = {
    ".wav",
    ".flac",
    ".mp3",
    ".ogg",
    ".opus",
    ".m4a",
    ".aac",
    ".webm",
    ".aiff",
    ".aif",
}

OUTPUT_CODEC_ARGUMENTS = {
    "wav": ["-c:a", "pcm_s16le"],
    "flac": ["-c:a", "flac"],
    "mp3": ["-c:a", "libmp3lame", "-q:a", "2"],
    "ogg": ["-c:a", "libvorbis", "-q:a", "6"],
}


class AudioProcessingError(RuntimeError):
    pass


def safe_stem(filename: str) -> str:
    stem = Path(filename).stem.strip() or "audio"
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", stem).strip("-._")
    return (cleaned or "audio")[:100]


def unique_audio_path(directory: Path, name: str, output_format: str) -> Path:
    if output_format not in OUTPUT_CODEC_ARGUMENTS:
        raise ValueError(f"Unsupported output format: {output_format}")
    directory.mkdir(parents=True, exist_ok=True)
    return directory / f"{safe_stem(name)}-{uuid.uuid4().hex[:10]}.{output_format}"


def _run(
    arguments: list[str], *, timeout: float | None = None
) -> subprocess.CompletedProcess[bytes]:
    try:
        completed = subprocess.run(
            arguments,
            check=False,
            capture_output=True,
            timeout=timeout,
        )
    except FileNotFoundError as error:
        raise AudioProcessingError(
            f"Required audio tool is not installed: {arguments[0]}"
        ) from error
    except subprocess.TimeoutExpired as error:
        raise AudioProcessingError("Audio processing timed out.") from error
    if completed.returncode:
        message = completed.stderr.decode("utf-8", errors="replace").strip()
        raise AudioProcessingError(message[-4000:] or "Audio processing failed.")
    return completed


def probe_audio(path: str | Path) -> dict[str, Any]:
    source = Path(path).expanduser()
    if not source.is_file():
        raise FileNotFoundError(source)
    completed = _run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration,format_name,bit_rate:stream=index,codec_type,codec_name,sample_rate,channels",
            "-of",
            "json",
            str(source),
        ],
        timeout=15,
    )
    payload = json.loads(completed.stdout.decode("utf-8"))
    audio_stream = next(
        (
            stream
            for stream in payload.get("streams", [])
            if stream.get("codec_type") == "audio"
        ),
        None,
    )
    if audio_stream is None:
        raise AudioProcessingError("The selected file has no audio stream.")
    duration = float(payload.get("format", {}).get("duration") or 0)
    return {
        "duration": duration,
        "sample_rate": int(audio_stream.get("sample_rate") or 0) or None,
        "channels": int(audio_stream.get("channels") or 0) or None,
        "codec": audio_stream.get("codec_name"),
        "format": payload.get("format", {}).get("format_name"),
        "bit_rate": int(payload.get("format", {}).get("bit_rate") or 0) or None,
        "size_bytes": source.stat().st_size,
        "mime_type": mimetypes.guess_type(source.name)[0] or "audio/octet-stream",
    }


def validate_audio_upload(filename: str, size_bytes: int, max_megabytes: int) -> None:
    extension = Path(filename).suffix.lower()
    if extension not in SUPPORTED_AUDIO_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_AUDIO_EXTENSIONS))
        raise ValueError(f"Unsupported audio extension. Supported: {supported}")
    if size_bytes <= 0:
        raise ValueError("The uploaded audio file is empty.")
    if size_bytes > max_megabytes * 1024 * 1024:
        raise ValueError(f"Audio upload exceeds the {max_megabytes} MB limit.")


def copy_uploaded_audio(
    source: Path, destination_directory: Path, original_name: str
) -> tuple[Path, dict[str, Any]]:
    extension = Path(original_name).suffix.lower()
    destination_directory.mkdir(parents=True, exist_ok=True)
    destination = (
        destination_directory
        / f"{safe_stem(original_name)}-{uuid.uuid4().hex[:10]}{extension}"
    )
    shutil.copyfile(source, destination)
    try:
        details = probe_audio(destination)
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    return destination, details


def _number(
    value: Any, name: str, *, minimum: float | None = None, maximum: float | None = None
) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number.")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite.")
    if minimum is not None and result < minimum:
        raise ValueError(f"{name} must be at least {minimum}.")
    if maximum is not None and result > maximum:
        raise ValueError(f"{name} must be at most {maximum}.")
    return result


def _atempo_filters(speed: float) -> list[str]:
    filters = []
    remaining = speed
    while remaining > 2.0:
        filters.append("atempo=2.0")
        remaining /= 2.0
    while remaining < 0.5:
        filters.append("atempo=0.5")
        remaining /= 0.5
    filters.append(f"atempo={remaining:.8f}")
    return filters


def _ranges_filter(ranges: list[dict[str, Any]], duration: float) -> tuple[str, str]:
    if not ranges:
        raise ValueError("At least one keep range is required.")
    normalized: list[tuple[float, float]] = []
    for range_value in ranges:
        start = _number(
            range_value.get("start", 0), "range start", minimum=0, maximum=duration
        )
        end = _number(
            range_value.get("end", duration), "range end", minimum=0, maximum=duration
        )
        if end <= start:
            raise ValueError("Every keep range must end after it starts.")
        normalized.append((start, end))
    normalized.sort()
    labels: list[str] = []
    filters: list[str] = []
    for index, (start, end) in enumerate(normalized):
        label = f"keep{index}"
        labels.append(f"[{label}]")
        filters.append(
            f"[0:a]atrim=start={start:.8f}:end={end:.8f},asetpts=PTS-STARTPTS[{label}]"
        )
    if len(labels) == 1:
        filters.append(f"{labels[0]}anull[outa]")
    else:
        filters.append(f"{''.join(labels)}concat=n={len(labels)}:v=0:a=1[outa]")
    return ";".join(filters), "[outa]"


def _remove_range_to_keep(
    operation: dict[str, Any], duration: float
) -> list[dict[str, float]]:
    start = _number(
        operation.get("start", 0), "remove start", minimum=0, maximum=duration
    )
    end = _number(
        operation.get("end", duration), "remove end", minimum=0, maximum=duration
    )
    if end <= start:
        raise ValueError("Remove selection must end after it starts.")
    ranges = []
    if start > 0:
        ranges.append({"start": 0.0, "end": start})
    if end < duration:
        ranges.append({"start": end, "end": duration})
    if not ranges:
        raise ValueError("Removing that selection would create an empty file.")
    return ranges


def process_audio(
    source_path: str | Path,
    destination_path: str | Path,
    operations: list[dict[str, Any]],
    *,
    output_format: str,
    sample_rate: int | None = None,
    channels: int | None = None,
) -> dict[str, Any]:
    """Apply a validated FFmpeg filter graph and preserve the source file."""
    source = Path(source_path)
    destination = Path(destination_path)
    if not source.is_file():
        raise FileNotFoundError(source)
    if output_format not in OUTPUT_CODEC_ARGUMENTS:
        raise ValueError("Unsupported output format.")
    details = probe_audio(source)
    duration = float(details["duration"])
    simple_filters: list[str] = []
    complex_filter: str | None = None
    map_label: str | None = None

    range_operations = [
        item for item in operations if item.get("op") in {"keep_ranges", "remove_range"}
    ]
    if len(range_operations) > 1:
        raise ValueError("Use one keep/remove operation per edit request.")
    if range_operations:
        operation = range_operations[0]
        ranges = (
            operation.get("ranges")
            if operation.get("op") == "keep_ranges"
            else _remove_range_to_keep(operation, duration)
        )
        if not isinstance(ranges, list):
            raise ValueError("keep_ranges requires a ranges list.")
        complex_filter, map_label = _ranges_filter(ranges, duration)

    for operation in operations:
        name = operation.get("op")
        if name in {"keep_ranges", "remove_range"}:
            continue
        if name == "trim":
            start = _number(
                operation.get("start", 0), "trim start", minimum=0, maximum=duration
            )
            end = _number(
                operation.get("end", duration), "trim end", minimum=0, maximum=duration
            )
            if end <= start:
                raise ValueError("Trim selection must end after it starts.")
            simple_filters.extend(
                [f"atrim=start={start:.8f}:end={end:.8f}", "asetpts=PTS-STARTPTS"]
            )
        elif name == "gain":
            decibels = _number(operation.get("db", 0), "gain", minimum=-60, maximum=30)
            simple_filters.append(f"volume={decibels:.4f}dB")
        elif name == "normalize":
            target = _number(
                operation.get("target_lufs", -16),
                "target LUFS",
                minimum=-36,
                maximum=-5,
            )
            simple_filters.append(f"loudnorm=I={target:.2f}:TP=-1.5:LRA=11")
        elif name == "fade_in":
            seconds = _number(
                operation.get("duration", 0.15),
                "fade-in duration",
                minimum=0,
                maximum=30,
            )
            simple_filters.append(f"afade=t=in:st=0:d={seconds:.6f}")
        elif name == "fade_out":
            seconds = _number(
                operation.get("duration", 0.15),
                "fade-out duration",
                minimum=0,
                maximum=30,
            )
            start = max(0.0, duration - seconds)
            simple_filters.append(f"afade=t=out:st={start:.6f}:d={seconds:.6f}")
        elif name == "denoise":
            strength = _number(
                operation.get("strength", 12), "denoise strength", minimum=0, maximum=40
            )
            simple_filters.append(f"afftdn=nr={strength:.3f}:nf=-50")
        elif name == "speed":
            speed = _number(operation.get("factor", 1), "speed", minimum=0.1, maximum=8)
            simple_filters.extend(_atempo_filters(speed))
        elif name == "pitch":
            semitones = _number(
                operation.get("semitones", 0), "pitch", minimum=-24, maximum=24
            )
            ratio = 2 ** (semitones / 12)
            simple_filters.append(f"rubberband=pitch={ratio:.8f}")
        elif name == "reverse":
            simple_filters.append("areverse")
        elif name == "trim_silence":
            threshold = _number(
                operation.get("threshold_db", -42),
                "silence threshold",
                minimum=-90,
                maximum=-5,
            )
            minimum = _number(
                operation.get("minimum_seconds", 0.15),
                "silence minimum",
                minimum=0.01,
                maximum=10,
            )
            simple_filters.append(
                "silenceremove="
                f"start_periods=1:start_duration={minimum:.4f}:start_threshold={threshold:.2f}dB:"
                f"stop_periods=-1:stop_duration={minimum:.4f}:stop_threshold={threshold:.2f}dB"
            )
        elif name == "highpass":
            frequency = _number(
                operation.get("frequency", 80),
                "high-pass frequency",
                minimum=10,
                maximum=20_000,
            )
            simple_filters.append(f"highpass=f={frequency:.3f}")
        elif name == "lowpass":
            frequency = _number(
                operation.get("frequency", 16_000),
                "low-pass frequency",
                minimum=20,
                maximum=24_000,
            )
            simple_filters.append(f"lowpass=f={frequency:.3f}")
        elif name == "compress":
            threshold = _number(
                operation.get("threshold_db", -18),
                "compressor threshold",
                minimum=-60,
                maximum=0,
            )
            ratio = _number(
                operation.get("ratio", 3), "compressor ratio", minimum=1, maximum=20
            )
            simple_filters.append(
                f"acompressor=threshold={10 ** (threshold / 20):.8f}:ratio={ratio:.3f}"
            )
        else:
            raise ValueError(f"Unsupported audio operation: {name!r}")

    if sample_rate is not None:
        if not 8_000 <= sample_rate <= 192_000:
            raise ValueError("Sample rate is outside the supported range.")
        simple_filters.append(f"aresample={sample_rate}")
    if channels is not None and channels not in {1, 2}:
        raise ValueError("Channels must be 1 or 2.")

    arguments = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(source),
    ]
    if complex_filter:
        if simple_filters:
            complex_filter += f";{map_label}{','.join(simple_filters)}[finala]"
            map_label = "[finala]"
        arguments.extend(
            ["-filter_complex", complex_filter, "-map", map_label or "[outa]"]
        )
    elif simple_filters:
        arguments.extend(["-af", ",".join(simple_filters)])
    if channels is not None:
        arguments.extend(["-ac", str(channels)])
    arguments.extend(OUTPUT_CODEC_ARGUMENTS[output_format])
    arguments.append(str(destination))
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        _run(arguments, timeout=max(60.0, duration * 3))
        return probe_audio(destination)
    except Exception:
        destination.unlink(missing_ok=True)
        raise


def concatenate_audio(
    sources: list[str | Path],
    destination_path: str | Path,
    *,
    output_format: str,
    crossfade: float = 0.0,
) -> dict[str, Any]:
    if len(sources) < 2:
        raise ValueError("At least two audio files are required.")
    if output_format not in OUTPUT_CODEC_ARGUMENTS:
        raise ValueError("Unsupported output format.")
    crossfade = _number(crossfade, "crossfade", minimum=0, maximum=10)
    paths = [Path(source) for source in sources]
    for path in paths:
        if not path.is_file():
            raise FileNotFoundError(path)
    durations = [probe_audio(path)["duration"] for path in paths]
    if crossfade and any(duration <= crossfade for duration in durations):
        raise ValueError("Crossfade must be shorter than every source clip.")

    arguments = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
    for path in paths:
        arguments.extend(["-i", str(path)])
    prepared = []
    filters = []
    for index in range(len(paths)):
        label = f"a{index}"
        prepared.append(f"[{label}]")
        filters.append(
            f"[{index}:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=mono[{label}]"
        )
    if not crossfade:
        filters.append(f"{''.join(prepared)}concat=n={len(paths)}:v=0:a=1[outa]")
    else:
        current = "a0"
        for index in range(1, len(paths)):
            output = "outa" if index == len(paths) - 1 else f"mix{index}"
            filters.append(
                f"[{current}][a{index}]acrossfade=d={crossfade:.6f}:c1=tri:c2=tri[{output}]"
            )
            current = output
    arguments.extend(["-filter_complex", ";".join(filters), "-map", "[outa]"])
    arguments.extend(OUTPUT_CODEC_ARGUMENTS[output_format])
    destination = Path(destination_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    arguments.append(str(destination))
    try:
        _run(arguments, timeout=max(60.0, sum(durations) * 3))
        return probe_audio(destination)
    except Exception:
        destination.unlink(missing_ok=True)
        raise


def waveform_peaks(path: str | Path, buckets: int = 1200) -> dict[str, Any]:
    if not 64 <= buckets <= 10_000:
        raise ValueError("Waveform bucket count is outside the supported range.")
    details = probe_audio(path)
    if details["duration"] > 4 * 60 * 60:
        raise ValueError("Waveform previews are limited to four hours.")
    completed = _run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(path),
            "-ac",
            "1",
            "-ar",
            "8000",
            "-f",
            "f32le",
            "pipe:1",
        ],
        timeout=max(30.0, float(details["duration"]) * 2),
    )
    sample_count = len(completed.stdout) // 4
    if not sample_count:
        return {"duration": details["duration"], "peaks": []}
    samples_per_bucket = max(1, math.ceil(sample_count / buckets))
    peaks: list[list[float]] = []
    minimum = 1.0
    maximum = -1.0
    count = 0
    for (sample,) in struct.iter_unpack("<f", completed.stdout[: sample_count * 4]):
        minimum = min(minimum, float(sample))
        maximum = max(maximum, float(sample))
        count += 1
        if count == samples_per_bucket:
            peaks.append([round(minimum, 5), round(maximum, 5)])
            minimum, maximum, count = 1.0, -1.0, 0
    if count:
        peaks.append([round(minimum, 5), round(maximum, 5)])
    return {
        "duration": details["duration"],
        "sample_rate": details["sample_rate"],
        "peaks": peaks,
    }


def detect_speech_segments(
    path: str | Path,
    *,
    threshold_db: float = -42,
    minimum_silence: float = 0.35,
    padding: float = 0.08,
) -> list[dict[str, float]]:
    threshold_db = _number(threshold_db, "silence threshold", minimum=-90, maximum=-5)
    minimum_silence = _number(
        minimum_silence, "minimum silence", minimum=0.05, maximum=10
    )
    padding = _number(padding, "segment padding", minimum=0, maximum=2)
    details = probe_audio(path)
    duration = float(details["duration"])
    try:
        completed = subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-nostats",
                "-i",
                str(path),
                "-af",
                f"silencedetect=noise={threshold_db:.2f}dB:d={minimum_silence:.4f}",
                "-f",
                "null",
                "-",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=max(30.0, duration * 2),
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as error:
        raise AudioProcessingError("Speech-segment detection failed.") from error
    output = completed.stderr
    silence_starts = [
        float(value) for value in re.findall(r"silence_start:\s*([0-9.]+)", output)
    ]
    silence_ends = [
        float(value) for value in re.findall(r"silence_end:\s*([0-9.]+)", output)
    ]
    silences: list[tuple[float, float]] = []
    end_index = 0
    for start in silence_starts:
        while end_index < len(silence_ends) and silence_ends[end_index] < start:
            end_index += 1
        end = silence_ends[end_index] if end_index < len(silence_ends) else duration
        silences.append((start, end))
        end_index += 1
    speech: list[dict[str, float]] = []
    cursor = 0.0
    for start, end in silences:
        if start > cursor:
            speech.append(
                {
                    "start": max(0.0, cursor - padding),
                    "end": min(duration, start + padding),
                }
            )
        cursor = max(cursor, end)
    if cursor < duration:
        speech.append({"start": max(0.0, cursor - padding), "end": duration})
    if not speech and duration > 0:
        speech = [{"start": 0.0, "end": duration}]
    return [segment for segment in speech if segment["end"] - segment["start"] >= 0.05]
