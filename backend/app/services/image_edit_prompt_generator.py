from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from web_demo.backend.app.core.config import IMAGE_EDIT_PROMPT_KIND, load_prompt_config, merge_prompt_config
from web_demo.backend.app.core.llm_client import OpenAICompatibleClient
from web_demo.backend.app.utils.file_writer import ensure_dir, write_csv, write_json, write_text


@dataclass
class GeneratedImageEditAsset:
    image: str
    subject: str
    source_summary: str
    edit_goal: str
    zh_prompt: str
    en_prompt: str
    keep_unchanged: list[str] = field(default_factory=list)
    add_or_emphasize: list[str] = field(default_factory=list)
    avoid: list[str] = field(default_factory=list)
    quality_check: list[str] = field(default_factory=list)
    raw_response: str = ""
    json_file: str = ""
    txt_file: str = ""


def _try_parse_json(text: str) -> dict[str, Any] | None:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.replace("json\n", "", 1).replace("JSON\n", "", 1)
    try:
        value = json.loads(cleaned)
        if isinstance(value, dict):
            return value
    except json.JSONDecodeError:
        pass
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start >= 0 and end > start:
        try:
            value = json.loads(cleaned[start : end + 1])
            if isinstance(value, dict):
                return value
        except json.JSONDecodeError:
            return None
    return None


def _format_placeholders(value: str, *, image_name: str, stem: str) -> str:
    return str(value).format(image_name=image_name, stem=stem)


def _mock_result(image_name: str, prompt_config: dict[str, Any]) -> dict[str, Any]:
    stem = Path(image_name).stem.replace("_", " ").strip() or "image"
    mock_config = prompt_config.get("mock_result", {})
    return {
        "subject": _format_placeholders(mock_config.get("subject", "{stem}"), image_name=image_name, stem=stem),
        "source_summary": _format_placeholders(
            mock_config.get("source_summary", "Mock image-edit prompt for {image_name}"),
            image_name=image_name,
            stem=stem,
        ),
        "edit_goal": _format_placeholders(
            mock_config.get("edit_goal", ""),
            image_name=image_name,
            stem=stem,
        ),
        "zh_prompt": _format_placeholders(mock_config.get("zh_prompt", ""), image_name=image_name, stem=stem),
        "en_prompt": _format_placeholders(mock_config.get("en_prompt", ""), image_name=image_name, stem=stem),
        "keep_unchanged": list(mock_config.get("keep_unchanged", []) or []),
        "add_or_emphasize": list(mock_config.get("add_or_emphasize", []) or []),
        "avoid": list(mock_config.get("avoid", []) or []),
        "quality_check": list(mock_config.get("quality_check", []) or []),
    }


def _format_text(payload: dict[str, Any]) -> str:
    lines = [
        f"Edit Goal:\n{payload.get('edit_goal', '')}",
        "",
        f"Chinese Prompt:\n{payload.get('zh_prompt', '')}",
        "",
        f"English Prompt:\n{payload.get('en_prompt', '')}",
        "",
        "Keep Unchanged:\n" + "; ".join(payload.get("keep_unchanged", []) or []),
        "",
        "Add Or Emphasize:\n" + "; ".join(payload.get("add_or_emphasize", []) or []),
        "",
        "Avoid:\n" + "; ".join(payload.get("avoid", []) or []),
        "",
        "Quality Check:\n" + "; ".join(payload.get("quality_check", []) or []),
    ]
    return "\n".join(lines).strip() + "\n"


