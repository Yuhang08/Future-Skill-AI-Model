"""FutureSkill AI local web app — no pip install needed.

Run: python app.py
Open: http://localhost:8000

Local demo only. For public deployment, add real user accounts,
HTTPS, production hosting, rate limiting and stronger upload validation.
"""

import base64
import hashlib
import hmac
import json
import mimetypes
import os
import re
import secrets
import sqlite3
import uuid
from datetime import date
from email.parser import BytesParser
from email.policy import default
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from catalog import CAREERS, public_catalog
from engine import (InputError, feedback_for_completion, generate_schedule,
                    points_for_task, skill_gaps, tree_details, validate_profile)
from storage import Store

BASE = Path(__file__).resolve().parent
INSTANCE = Path(os.environ.get("FUTURESKILL_DATA_DIR", BASE / "instance"))
INSTANCE.mkdir(parents=True, exist_ok=True)
UPLOADS = INSTANCE / "uploads"
UPLOADS.mkdir(parents=True, exist_ok=True)
STORE = Store(INSTANCE / "futureskill.sqlite3")
SECRET_PATH = INSTANCE / ".session_secret"
if SECRET_PATH.exists():
    SECRET = SECRET_PATH.read_bytes()
else:
    SECRET = secrets.token_bytes(32)
    SECRET_PATH.write_bytes(SECRET)
    try:
        os.chmod(SECRET_PATH, 0o600)
    except OSError:
        pass

MAX_IMAGE = 5 * 1024 * 1024
MAX_BODY = MAX_IMAGE + 100_000


def sign(value):
    return hmac.new(SECRET, value.encode(), hashlib.sha256).hexdigest()


def cookie_identity(cookie_value):
    if not cookie_value or "." not in cookie_value:
        return None
    uid, mac = cookie_value.split(".", 1)
    if not re.fullmatch(r"[a-f0-9]{32}", uid):
        return None
    if not hmac.compare_digest(sign(uid), mac):
        return None
    return uid


def create_cookie():
    uid = uuid.uuid4().hex
    return uid, f"{uid}.{sign(uid)}"


def valid_image(content, reported_type):
    """Allow a narrow set of image formats; never accept SVG or HTML."""
    if len(content) > MAX_IMAGE or len(content) < 24:
        return None
    if (reported_type == "image/png" and content.startswith(b"\x89PNG\r\n\x1a\n")
            and content[-12:-8] == b"\x00\x00\x00\x00" and content[-8:-4] == b"IEND"):
        return ".png", "image/png"
    if (reported_type == "image/jpeg" and content.startswith(b"\xff\xd8\xff")
            and content[-2:] == b"\xff\xd9"):
        return ".jpg", "image/jpeg"
    if (reported_type == "image/webp" and content[:4] == b"RIFF" and
            content[8:12] == b"WEBP"):
        return ".webp", "image/webp"
    return None


def public_state(user_id):
    profile = STORE.get_profile(user_id)
    result = {"catalog": public_catalog(), "profile": profile}
    all_tasks = STORE.list_tasks(user_id)
    total_points = sum(points_for_task(task) for task in all_tasks if task["completed"])
    tree = tree_details(total_points)
    result["tree"] = tree
    if profile is None:
        return result

    career = profile["target_career"]
    tasks = [task for task in all_tasks if task["career"] == career]
    for item in tasks:
        item["completed"] = bool(item["completed"])
        item["proof_url"] = f"/api/tasks/{item['id']}/proof" if item["proof_path"] else None
        del item["proof_path"]
        item["points"] = points_for_task(item)

    gaps = skill_gaps(profile)
    expected = sum(info["estimated_hours"] for info in gaps.values())
    learned = sum(task["hours"] for task in tasks if task["completed"] and task["kind"] == "learning")
    checked = sum(bool(task["completed"]) for task in tasks)
    total_tasks = len(tasks)
    remaining = {skill: max(0.0, info["estimated_hours"] - sum(
        task["hours"] for task in tasks if task["completed"] and task["kind"] == "learning" and task["skill"] == skill
    )) for skill, info in gaps.items()}
    for skill, hours in remaining.items():
        gaps[skill]["remaining_hours"] = round(hours, 2)

    result.update({
        "tasks": tasks,
        "gaps": gaps,
        "stats": {
            "learning_hours_completed": round(learned, 2),
            "estimated_learning_hours": round(expected, 2),
            "study_progress_pct": round(min(100, learned / expected * 100), 1) if expected else 100,
            "task_progress_pct": round(checked / total_tasks * 100, 1) if total_tasks else (100 if not expected else 0),
            "completed_tasks": checked, "total_tasks": total_tasks,
            "completed_all_time": sum(bool(task["completed"]) for task in all_tasks),
            "remaining_hours": round(sum(remaining.values()), 2),
            "estimated_weeks_remaining": (
                __import__("math").ceil(sum(remaining.values()) / (profile["weekly_hours"] * 0.8))
                if remaining else 0
            ),
        },
    })
    return result


