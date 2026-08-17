from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from web_demo.backend.app.core.config import VIDEO_PROMPT_KIND, load_prompt_config, merge_prompt_config
from web_demo.backend.app.core.llm_client import OpenAICompatibleClient
from web_demo.backend.app.utils.file_writer import ensure_dir, write_csv, write_json, write_text


@dataclass
class GeneratedVideoAsset:
    video: str
    match_key: str
    reference_main: str
    reference_alt_1: str
    reference_alt_2: str
    source_summary: str
    reference_summary: str
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


def _format_placeholders(value: str, *, video_name: str, stem: str, reference_names: str) -> str:
    return str(value).format(video_name=video_name, stem=stem, reference_names=reference_names)


def _mock_result(video_name: str, references: list[dict[str, str]], prompt_config: dict[str, Any]) -> dict[str, Any]:
    stem = Path(video_name).stem
    reference_names = ", ".join(reference["name"] for reference in references) if references else "none"
    mock_config = prompt_config.get("mock_result", {})
    return {
        "source_summary": _format_placeholders(
            mock_config.get("source_summary", "Mock source summary for {video_name}"),
            video_name=video_name,
            stem=stem,
            reference_names=reference_names,
        ),
        "reference_summary": _format_placeholders(
            mock_config.get("reference_summary", "Reference images: {reference_names}"),
            video_name=video_name,
            stem=stem,
            reference_names=reference_names,
        ),
        "edit_goal": _format_placeholders(
            mock_config.get("edit_goal", ""),
            video_name=video_name,
            stem=stem,
            reference_names=reference_names,
        ),
        "zh_prompt": _format_placeholders(mock_config.get("zh_prompt", ""), video_name=video_name, stem=stem, reference_names=reference_names),
        "en_prompt": _format_placeholders(mock_config.get("en_prompt", ""), video_name=video_name, stem=stem, reference_names=reference_names),
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


def run_video_generation(
    *,
    job_id: str,
    videos: list[dict[str, Any]],
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
    config = merge_prompt_config(VIDEO_PROMPT_KIND, prompt_config) if prompt_config else load_prompt_config(VIDEO_PROMPT_KIND)
    system_prompt = str(config.get("system_prompt", "")).strip()
    base_user_text = str(config.get("user_text", "")).strip()
    job_output_dir = _create_timestamp_output_dir(output_root)
    assets: list[GeneratedVideoAsset] = []
    failures: list[dict[str, str]] = []
    total = len(videos)

    for index, video_item in enumerate(videos, start=1):
        video_name = str(video_item.get("name", "video"))
        match_key = str(video_item.get("matchKey") or Path(video_name).stem)
        references = list(video_item.get("references") or [])
        video_url = str(video_item.get("videoUrl") or video_item.get("videoDataUrl") or "")
        json_path = job_output_dir / f"{match_key}.prompt.json"
        txt_path = job_output_dir / f"{match_key}.prompt.txt"

        try:
            if not overwrite and json_path.exists():
                log(f"Skip existing: {video_name}")
                continue

            log(f"Processing video: {video_name}")
            if use_mock or not api_key.strip():
                payload = _mock_result(video_name, references, config)
                raw_response = json.dumps(payload, ensure_ascii=False, indent=2)
            else:
                if not video_url:
                    raise RuntimeError("Missing source video URL.")
                media_urls = [video_url] + [
                    str(reference.get("url") or reference.get("dataUrl") or "")
                    for reference in references
                    if reference.get("url") or reference.get("dataUrl")
                ]
                reference_names = ", ".join(reference.get("name", "") for reference in references if reference.get("name")) or "none"
                user_text = (
                    f"{base_user_text}\n\n"
                    f"Source video file: {video_name}\n"
                    f"Reference images: {reference_names}\n"
                    "Media order: the first media item is the source video URL, and the remaining media items are reference image URLs."
                )
                response = client.chat_with_media_urls(system_prompt, user_text, media_urls)
                raw_response = response.text
                payload = _try_parse_json(raw_response) or {
                    "source_summary": "",
                    "reference_summary": "",
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
                "video": video_name,
                "match_key": match_key,
                "reference_main": str(video_item.get("referenceMain") or ""),
                "reference_alt_1": str(video_item.get("referenceAlt1") or ""),
                "reference_alt_2": str(video_item.get("referenceAlt2") or ""),
                "source_summary": payload.get("source_summary", ""),
                "reference_summary": payload.get("reference_summary", ""),
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
                GeneratedVideoAsset(
                    video=normalized["video"],
                    match_key=normalized["match_key"],
                    reference_main=normalized["reference_main"],
                    reference_alt_1=normalized["reference_alt_1"],
                    reference_alt_2=normalized["reference_alt_2"],
                    source_summary=normalized["source_summary"],
                    reference_summary=normalized["reference_summary"],
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
            failures.append({"video": video_name, "error": str(exc)})
            log(f"Failed: {video_name} -> {exc}")
        finally:
            progress(index, total)

    summary_rows = [
        {
            "video": item.video,
            "match_key": item.match_key,
            "reference_main": item.reference_main,
            "reference_alt_1": item.reference_alt_1,
            "reference_alt_2": item.reference_alt_2,
            "source_summary": item.source_summary,
            "reference_summary": item.reference_summary,
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