def _create_timestamp_output_dir(output_root: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    candidate = output_root / timestamp
    suffix = 1
    while candidate.exists():
        candidate = output_root / f"{timestamp}_{suffix}"
        suffix += 1
    return ensure_dir(candidate)


def run_image_edit_generation(
    *,
    job_id: str,
    images: list[dict[str, str]],
    output_root: Path,
    api_key: str,
    base_url: str,
    model: str,
    overwrite: bool,
    use_mock: bool,
    prompt_config: dict[str, Any] | None,
    log: Callable[[str], None],
    progress: Callable[[int, int], None],
) -> dict[str, Any]:
    client = OpenAICompatibleClient(base_url=base_url, api_key=api_key, model=model)
    config = (
        merge_prompt_config(IMAGE_EDIT_PROMPT_KIND, prompt_config)
        if prompt_config
        else load_prompt_config(IMAGE_EDIT_PROMPT_KIND)
    )
    system_prompt = str(config.get("system_prompt", "")).strip()
    user_text = str(config.get("user_text", "")).strip()
    job_output_dir = _create_timestamp_output_dir(output_root)
    assets: list[GeneratedImageEditAsset] = []
    failures: list[dict[str, str]] = []
    total = len(images)

    for index, image in enumerate(images, start=1):
        name = image["name"]
        image_url = str(image.get("imageUrl") or image.get("dataUrl") or "")
        stem = Path(name).stem
        json_path = job_output_dir / f"{stem}.prompt.json"
        txt_path = job_output_dir / f"{stem}.prompt.txt"

        try:
            if not overwrite and json_path.exists():
                log(f"Skip existing: {name}")
                continue

            log(f"Processing image edit: {name}")
            if use_mock or not api_key.strip():
                payload = _mock_result(name, config)
                raw_response = json.dumps(payload, ensure_ascii=False, indent=2)
            else:
                if not image_url:
                    raise RuntimeError("Missing source image URL.")
                response = client.chat_with_image(system_prompt, user_text, image_url)
                raw_response = response.text
                payload = _try_parse_json(raw_response) or {
                    "subject": "",
                    "source_summary": "",
                    "edit_goal": "",
                    "zh_prompt": raw_response,
                    "en_prompt": "",
                    "keep_unchanged": [],
                    "add_or_emphasize": [],
                    "avoid": [],
                    "quality_check": [],
                    "raw_response": raw_response,
                }

            normalized = {
                "subject": payload.get("subject", ""),
                "source_summary": payload.get("source_summary", ""),
                "edit_goal": payload.get("edit_goal", ""),
                "zh_prompt": payload.get("zh_prompt", ""),
                "en_prompt": payload.get("en_prompt", ""),
                "keep_unchanged": payload.get("keep_unchanged", []) or [],
                "add_or_emphasize": payload.get("add_or_emphasize", []) or [],
                "avoid": payload.get("avoid", []) or [],
                "quality_check": payload.get("quality_check", []) or [],
                "raw_response": raw_response,
            }

            write_json(json_path, normalized)
            write_text(txt_path, _format_text(normalized))
            assets.append(
                GeneratedImageEditAsset(
                    image=name,
                    subject=normalized["subject"],
                    source_summary=normalized["source_summary"],
                    edit_goal=normalized["edit_goal"],
                    zh_prompt=normalized["zh_prompt"],
                    en_prompt=normalized["en_prompt"],
                    keep_unchanged=list(normalized["keep_unchanged"]),
                    add_or_emphasize=list(normalized["add_or_emphasize"]),
                    avoid=list(normalized["avoid"]),
                    quality_check=list(normalized["quality_check"]),
                    raw_response=raw_response,
                    json_file=str(json_path),
                    txt_file=str(txt_path),
                )
            )
            log(f"Saved: {json_path.name} / {txt_path.name}")
        except Exception as exc:
            failures.append({"image": name, "error": str(exc)})
            log(f"Failed: {name} -> {exc}")
        finally:
            progress(index, total)

    summary_rows = [
        {
            "image": item.image,
            "subject": item.subject,
            "source_summary": item.source_summary,
            "edit_goal": item.edit_goal,
            "zh_prompt": item.zh_prompt,
            "en_prompt": item.en_prompt,
            "json_file": item.json_file,
            "txt_file": item.txt_file,
        }
        for item in assets
    ]
    write_csv(job_output_dir / "prompts.csv", summary_rows)

    return {
        "job_id": job_id,
        "output_dir": str(job_output_dir),
        "items": [item.__dict__ for item in assets],
        "failures": failures,
        "summary_file": str(job_output_dir / "prompts.csv"),
    }
