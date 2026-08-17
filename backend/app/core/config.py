from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


IMAGE_PROMPT_KIND = "image"
VIDEO_PROMPT_KIND = "video"


@dataclass(frozen=True)
class DemoDefaults:
    api_key: str = ""
    base_url: str = "https://apinebula.ai/v1"
    model: str = "Prompt"
    output_root: str = ""
    image_output_root: str = ""
    video_output_root: str = ""


def project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def backend_root() -> Path:
    return Path(__file__).resolve().parents[2]


def project_relative_path_text(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(project_root().resolve()).as_posix()
    except ValueError:
        try:
            return resolved.relative_to(backend_root().resolve()).as_posix()
        except ValueError:
            return str(resolved)


def default_output_root(kind: str | None = None) -> Path:
    return project_root() / "output"


def default_output_root_text(kind: str | None = None) -> str:
    return project_relative_path_text(default_output_root(kind))


def _normalize_relative_output_dir_text(text: str) -> str:
    normalized = Path(text).as_posix().strip()
    normalized = normalized.lstrip("./")
    lowered = normalized.lower()
    legacy_values = {
        "outputs",
        "outputs/image",
        "outputs/video",
        "backend/outputs",
        "backend/outputs/image",
        "backend/outputs/video",
        "output/image",
        "output/video",
    }
    if lowered in legacy_values:
        return "output"
    return normalized


def _normalize_output_path_text(value: str | None) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    path = Path(text)
    if not path.is_absolute():
        return _normalize_relative_output_dir_text(path.as_posix())
    resolved = path.resolve()
    lowered_parts = [part.lower() for part in resolved.parts]
    if "backend" in lowered_parts:
        backend_index = lowered_parts.index("backend")
        trailing_parts = resolved.parts[backend_index + 1 :]
        if trailing_parts:
            return _normalize_relative_output_dir_text(Path(*trailing_parts).as_posix())
    for base in (backend_root().resolve(), project_root().resolve()):
        try:
            return _normalize_relative_output_dir_text(resolved.relative_to(base).as_posix())
        except ValueError:
            continue
    return str(path)


def resolve_output_path(value: str | None, kind: str | None = None) -> Path:
    text = str(value or "").strip()
    if not text:
        return default_output_root(kind)
    path = Path(text)
    if path.is_absolute():
        return path
    normalized = _normalize_relative_output_dir_text(path.as_posix())
    return (project_root() / normalized).resolve()


def default_upload_root() -> Path:
    return backend_root() / "uploads"


def api_config_path() -> Path:
    return backend_root() / "api_config.json"


def _prompt_config_filename(kind: str) -> str:
    if kind == IMAGE_PROMPT_KIND:
        return "image_prompt_config.json"
    if kind == VIDEO_PROMPT_KIND:
        return "video_prompt_config.json"
    raise ValueError(f"Unsupported prompt config kind: {kind}")


def prompt_config_path(kind: str = IMAGE_PROMPT_KIND) -> Path:
    return backend_root() / _prompt_config_filename(kind)


def default_prompt_config(kind: str) -> dict[str, Any]:
    if kind == IMAGE_PROMPT_KIND:
        return {
            "system_prompt": """You are a professional image-to-video prompt generator.
Observe the input image and generate high-quality prompts for an Image-to-Video model.

Rules:
1. Do not redesign the image scene. Do not invent important subjects that are not visible in the image.
2. Preserve the original subject identity, appearance, clothing, colors, background layout, object count, and overall visual style.
3. Clearly describe the subject, core action, motion direction and range, camera language, timing and rhythm, environmental motion, composition and spatial relationship, visual style and quality, mood, unchanged elements, and negative constraints.
4. Output both a Chinese prompt and an English prompt.
5. Return strict JSON only. Do not use Markdown. Do not add explanations.

JSON schema:
{
  "subject": "main subject",
  "scene_summary": "brief description of the input image",
  "zh_prompt": "complete Chinese image-to-video prompt",
  "en_prompt": "complete English image-to-video prompt",
  "keep_unchanged": ["elements that must remain unchanged"],
  "avoid": ["problems to avoid"],
  "quality_check": ["items to check after generation"]
}
""",
            "user_text": """Generate an image-to-video prompt based on this input image.

The Chinese prompt must include: generate a short video from the input image; preserve the original image; subject; core action; motion direction, range, and speed; camera language; timing and rhythm; environmental motion; composition and spatial relationship; visual style and quality; mood; unchanged elements; and things to avoid.

The English prompt should be natural, complete, and ready to submit to an image-to-video model.
""",
            "mock_result": {
                "subject": "{stem}",
                "scene_summary": "Mock prompt for {image_name}",
                "zh_prompt": "基于输入图片生成一段短视频，保留原图中的 {stem}，保持主体外观、颜色、构图和背景不变，镜头轻微推进，动作自然、节奏平稳，画面风格统一，避免新增无关元素或改变原有细节。",
                "en_prompt": "Generate a short video from the input image, preserve the original {stem}, keep the subject appearance, colors, composition, and background unchanged, use a gentle camera push-in, natural motion, steady rhythm, consistent visual style, and avoid adding unrelated elements or altering original details.",
                "keep_unchanged": ["subject identity", "colors", "composition", "background"],
                "avoid": ["extra subjects", "scene redesign", "style drift"],
                "quality_check": ["subject remains stable", "motion is smooth", "background stays consistent"],
            },
        }

    if kind == VIDEO_PROMPT_KIND:
        return {
            "system_prompt": """You are a professional video-editing prompt generator.
You will receive the source video as a publicly accessible URL, followed by one or two reference images provided as publicly accessible URLs.

Rules:
1. Treat the first media item as the source video content reference.
2. Treat the remaining media items as reference images for styling, subject detail, props, costume, or composition.
3. Do not replace the source video content. Use the references as editing targets or enhancement constraints.
4. Output both a Chinese prompt and an English prompt.
5. Return strict JSON only. Do not use Markdown. Do not add explanations.

JSON schema:
{
  "source_summary": "brief summary of the source video",
  "reference_summary": "brief summary of the reference images",
  "edit_goal": "what the edit should achieve",
  "zh_prompt": "complete Chinese video-editing prompt",
  "en_prompt": "complete English video-editing prompt",
  "keep_unchanged": ["elements that must remain unchanged"],
  "add_or_emphasize": ["elements to add or emphasize"],
  "avoid": ["problems to avoid"],
  "quality_check": ["items to check after generation"]
}
""",
            "user_text": """Generate a video-editing prompt for the source video using the reference images.

The Chinese prompt must clearly describe: the original video content to preserve, the desired edit direction, what to borrow from the reference images, motion continuity, camera consistency, scene continuity, visual style, subject consistency, and things to avoid.

The English prompt should be natural, complete, and ready to submit to a video-editing model.
""",
            "mock_result": {
                "source_summary": "Mock source summary for {video_name}",
                "reference_summary": "Reference images: {reference_names}",
                "edit_goal": "Use the references to refine the source video while preserving the original motion and scene continuity.",
                "zh_prompt": "请基于源视频 {video_name} 进行视频编辑，保留原始镜头运动、主体结构和场景连续性，参考图像 {reference_names} 的风格和细节进行增强，不改变原视频的叙事逻辑，重点强化质感、色彩与目标元素一致性，避免出现主体漂移、结构变形和时序跳变。",
                "en_prompt": "Edit the source video {video_name} while preserving the original motion, subject structure, and scene continuity. Use the reference images {reference_names} to guide styling and detail enhancement without changing the original narrative flow. Emphasize texture, color consistency, and target visual elements, and avoid subject drift, structural distortion, or temporal flicker.",
                "keep_unchanged": ["camera motion", "scene continuity", "subject identity"],
                "add_or_emphasize": ["reference styling cues", "texture detail", "color refinement"],
                "avoid": ["subject drift", "flicker", "over-redesign"],
                "quality_check": ["continuity is stable", "reference traits are reflected", "motion remains natural"],
            },
        }

    raise ValueError(f"Unsupported prompt config kind: {kind}")


def default_api_config(kind: str | None = None) -> dict[str, Any]:
    base_url = os.getenv("APINEBULA_BASE_URL", "https://apinebula.ai/v1")
    model = os.getenv("APINEBULA_MODEL", "Prompt")
    full = {
        IMAGE_PROMPT_KIND: {
            "api_key": "",
            "base_url": base_url,
            "model": model,
            "output_dir": default_output_root_text(IMAGE_PROMPT_KIND),
            "use_mock": True,
            "overwrite": False,
        },
        VIDEO_PROMPT_KIND: {
            "api_key": "",
            "base_url": base_url,
            "model": model,
            "output_dir": default_output_root_text(VIDEO_PROMPT_KIND),
            "use_mock": True,
            "overwrite": False,
        },
    }
    if kind is None:
        return full
    if kind not in full:
        raise ValueError(f"Unsupported API config kind: {kind}")
    return dict(full[kind])


def _merge_dict(default: dict[str, Any], value: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(value, dict):
        return dict(default)
    merged = dict(default)
    for key, default_value in default.items():
        if isinstance(default_value, dict):
            merged[key] = _merge_dict(default_value, value.get(key))
        else:
            merged[key] = value.get(key, default_value)
    for key, item in value.items():
        if key not in merged:
            merged[key] = item
    return merged


def merge_prompt_config(kind: str, config: dict[str, Any] | None) -> dict[str, Any]:
    return _merge_dict(default_prompt_config(kind), config)


def _merge_api_config(config: dict[str, Any] | None) -> dict[str, Any]:
    defaults = default_api_config()
    raw = config if isinstance(config, dict) else {}
    merged = {
        IMAGE_PROMPT_KIND: _merge_dict(defaults[IMAGE_PROMPT_KIND], raw.get(IMAGE_PROMPT_KIND)),
        VIDEO_PROMPT_KIND: _merge_dict(defaults[VIDEO_PROMPT_KIND], raw.get(VIDEO_PROMPT_KIND)),
    }
    merged[IMAGE_PROMPT_KIND]["output_dir"] = _normalize_output_path_text(merged[IMAGE_PROMPT_KIND].get("output_dir"))
    merged[VIDEO_PROMPT_KIND]["output_dir"] = _normalize_output_path_text(merged[VIDEO_PROMPT_KIND].get("output_dir"))
    for key, value in raw.items():
        if key not in merged:
            merged[key] = value
    return merged


def load_prompt_config(kind: str = IMAGE_PROMPT_KIND) -> dict[str, Any]:
    path = prompt_config_path(kind)
    if not path.exists():
        defaults = default_prompt_config(kind)
        save_prompt_config(kind, defaults)
        return defaults
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default_prompt_config(kind)
    return merge_prompt_config(kind, raw if isinstance(raw, dict) else {})


def save_prompt_config(kind: str, config: dict[str, Any]) -> dict[str, Any]:
    path = prompt_config_path(kind)
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = merge_prompt_config(kind, config)
    path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
    return normalized


def load_api_config(kind: str | None = None) -> dict[str, Any]:
    path = api_config_path()
    if not path.exists():
        defaults = _merge_api_config({})
        path.write_text(json.dumps(defaults, ensure_ascii=False, indent=2), encoding="utf-8")
        return defaults if kind is None else dict(defaults[kind])
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        defaults = _merge_api_config({})
        return defaults if kind is None else dict(defaults[kind])
    normalized = _merge_api_config(raw if isinstance(raw, dict) else {})
    if normalized != raw:
        path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
    return normalized if kind is None else dict(normalized[kind])


def save_api_config(kind: str, config: dict[str, Any]) -> dict[str, Any]:
    path = api_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    current = load_api_config()
    current[kind] = _merge_dict(default_api_config(kind), config if isinstance(config, dict) else {})
    current[kind]["output_dir"] = _normalize_output_path_text(current[kind].get("output_dir"))
    path.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")
    return dict(current[kind])


def load_defaults() -> DemoDefaults:
    return DemoDefaults(
        api_key="",
        base_url=os.getenv("APINEBULA_BASE_URL", "https://apinebula.ai/v1"),
        model=os.getenv("APINEBULA_MODEL", "Prompt"),
        output_root=default_output_root_text(),
        image_output_root=default_output_root_text(IMAGE_PROMPT_KIND),
        video_output_root=default_output_root_text(VIDEO_PROMPT_KIND),
    )


def normalize_base_url(value: str) -> str:
    if re.search(r"apinebula\.ai/v1/?$", value or ""):
        return "https://api.yhlxj.ai/v1"
    return (value or "").rstrip("/")