class Handler(BaseHTTPRequestHandler):
    server_version = "FutureSkill/1.0"

    def setup(self):
        super().setup()
        self._new_cookie = None
        self._uid = None

    def uid(self):
        if self._uid:
            return self._uid
        try:
            cookie = SimpleCookie()
            cookie.load(self.headers.get("Cookie", ""))
            value = cookie["FS_SESSION"].value if "FS_SESSION" in cookie else None
        except Exception:
            value = None
        uid = cookie_identity(value)
        if not uid:
            uid, self._new_cookie = create_cookie()
        self._uid = uid
        return uid

    def csrf(self):
        return sign("csrf:" + self.uid())

    def respond(self, status, content, content_type="application/json; charset=utf-8", extra_headers=None):
        if isinstance(content, (dict, list)):
            content = json.dumps(content, ensure_ascii=False).encode("utf-8")
        elif isinstance(content, str):
            content = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        if self._new_cookie:
            self.send_header("Set-Cookie", f"FS_SESSION={self._new_cookie}; HttpOnly; SameSite=Lax; Path=/")
        for key, value in (extra_headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(content)

    def fail(self, status, message):
        self.respond(status, {"error": message})

    def get_json(self):
        if not self.headers.get("Content-Type", "").startswith("application/json"):
            raise InputError("Expected JSON request.")
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > MAX_BODY:
            raise InputError("Invalid request size.")
        try:
            return json.loads(self.rfile.read(length))
        except (json.JSONDecodeError, UnicodeError):
            raise InputError("Invalid JSON body.") from None

    def authenticated_post(self):
        return hmac.compare_digest(self.headers.get("X-CSRF-Token", ""), self.csrf())

    def do_GET(self):
        path = urlparse(self.path).path
        user_id = self.uid()
        if path == "/api/state":
            result = public_state(user_id)
            result["csrf"] = self.csrf()
            return self.respond(200, result)
        match = re.fullmatch(r"/api/tasks/([a-f0-9-]{36})/proof", path)
        if match:
            task = STORE.get_task(user_id, match.group(1))
            if not task or not task["proof_path"]:
                return self.fail(404, "Photo not found.")
            filename = task["proof_path"]
            file_path = UPLOADS / filename
            if not re.fullmatch(r"[a-f0-9]{32}\.(jpg|png|webp)", filename) or not file_path.is_file():
                return self.fail(404, "Photo not found.")
            kind = mimetypes.guess_type(filename)[0] or "application/octet-stream"
            return self.respond(200, file_path.read_bytes(), kind,
                                {"Content-Security-Policy": "default-src 'none'; sandbox",
                                 "Content-Disposition": 'inline; filename="learning-proof"'})
        static_files = {
            "/": (BASE / "index.html", "text/html; charset=utf-8"),
            "/static/app.js": (BASE / "static" / "app.js", "text/javascript; charset=utf-8"),
            "/static/style.css": (BASE / "static" / "style.css", "text/css; charset=utf-8"),
        }
        if path in static_files:
            file_path, content_type = static_files[path]
            return self.respond(200, file_path.read_bytes(), content_type)
        return self.fail(404, "Page not found.")

    def do_POST(self):
        path = urlparse(self.path).path
        user_id = self.uid()
        if not self.authenticated_post():
            return self.fail(403, "Invalid session token. Refresh the page.")
        try:
            if path == "/api/plan":
                data = validate_profile(self.get_json())
                old = STORE.get_profile(user_id)
                # For same-career plans, keep completed tasks and their practice hours.
                previous = STORE.list_tasks(user_id, data["target_career"])
                completed_by_skill = {}
                for task in previous:
                    if task["completed"] and task["kind"] == "learning":
                        completed_by_skill[task["skill"]] = completed_by_skill.get(task["skill"], 0) + task["hours"]
                plan = generate_schedule(data, completed_by_skill)
                STORE.save_profile(user_id, data)
                removed = STORE.insert_plan(user_id, data["target_career"], plan["tasks"])
                for filename in removed:
                    self._delete_old_photo(filename)
                return self.respond(200, {"message": plan["message"], "plan": plan["remaining_after_plan"], "state": public_state(user_id)})

            if path == "/api/replan":
                current = STORE.get_profile(user_id)
                if not current:
                    return self.fail(409, "Create a learning plan first.")
                changes = self.get_json()
                if not isinstance(changes, dict):
                    raise InputError("Invalid rescheduling options.")
                allowed = {"weekly_hours", "target_weeks", "preferred_days"}
                if any(k not in allowed for k in changes):
                    raise InputError("Only scheduling options can be changed here.")
                updated = validate_profile({**current, **changes})
                previous = STORE.list_tasks(user_id, updated["target_career"])
                completed_by_skill = {}
                for task in previous:
                    if task["completed"] and task["kind"] == "learning":
                        completed_by_skill[task["skill"]] = completed_by_skill.get(task["skill"], 0) + task["hours"]
                plan = generate_schedule(updated, completed_by_skill)
                STORE.save_profile(user_id, updated)
                removed = STORE.insert_plan(user_id, updated["target_career"], plan["tasks"])
                for filename in removed:
                    self._delete_old_photo(filename)
                return self.respond(200, {"message": "Unfinished work has been rescheduled. Completed tasks are saved.",
                                          "plan": plan["remaining_after_plan"], "state": public_state(user_id)})

            status_match = re.fullmatch(r"/api/tasks/([a-f0-9-]{36})/status", path)
            if status_match:
                task_id = status_match.group(1)
                body = self.get_json()
                if not isinstance(body, dict) or not isinstance(body.get("completed"), bool):
                    raise InputError("completed must be true or false.")
                before = public_state(user_id)["tree"]
                task = STORE.set_status(user_id, task_id, body["completed"])
                if not task:
                    return self.fail(404, "Task not found for this session.")
                after = public_state(user_id)
                done = len([t for t in after.get("tasks", []) if t["completed"] and t["kind"] == "learning"])
                message = feedback_for_completion(done, task["kind"], after["tree"], before) if body["completed"] else "Updated! You can return to this task whenever you're ready."
                return self.respond(200, {"message": message, "state": after})

            proof_match = re.fullmatch(r"/api/tasks/([a-f0-9-]{36})/proof", path)
            if proof_match:
                task_id = proof_match.group(1)
                if not STORE.get_task(user_id, task_id):
                    return self.fail(404, "Task not found for this session.")
                raw_type = self.headers.get("Content-Type", "")
                length = int(self.headers.get("Content-Length", "0"))
                if not raw_type.startswith("multipart/form-data;") or length <= 0 or length > MAX_BODY:
                    raise InputError("Upload one image smaller than 5 MB.")
                data = self.rfile.read(length)
                msg = BytesParser(policy=default).parsebytes((f"Content-Type: {raw_type}\r\nMIME-Version: 1.0\r\n\r\n").encode() + data)
                parts = [p for p in msg.iter_parts() if p.get_param("name", header="content-disposition") == "photo"]
                if len(parts) != 1:
                    raise InputError("Please select exactly one photo.")
                part = parts[0]
                blob = part.get_payload(decode=True)
                detected = valid_image(blob, part.get_content_type())
                if not detected:
                    raise InputError("Use a real JPG, PNG or WEBP image under 5 MB.")
                extension, _ = detected
                filename = uuid.uuid4().hex + extension
                (UPLOADS / filename).write_bytes(blob)
                old_file, exists = STORE.set_proof(user_id, task_id, filename)
                if not exists:
                    (UPLOADS / filename).unlink(missing_ok=True)
                    return self.fail(404, "Task not found.")
                self._delete_old_photo(old_file)
                return self.respond(200, {"message": "Photo saved as task evidence. It is not automatically graded.",
                                          "state": public_state(user_id)})
            return self.fail(404, "Unknown action.")
        except (InputError, ValueError, TypeError) as exc:
            return self.fail(400, str(exc))
        except Exception as exc:
            # Avoid exposing internal information to clients.
            self.log_error("Server problem: %s", exc)
            return self.fail(500, "Something went wrong. Please retry.")

    @staticmethod
    def _delete_old_photo(filename):
        if filename and re.fullmatch(r"[a-f0-9]{32}\.(jpg|png|webp)", filename):
            (UPLOADS / filename).unlink(missing_ok=True)


def serve(port=8000):
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print("\n🌱 FutureSkill AI is running!")
    print(f"Open your browser: http://localhost:{port}")
    print("Press Ctrl+C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nGoodbye!")
    finally:
        server.server_close()


if __name__ == "__main__":
    serve(int(os.environ.get("PORT", "8000")))
