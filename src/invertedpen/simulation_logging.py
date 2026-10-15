"""Self-describing, reproducible storage for simulation trajectories."""

from __future__ import annotations

import json
import importlib.metadata
import platform
import subprocess
import sys
import uuid
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

SCHEMA_VERSION = 1


def _package_version(package: str) -> str | None:
    try:
        return importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        return None


def _json_value(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _git_metadata() -> dict[str, Any]:
    metadata: dict[str, Any] = {"commit": None, "dirty": None, "error": None}
    commands = {
        "commit": ["git", "rev-parse", "HEAD"],
        "status": ["git", "status", "--porcelain"],
    }
    try:
        commit = subprocess.run(
            commands["commit"], check=True, capture_output=True, text=True
        ).stdout.strip()
        status = subprocess.run(
            commands["status"], check=True, capture_output=True, text=True
        ).stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        metadata["error"] = f"{type(exc).__name__}: {exc}"
        return metadata
    metadata["commit"] = commit
    metadata["dirty"] = bool(status)
    return metadata


class SimulationLogger:
    """Buffer named samples and persist one complete or incomplete run."""

    def __init__(
        self,
        root: str | Path = "artifacts/runs",
        *,
        tag: str = "simulation",
        metadata: Mapping[str, Any] | None = None,
        signal_metadata: Mapping[str, Mapping[str, Any]] | None = None,
    ) -> None:
        if not tag or any(character in tag for character in r'\/'):
            raise ValueError("tag must be non-empty and must not contain path separators")
        self.root = Path(root)
        self.tag = tag
        self.metadata = dict(metadata or {})
        self.signal_metadata = {
            name: dict(spec) for name, spec in (signal_metadata or {}).items()
        }
        self._samples: dict[str, list[np.ndarray]] = {}
        self._shapes: dict[str, tuple[int, ...]] = {}
        self._dtypes: dict[str, np.dtype[Any]] = {}
        self._run_path: Path | None = None

    @property
    def run_path(self) -> Path | None:
        return self._run_path

    def log(self, step: int, **signals: Any) -> None:
        """Buffer one sample, rejecting missing or inconsistent signals."""
        if step < 0:
            raise ValueError("step must be non-negative")
        if not signals:
            raise ValueError("at least one signal is required")
        if self._samples and set(signals) != set(self._samples):
            raise ValueError("every sample must contain the same signal names")
        arrays = {name: np.asarray(value) for name, value in signals.items()}
        for name, array in arrays.items():
            if name in self._shapes and array.shape != self._shapes[name]:
                raise ValueError(
                    f"signal {name!r} changed shape from {self._shapes[name]} "
                    f"to {array.shape}"
                )
        for name, array in arrays.items():
            self._samples.setdefault(name, []).append(array.copy())
            self._shapes.setdefault(name, array.shape)
            self._dtypes.setdefault(name, array.dtype)

    def _make_run_path(self) -> Path:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self.root.mkdir(parents=True, exist_ok=True)
        while True:
            path = self.root / f"{timestamp}_{self.tag}_{uuid.uuid4().hex[:8]}"
            if not path.exists():
                return path

    def finalize(
        self,
        *,
        status: str = "complete",
        error: BaseException | None = None,
    ) -> Path:
        """Write buffered samples and metadata, returning the run directory."""
        if status not in {"complete", "incomplete"}:
            raise ValueError("status must be 'complete' or 'incomplete'")
        if status == "complete" and error is not None:
            raise ValueError("complete runs cannot include an error")
        if not self._samples:
            raise ValueError("cannot finalize a run without samples")

        run_path = self._make_run_path()
        temporary_path = run_path.with_name(f".{run_path.name}.tmp")
        arrays = {name: np.stack(samples) for name, samples in self._samples.items()}
        signal_info = {}
        for name, array in arrays.items():
            signal_info[name] = {
                "shape": list(array.shape[1:]),
                "dtype": str(array.dtype),
                **self.signal_metadata.get(name, {}),
            }
        manifest: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "status": status,
            "run_id": run_path.name,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "tag": self.tag,
            "signals": signal_info,
            "git": _git_metadata(),
            "runtime": {
                "python": sys.version,
                "platform": platform.platform(),
                "packages": {
                    package: version
                    for package in ("invertedpen", "numpy", "casadi", "sympy")
                    if (version := _package_version(package)) is not None
                },
            },
            "configuration": _json_value(self.metadata),
        }
        if error is not None:
            manifest["error"] = {
                "type": type(error).__name__,
                "message": str(error),
            }
        try:
            temporary_path.mkdir()
            np.savez(temporary_path / "trajectory.npz", **arrays)
            with (temporary_path / "metadata.json").open("w", encoding="utf-8") as file:
                json.dump(manifest, file, indent=2, sort_keys=True)
                file.write("\n")
            temporary_path.rename(run_path)
        except Exception:
            if temporary_path.exists():
                for child in temporary_path.iterdir():
                    child.unlink()
                temporary_path.rmdir()
            raise
        self._run_path = run_path
        return run_path

    def __enter__(self) -> SimulationLogger:
        return self

    def __exit__(
        self,
        _exception_type: type[BaseException] | None,
        exception: BaseException | None,
        _traceback: object,
    ) -> bool:
        if exception is not None and self._samples and self._run_path is None:
            self.finalize(status="incomplete", error=exception)
        return False


def load_run(path: str | Path) -> tuple[dict[str, Any], dict[str, np.ndarray]]:
    """Load a persisted run manifest and trajectory arrays."""
    run_path = Path(path)
    with (run_path / "metadata.json").open(encoding="utf-8") as file:
        metadata = json.load(file)
    with np.load(run_path / "trajectory.npz") as archive:
        arrays = {name: archive[name].copy() for name in archive.files}
    return metadata, arrays
