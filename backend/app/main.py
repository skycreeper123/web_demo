from __future__ import annotations

import json
import os
import sys
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable
from urllib.parse import unquote, urlparse

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[3]))

from web_demo.backend.app.core.config import (  # noqa: E402
    IMAGE_PROMPT_KIND,
    VIDEO_PROMPT_KIND,
    api_config_path,
    default_output_root,
    load_api_config,
    load_defaults,
    load_prompt_config,
    project_relative_path_text,
    prompt_config_path,
    resolve_output_path,
    save_api_config,
    save_prompt_config,
)
from web_demo.backend.app.services.prompt_generator import run_image_generation  # noqa: E402
from web_demo.backend.app.services.video_matcher import build_video_matches  # noqa: E402
from web_demo.backend.app.services.video_prompt_generator import run_video_generation  # noqa: E402
from web_demo.backend.app.utils.file_writer import ensure_dir  # noqa: E402


FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"
DEFAULTS = load_defaults()


@dataclass
class JobState:
    id: str
    kind: str
    status: str = "queued"
    progress: int = 0
    total: int = 0
    logs: list[str] = field(default_factory=list)
    outputs: list[dict[str, Any]] = field(default_factory=list)
    output_dir: str = ""
    error: str = ""
    created_at: float = field(default_factory=time.time)
    started_at: float = 0.0
    finished_at: float = 0.0


class JobStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._jobs: dict[str, JobState] = {}

    def create(self, *, kind: str, total: int) -> JobState:
        job = JobState(id=uuid.uuid4().hex[:12], kind=kind, total=total)
        with self._lock:
            self._jobs[job.id] = job
        return job

    def get(self, job_id: str) -> JobState | None:
        with self._lock:
            return self._jobs.get(job_id)

    def update(self, job_id: str, **changes: Any) -> JobState:
        with self._lock:
            job = self._jobs[job_id]
            for key, value in changes.items():
                setattr(job, key, value)
            return job

    def append_log(self, job_id: str, message: str) -> None:
        with self._lock:
            self._jobs[job_id].logs.append(message)

    def replace_outputs(self, job_id: str, outputs: list[dict[str, Any]]) -> None:
        with self._lock:
            self._jobs[job_id].outputs = outputs


STORE = JobStore()


class BrowserSessionStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._sessions: dict[str, float] = {}
        self._had_browser_session = False

    def register(self, session_id: str) -> None:
        now = time.time()
        with self._lock:
            self._sessions[session_id] = now
            self._had_browser_session = True

    def heartbeat(self, session_id: str) -> bool:
        now = time.time()
        with self._lock:
            if session_id not in self._sessions:
                return False
            self._sessions[session_id] = now
            return True

    def close(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)

    def snapshot(self, stale_after_seconds: float) -> dict[str, Any]:
        now = time.time()
        with self._lock:
            stale_ids = [
                session_id
                for session_id, last_seen_at in self._sessions.items()
                if (now - last_seen_at) > stale_after_seconds
            ]
            for session_id in stale_ids:
                self._sessions.pop(session_id, None)
            active_count = len(self._sessions)
            return {
                "active_count": active_count,
                "had_browser_session": self._had_browser_session,
                "session_ids": sorted(self._sessions),
            }


BROWSER_SESSIONS = BrowserSessionStore()
SESSION_HEARTBEAT_TIMEOUT_SECONDS = 15.0
SESSION_SWEEP_INTERVAL_SECONDS = 5.0


def json_response(handler: BaseHTTPRequestHandler, status: int, payload: Any) -> None:
    data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(data)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(data)


def text_response(
    handler: BaseHTTPRequestHandler,
    status: int,
    content: str,
    content_type: str = "text/plain; charset=utf-8",
) -> None:
    data = content.encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(data)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(data)


