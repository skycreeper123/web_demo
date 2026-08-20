from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from web_demo.backend.app.core.config import project_root


def _auto_path_style() -> str:
    return "windows" if os.name == "nt" else "linux"


def effective_path_style(config: dict[str, Any]) -> str:
    value = str(config.get("path_style") or "").strip().lower()
    return value if value in {"windows", "linux"} else _auto_path_style()


def resolve_configured_path(value: str | None, *, fallback: Path | None = None) -> Path:
    text = str(value or "").strip()
    if not text:
        if fallback is None:
            raise RuntimeError("Missing required path configuration.")
        return fallback
    path = Path(text)
    if path.is_absolute():
        return path
    return (project_root() / path).resolve()


def resolve_comfy_root_dir(config: dict[str, Any]) -> Path:
    return resolve_configured_path(config.get("comfy_root_dir") or None, fallback=project_root())


def resolve_comfy_input_dir(config: dict[str, Any]) -> Path:
    root = resolve_comfy_root_dir(config)
    return resolve_configured_path(config.get("comfy_input_dir") or None, fallback=root / "input")


def resolve_comfy_output_dir(config: dict[str, Any]) -> Path:
    root = resolve_comfy_root_dir(config)
    return resolve_configured_path(config.get("comfy_output_dir") or None, fallback=root / "output")


def resolve_temp_dir(config: dict[str, Any]) -> Path:
    return resolve_configured_path(config.get("temp_dir") or None, fallback=project_root() / "output" / "comfy_temp")


def resolve_workflow_manifest_dir(config: dict[str, Any]) -> Path:
    return resolve_configured_path(
        config.get("workflow_manifest_dir") or None,
        fallback=project_root() / "workflow",
    )


def workflow_ref(*parts: str) -> str:
    return Path(*parts).as_posix()