def read_body_json(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    length = int(handler.headers.get("Content-Length", "0"))
    body = handler.rfile.read(length) if length else b"{}"
    return json.loads(body.decode("utf-8") or "{}")


def open_folder(path: Path) -> None:
    if hasattr(os, "startfile"):
        os.startfile(str(path))
    else:
        raise RuntimeError("Folder opening is only implemented for Windows in this demo.")


def job_snapshot(job: JobState) -> dict[str, Any]:
    data = asdict(job)
    data["outputs_count"] = len(job.outputs)
    return data


def start_browser_session_reaper(server: ThreadingHTTPServer) -> None:
    def worker() -> None:
        while True:
            time.sleep(SESSION_SWEEP_INTERVAL_SECONDS)
            snapshot = BROWSER_SESSIONS.snapshot(SESSION_HEARTBEAT_TIMEOUT_SECONDS)
            if snapshot["had_browser_session"] and snapshot["active_count"] == 0:
                server.shutdown()
                return

    threading.Thread(target=worker, daemon=True).start()


def terminate_server_process(server: ThreadingHTTPServer, exit_code: int = 0) -> None:
    def worker() -> None:
        try:
            server.shutdown()
            server.server_close()
        finally:
            time.sleep(0.2)
            os._exit(exit_code)

    threading.Thread(target=worker, daemon=True).start()


def _prompt_config_payload(kind: str) -> dict[str, Any]:
    return {
        "path": project_relative_path_text(prompt_config_path(kind)),
        "config": load_prompt_config(kind),
    }


def _api_config_payload(kind: str) -> dict[str, Any]:
    return {
        "path": project_relative_path_text(api_config_path()),
        "config": load_api_config(kind),
    }


def _start_job_worker(
    *,
    job: JobState,
    total: int,
    runner: Callable[[JobState], dict[str, Any]],
) -> JobState:
    STORE.update(job.id, status="running", started_at=time.time())

    def worker() -> None:
        try:
            result = runner(job)
            STORE.replace_outputs(job.id, result["items"])
            status = "completed" if result["items"] or not result["failures"] else "failed"
            STORE.update(
                job.id,
                status=status,
                progress=total,
                total=total,
                output_dir=result["output_dir"],
                finished_at=time.time(),
            )
            if result["failures"]:
                STORE.append_log(job.id, f"Failed items: {len(result['failures'])}")
            STORE.append_log(job.id, f"Done. Output: {result['output_dir']}")
        except Exception as exc:
            STORE.update(job.id, status="failed", error=str(exc), finished_at=time.time())
            STORE.append_log(job.id, f"Failed: {exc}")

    threading.Thread(target=worker, daemon=True).start()
    return job


def start_image_job(payload: dict[str, Any]) -> JobState:
    images = list(payload.get("images") or [])
    module_config = load_api_config(IMAGE_PROMPT_KIND)
    output_root = resolve_output_path(
        payload.get("outputDir")
        or module_config.get("output_dir")
        or DEFAULTS.image_output_root
        or default_output_root(IMAGE_PROMPT_KIND),
        IMAGE_PROMPT_KIND,
    )
    ensure_dir(output_root)
    job = STORE.create(kind=IMAGE_PROMPT_KIND, total=len(images))

    def runner(job_state: JobState) -> dict[str, Any]:
        return run_image_generation(
            job_id=job_state.id,
            images=images,
            output_root=output_root,
            api_key=str(payload.get("apiKey") or module_config.get("api_key") or ""),
            base_url=str(payload.get("baseUrl") or module_config.get("base_url") or DEFAULTS.base_url),
            model=str(payload.get("model") or module_config.get("model") or DEFAULTS.model),
            overwrite=bool(payload.get("overwrite", module_config.get("overwrite", False))),
            use_mock=bool(payload.get("useMock", module_config.get("use_mock", True))),
            prompt_config=payload.get("promptConfig"),
            log=lambda message: STORE.append_log(job_state.id, message),
            progress=lambda current, total: STORE.update(job_state.id, progress=current, total=total),
        )
    return _start_job_worker(job=job, total=len(images), runner=runner)


def start_video_job(payload: dict[str, Any]) -> JobState:
    videos = list(payload.get("videos") or [])
    module_config = load_api_config(VIDEO_PROMPT_KIND)
    output_root = resolve_output_path(
        payload.get("outputDir")
        or module_config.get("output_dir")
        or DEFAULTS.video_output_root
        or default_output_root(VIDEO_PROMPT_KIND),
        VIDEO_PROMPT_KIND,
    )
    ensure_dir(output_root)
    job = STORE.create(kind=VIDEO_PROMPT_KIND, total=len(videos))

    def runner(job_state: JobState) -> dict[str, Any]:
        return run_video_generation(
            job_id=job_state.id,
            videos=videos,
            output_root=output_root,
            api_key=str(payload.get("apiKey") or module_config.get("api_key") or ""),
            base_url=str(payload.get("baseUrl") or module_config.get("base_url") or DEFAULTS.base_url),
            model=str(payload.get("model") or module_config.get("model") or DEFAULTS.model),
            overwrite=bool(payload.get("overwrite", module_config.get("overwrite", False))),
            use_mock=bool(payload.get("useMock", module_config.get("use_mock", True))),
            prompt_config=payload.get("promptConfig"),
            log=lambda message: STORE.append_log(job_state.id, message),
            progress=lambda current, total: STORE.update(job_state.id, progress=current, total=total),
        )
    return _start_job_worker(job=job, total=len(videos), runner=runner)


class DemoHandler(BaseHTTPRequestHandler):
    server_version = "PromptToolDemo/0.2"

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path

        if path == "/":
            return self._serve_frontend("index.html", "text/html; charset=utf-8")
        if path == "/app.js":
            return self._serve_frontend("app.js", "application/javascript; charset=utf-8")
        if path == "/style.css":
            return self._serve_frontend("style.css", "text/css; charset=utf-8")

        if path == "/api/config":
            image_api_config = load_api_config(IMAGE_PROMPT_KIND)
            video_api_config = load_api_config(VIDEO_PROMPT_KIND)
            return json_response(
                self,
                HTTPStatus.OK,
                {
                    "apiKey": "",
                    "baseUrl": DEFAULTS.base_url,
                    "model": DEFAULTS.model,
                    "outputRoot": DEFAULTS.output_root,
                    "imageOutputRoot": DEFAULTS.image_output_root,
                    "videoOutputRoot": DEFAULTS.video_output_root,
                    "imagePromptConfigPath": project_relative_path_text(prompt_config_path(IMAGE_PROMPT_KIND)),
                    "videoPromptConfigPath": project_relative_path_text(prompt_config_path(VIDEO_PROMPT_KIND)),
                    "imageApiConfigPath": project_relative_path_text(api_config_path()),
                    "videoApiConfigPath": project_relative_path_text(api_config_path()),
                    "imageApiConfig": image_api_config,
                    "videoApiConfig": video_api_config,
                    "useMock": True,
                },
            )

        if path == "/api/prompt-config":
            return json_response(self, HTTPStatus.OK, _prompt_config_payload(IMAGE_PROMPT_KIND))
        if path == f"/api/prompt-config/{IMAGE_PROMPT_KIND}":
            return json_response(self, HTTPStatus.OK, _prompt_config_payload(IMAGE_PROMPT_KIND))
        if path == f"/api/prompt-config/{VIDEO_PROMPT_KIND}":
            return json_response(self, HTTPStatus.OK, _prompt_config_payload(VIDEO_PROMPT_KIND))
        if path == f"/api/runtime-config/{IMAGE_PROMPT_KIND}":
            return json_response(self, HTTPStatus.OK, _api_config_payload(IMAGE_PROMPT_KIND))
        if path == f"/api/runtime-config/{VIDEO_PROMPT_KIND}":
            return json_response(self, HTTPStatus.OK, _api_config_payload(VIDEO_PROMPT_KIND))

        if path == "/api/browser-session":
            return json_response(
                self,
                HTTPStatus.OK,
                BROWSER_SESSIONS.snapshot(SESSION_HEARTBEAT_TIMEOUT_SECONDS),
            )

        if path.startswith("/api/jobs/") and path.endswith("/files"):
            job_id = path.split("/")[3]
            job = STORE.get(job_id)
            if not job:
                return json_response(self, HTTPStatus.NOT_FOUND, {"error": "Job not found"})
            files = []
            if job.output_dir:
                for file_path in sorted(Path(job.output_dir).glob("*")):
                    if file_path.is_file():
                        files.append(
                            {
                                "name": file_path.name,
                                "url": f"/api/jobs/{job_id}/files/{file_path.name}",
                            }
                        )
            return json_response(self, HTTPStatus.OK, {"files": files})

        if path.startswith("/api/jobs/") and "/files/" in path:
            parts = path.split("/")
            job_id = parts[3]
            filename = unquote(parts[-1])
            job = STORE.get(job_id)
            if not job:
                return json_response(self, HTTPStatus.NOT_FOUND, {"error": "Job not found"})
            if not job.output_dir:
                return json_response(self, HTTPStatus.NOT_FOUND, {"error": "Output directory not ready"})
            file_path = Path(job.output_dir) / filename
            if not file_path.exists():
                return json_response(self, HTTPStatus.NOT_FOUND, {"error": "File not found"})
            content_type = "application/octet-stream"
            if file_path.suffix == ".json":
                content_type = "application/json; charset=utf-8"
            elif file_path.suffix == ".txt":
                content_type = "text/plain; charset=utf-8"
            elif file_path.suffix == ".csv":
                content_type = "text/csv; charset=utf-8"
            return text_response(self, HTTPStatus.OK, file_path.read_text(encoding="utf-8"), content_type)

        if path.startswith("/api/jobs/"):
            job_id = path.split("/")[3]
            job = STORE.get(job_id)
            if not job:
                return json_response(self, HTTPStatus.NOT_FOUND, {"error": "Job not found"})
            return json_response(self, HTTPStatus.OK, job_snapshot(job))

        return json_response(self, HTTPStatus.NOT_FOUND, {"error": "Not found"})

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path

        if path in {"/api/generate", f"/api/generate/{IMAGE_PROMPT_KIND}-prompt"}:
            payload = read_body_json(self)
            images = payload.get("images") or []
            if not images:
                return json_response(self, HTTPStatus.BAD_REQUEST, {"error": "No images supplied"})
            job = start_image_job(payload)
            return json_response(self, HTTPStatus.ACCEPTED, {"jobId": job.id, "job": job_snapshot(job)})

        if path == f"/api/generate/{VIDEO_PROMPT_KIND}-prompt":
            payload = read_body_json(self)
            videos = payload.get("videos") or []
            if not videos:
                return json_response(self, HTTPStatus.BAD_REQUEST, {"error": "No videos supplied"})
            job = start_video_job(payload)
            return json_response(self, HTTPStatus.ACCEPTED, {"jobId": job.id, "job": job_snapshot(job)})

        if path == "/api/video/scan-match":
            payload = read_body_json(self)
            return json_response(
                self,
                HTTPStatus.OK,
                build_video_matches(payload.get("videos") or [], payload.get("references") or []),
            )

        if path == "/api/prompt-config":
            payload = read_body_json(self)
            normalized = save_prompt_config(IMAGE_PROMPT_KIND, payload.get("config") or {})
            return json_response(
                self,
                HTTPStatus.OK,
                {
                    "ok": True,
                    "path": project_relative_path_text(prompt_config_path(IMAGE_PROMPT_KIND)),
                    "config": normalized,
                },
            )

        if path == f"/api/prompt-config/{IMAGE_PROMPT_KIND}":
            payload = read_body_json(self)
            normalized = save_prompt_config(IMAGE_PROMPT_KIND, payload.get("config") or {})
            return json_response(
                self,
                HTTPStatus.OK,
                {
                    "ok": True,
                    "path": project_relative_path_text(prompt_config_path(IMAGE_PROMPT_KIND)),
                    "config": normalized,
                },
            )

        if path == f"/api/prompt-config/{VIDEO_PROMPT_KIND}":
            payload = read_body_json(self)
            normalized = save_prompt_config(VIDEO_PROMPT_KIND, payload.get("config") or {})
            return json_response(
                self,
                HTTPStatus.OK,
                {
                    "ok": True,
                    "path": project_relative_path_text(prompt_config_path(VIDEO_PROMPT_KIND)),
                    "config": normalized,
                },
            )

        if path == f"/api/runtime-config/{IMAGE_PROMPT_KIND}":
            payload = read_body_json(self)
            normalized = save_api_config(IMAGE_PROMPT_KIND, payload.get("config") or {})
            return json_response(
                self,
                HTTPStatus.OK,
                {
                    "ok": True,
                    "path": project_relative_path_text(api_config_path()),
                    "config": normalized,
                },
            )

        if path == f"/api/runtime-config/{VIDEO_PROMPT_KIND}":
            payload = read_body_json(self)
            normalized = save_api_config(VIDEO_PROMPT_KIND, payload.get("config") or {})
            return json_response(
                self,
                HTTPStatus.OK,
                {
                    "ok": True,
                    "path": project_relative_path_text(api_config_path()),
                    "config": normalized,
                },
            )

        if path == "/api/browser-session/register":
            payload = read_body_json(self)
            session_id = str(payload.get("sessionId") or "").strip()
            if not session_id:
                return json_response(self, HTTPStatus.BAD_REQUEST, {"error": "Missing sessionId"})
            BROWSER_SESSIONS.register(session_id)
            return json_response(
                self,
                HTTPStatus.OK,
                {
                    "ok": True,
                    "sessionId": session_id,
                    **BROWSER_SESSIONS.snapshot(SESSION_HEARTBEAT_TIMEOUT_SECONDS),
                },
            )

        if path == "/api/browser-session/heartbeat":
            payload = read_body_json(self)
            session_id = str(payload.get("sessionId") or "").strip()
            if not session_id:
                return json_response(self, HTTPStatus.BAD_REQUEST, {"error": "Missing sessionId"})
            known = BROWSER_SESSIONS.heartbeat(session_id)
            if not known:
                BROWSER_SESSIONS.register(session_id)
            return json_response(
                self,
                HTTPStatus.OK,
                {
                    "ok": True,
                    "sessionId": session_id,
                    **BROWSER_SESSIONS.snapshot(SESSION_HEARTBEAT_TIMEOUT_SECONDS),
                },
            )

        if path == "/api/browser-session/close":
            payload = read_body_json(self)
            session_id = str(payload.get("sessionId") or "").strip()
            if not session_id:
                return json_response(self, HTTPStatus.BAD_REQUEST, {"error": "Missing sessionId"})
            BROWSER_SESSIONS.close(session_id)
            return json_response(
                self,
                HTTPStatus.OK,
                {
                    "ok": True,
                    "sessionId": session_id,
                    **BROWSER_SESSIONS.snapshot(SESSION_HEARTBEAT_TIMEOUT_SECONDS),
                },
            )

        if path == "/api/app/terminate":
            payload = read_body_json(self)
            session_id = str(payload.get("sessionId") or "").strip()
            if session_id:
                BROWSER_SESSIONS.close(session_id)
            json_response(
                self,
                HTTPStatus.OK,
                {
                    "ok": True,
                    "message": "Server is shutting down.",
                },
            )
            terminate_server_process(self.server)
            return

        if path.startswith("/api/jobs/") and path.endswith("/open-output"):
            job_id = path.split("/")[3]
            job = STORE.get(job_id)
            if not job:
                return json_response(self, HTTPStatus.NOT_FOUND, {"error": "Job not found"})
            if not job.output_dir:
                return json_response(self, HTTPStatus.BAD_REQUEST, {"error": "Output folder is not ready yet"})
            open_folder(Path(job.output_dir))
            return json_response(self, HTTPStatus.OK, {"ok": True, "path": job.output_dir})

        return json_response(self, HTTPStatus.NOT_FOUND, {"error": "Not found"})

    def _serve_frontend(self, filename: str, content_type: str) -> None:
        file_path = FRONTEND_DIR / filename
        if not file_path.exists():
            return json_response(self, HTTPStatus.NOT_FOUND, {"error": f"Missing frontend file: {filename}"})
        text_response(self, HTTPStatus.OK, file_path.read_text(encoding="utf-8"), content_type)


def main() -> None:
    ensure_dir(default_output_root())
    ensure_dir(default_output_root(IMAGE_PROMPT_KIND))
    ensure_dir(default_output_root(VIDEO_PROMPT_KIND))
    ensure_dir(Path(__file__).resolve().parents[2] / "uploads")
    load_api_config()
    load_prompt_config(IMAGE_PROMPT_KIND)
    load_prompt_config(VIDEO_PROMPT_KIND)
    server = ThreadingHTTPServer(("127.0.0.1", 8000), DemoHandler)
    start_browser_session_reaper(server)
    print("Prompt tool demo running at http://127.0.0.1:8000")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
