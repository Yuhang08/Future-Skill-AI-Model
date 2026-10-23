"""The reskilling endpoints integrated into the original FastAPI application.

Runs locally. For a public launch, add real authentication, HTTPS, rate limiting,
retention controls, audited photo handling and production infrastructure.
"""
import hashlib
import hmac
import math
import mimetypes
import os
import re
import secrets
import uuid
import base64
from pathlib import Path
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse

from .catalog import CAREERS, public_catalog
from .engine import (
    InputError, validate_profile, skill_gaps, generate_schedule,
    points_for_task, tree_details, feedback_for_completion,
)
from .storage import Store

router = APIRouter()
BASE = Path(__file__).resolve().parent
DEV_INVENTORY_ENABLED = os.environ.get("FUTURESKILL_DEV_INVENTORY") == "1"
DEMO_SCENARIOS = {
    "default", "fresh", "returning", "no-gap", "partial",
    "edit", "dashboard", "tasks", "tree", "schedule", "evidence", "loading",
}
DATA_DIR = Path(os.environ.get("FUTURESKILL_DATA_DIR", BASE.parent / "instance"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS = DATA_DIR / "uploads"
UPLOADS.mkdir(parents=True, exist_ok=True)
STORE = Store(DATA_DIR / "futureskill.sqlite3")
SECRET_FILE = DATA_DIR / ".session_secret"
if SECRET_FILE.is_file():
    SECRET = SECRET_FILE.read_bytes()
else:
    SECRET = secrets.token_bytes(32)
    SECRET_FILE.write_bytes(SECRET)
    try:
        os.chmod(SECRET_FILE, 0o600)
    except OSError:
        pass

MAX_IMAGE_BYTES = 5 * 1024 * 1024
TASK_RE = re.compile(r"[a-f0-9-]{36}\Z")
PHOTO_RE = re.compile(r"[a-f0-9]{32}\.(jpg|png|webp)\Z")


def sign(text: str) -> str:
    return hmac.new(SECRET, text.encode('utf-8'), hashlib.sha256).hexdigest()


def decode_session(cookie: str | None) -> str | None:
    if not cookie or '.' not in cookie:
        return None
    uid, signature = cookie.split('.', 1)
    if not re.fullmatch(r'[a-f0-9]{32}', uid):
        return None
    return uid if hmac.compare_digest(sign(uid), signature) else None


async def session_cookie_middleware(request: Request, call_next):
    """Identical anonymous browser identity shared by old and new routes."""
    demo_mode = DEV_INVENTORY_ENABLED and (
        request.query_params.get("demo") == "1"
        or request.url.path.startswith("/__dev/demo/")
    )
    scenario = request.query_params.get(
        "demo_scenario",
        request.query_params.get("scenario", "default")
        if request.url.path.startswith("/__dev/demo/")
        else "default",
    )
    if scenario not in DEMO_SCENARIOS:
        scenario = "default"
    cookie_name = f"FS_DEMO_{scenario.upper().replace('-', '_')}" if demo_mode else "FS_SESSION"
    user_id = decode_session(request.cookies.get(cookie_name))
    new_cookie = user_id is None
    if not user_id:
        user_id = uuid.uuid4().hex
    request.state.futureskill_user_id = user_id
    request.state.futureskill_demo = demo_mode
    request.state.futureskill_demo_scenario = scenario
    response = await call_next(request)
    if new_cookie:
        # secure=False is only acceptable for this localhost demo.
        response.set_cookie(
            cookie_name, f'{user_id}.{sign(user_id)}',
            httponly=True, samesite='lax', secure=False, path='/',
        )
    return response


def uid(request: Request) -> str:
    return request.state.futureskill_user_id


def csrf_token(request: Request) -> str:
    return sign('csrf:' + uid(request))


def require_csrf(request: Request):
    supplied = request.headers.get('X-CSRF-Token', '')
    if not hmac.compare_digest(supplied, csrf_token(request)):
        raise HTTPException(403, detail='Invalid session token. Refresh the page.')


def user_error(message, status=400):
    return JSONResponse({'error': message}, status_code=status)


def valid_image(blob: bytes, content_type: str):
    if not 24 <= len(blob) <= MAX_IMAGE_BYTES:
        return None
    if (content_type == 'image/png' and blob.startswith(b'\x89PNG\r\n\x1a\n')
            and blob[-12:-8] == b'\x00\x00\x00\x00' and blob[-8:-4] == b'IEND'):
        return '.png'
    if (content_type == 'image/jpeg' and blob.startswith(b'\xff\xd8\xff')
            and blob.endswith(b'\xff\xd9')):
        return '.jpg'
    if (content_type == 'image/webp' and blob[:4] == b'RIFF'
            and blob[8:12] == b'WEBP'):
        return '.webp'
    return None


def delete_photo(filename):
    if filename and PHOTO_RE.fullmatch(filename):
        (UPLOADS / filename).unlink(missing_ok=True)


def public_state(user_id: str, demo_mode=False, demo_scenario="default"):
    profile = STORE.get_profile(user_id)
    state = {'catalog': public_catalog(), 'profile': profile}
    all_tasks = STORE.list_tasks(user_id)
    points = sum(points_for_task(t) for t in all_tasks if t['completed'])
    state['tree'] = tree_details(points)
    if profile is None:
        return state

    career = profile['target_career']
    tasks = [t for t in all_tasks if t['career'] == career]
    for task in tasks:
        task['completed'] = bool(task['completed'])
        proof_query = urlencode({
            "demo": "1",
            "demo_scenario": demo_scenario,
        }) if demo_mode else ""
        task['proof_url'] = (
            f"/api/tasks/{task['id']}/proof?{proof_query}"
            if task['proof_path'] else None
        )
        task.pop('proof_path', None)
        task['points'] = points_for_task(task)
    gaps = skill_gaps(profile)
    expected = sum(item['estimated_hours'] for item in gaps.values())
    learned = sum(t['hours'] for t in tasks if t['completed'] and t['kind'] == 'learning')
    checked = sum(bool(t['completed']) for t in tasks)
    remaining = {}
    for skill, item in gaps.items():
        completed_learning = sum(t['hours'] for t in tasks
                                 if t['completed'] and t['kind'] == 'learning' and t['skill'] == skill)
        remaining[skill] = max(0., item['estimated_hours'] - completed_learning)
        item['remaining_hours'] = round(remaining[skill], 2)
    state.update({
        'tasks': tasks, 'gaps': gaps,
        'stats': {
            'learning_hours_completed': round(learned, 2),
            'estimated_learning_hours': round(expected, 2),
            'study_progress_pct': round(min(100, learned / expected * 100), 1) if expected else 100,
            'task_progress_pct': round(checked / len(tasks) * 100, 1) if tasks else (100 if not expected else 0),
            'completed_tasks': checked, 'total_tasks': len(tasks),
            'completed_all_time': sum(bool(t['completed']) for t in all_tasks),
            'remaining_hours': round(sum(remaining.values()), 2),
            'estimated_weeks_remaining': math.ceil(sum(remaining.values()) / (profile['weekly_hours'] * .8))
                                         if sum(remaining.values()) else 0,
        }
    })
    return state


def completed_by_skill(user_id, career):
    done = {}
    for task in STORE.list_tasks(user_id, career):
        if task['completed'] and task['kind'] == 'learning':
            done[task['skill']] = done.get(task['skill'], 0) + task['hours']
    return done


def state_for_request(request: Request):
    return public_state(
        uid(request),
        demo_mode=getattr(request.state, "futureskill_demo", False),
        demo_scenario=getattr(request.state, "futureskill_demo_scenario", "default"),
    )


def demo_profile(scenario: str):
    career = "Data Analyst"
    role = CAREERS[career]["skills"]
    if scenario == "no-gap":
        skill_levels = {name: details["required"] for name, details in role.items()}
        weekly_hours, weeks = 6, 8
    elif scenario == "partial":
        skill_levels = {name: 0 for name in role}
        weekly_hours, weeks = 1, 1
    else:
        skill_levels = {
            name: min(details["required"], 2 if index % 2 == 0 else 1)
            for index, (name, details) in enumerate(role.items())
        }
        weekly_hours, weeks = 6, 8
    return validate_profile({
        "target_career": career,
        "skills": skill_levels,
        "user_type": "career_changer" if scenario == "returning" else "student",
        "current_industry": "Sample demo profile",
        "experience": "some",
        "personal_goal": "Development-only sample data — safe to change.",
        "weekly_hours": weekly_hours,
        "target_weeks": weeks,
        "preferred_days": ["Tuesday", "Thursday", "Saturday"],
        "learning_style": "project",
    })


def seed_demo_session(user_id: str, scenario: str):
    profile = STORE.get_profile(user_id)
    if profile is not None:
        return
    profile = demo_profile(scenario)
    plan = generate_schedule(profile)
    STORE.save_profile(user_id, profile)
    for filename in STORE.insert_plan(user_id, profile["target_career"], plan["tasks"]):
        delete_photo(filename)

    # Provide a visible completed win and an example photo only in the isolated
    # development session. It never uses a real learner's session identifier.
    tasks = STORE.list_tasks(user_id, profile["target_career"])
    learning_task = next((task for task in tasks if task["kind"] == "learning"), None)
    if scenario not in {"fresh", "no-gap", "partial"} and learning_task:
        STORE.set_status(user_id, learning_task["id"], True)
        png = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/bP8AAAAASUVORK5CYII="
        )
        filename = f"{uuid.uuid4().hex}.png"
        (UPLOADS / filename).write_bytes(png)
        STORE.set_proof(user_id, learning_task["id"], filename)


if DEV_INVENTORY_ENABLED:
    @router.get("/__dev/career-preview")
    def development_career_preview():
        # Browser-memory-only samples; never replace sessionStorage or learner records.
        html = (BASE.parent / "static" / "career-workspace.html").read_text(encoding="utf-8")
        html = html.replace("</head>", "<script>window.FutureSkillCareerPreview=true;</script></head>", 1)
        return HTMLResponse(html, headers={"Cache-Control": "no-store"})

    @router.get("/__dev/brand")
    def development_brand_preview():
        return FileResponse(BASE.parent / "brand-preview.html", media_type="text/html")

    @router.get("/__dev/screens")
    def development_screen_inventory():
        return FileResponse(BASE.parent / "static" / "dev-screens.html", media_type="text/html")

    @router.get("/__dev/demo/open")
    def open_demo_screen(
        request: Request,
        screen: str = "S10",
        scenario: str = "default",
        career: str | None = None,
    ):
        if scenario not in DEMO_SCENARIOS:
            raise HTTPException(status_code=400, detail="Unknown demo scenario.")
        if scenario != "fresh":
            seed_demo_session(uid(request), scenario)

        params = {
            "demo": "1",
            "demo_scenario": scenario,
            "screen": screen,
        }
        if career:
            params["career"] = career[:100]
        return RedirectResponse(f"/reskilling?{urlencode(params)}", status_code=303)


@router.get('/reskilling')
def reskilling_page():
    page = BASE / 'index.html'
    if not DEV_INVENTORY_ENABLED:
        return FileResponse(page, media_type='text/html')
    html = page.read_text(encoding='utf-8').replace(
        '</header>',
        '</header><div class="dev-inventory-shortcut"><a href="/__dev/screens">Development only · Open screen inventory</a></div>',
        1,
    )
    return HTMLResponse(html)


@router.get('/api/state')
def get_state(request: Request):
    state = state_for_request(request)
    state['csrf'] = csrf_token(request)
    return state


@router.post('/api/plan')
async def make_plan(request: Request):
    require_csrf(request)
    try:
        data = validate_profile(await request.json())
        old_done = completed_by_skill(uid(request), data['target_career'])
        plan = generate_schedule(data, old_done)
        STORE.save_profile(uid(request), data)
        old_photos = STORE.insert_plan(uid(request), data['target_career'], plan['tasks'])
        for filename in old_photos:
            delete_photo(filename)
        return {'message': plan['message'], 'plan': plan['remaining_after_plan'],
                'state': state_for_request(request)}
    except (InputError, ValueError, TypeError, KeyError) as exc:
        return user_error(str(exc))


@router.post('/api/replan')
async def replan(request: Request):
    require_csrf(request)
    profile = STORE.get_profile(uid(request))
    if profile is None:
        return user_error('Create your pathway first.', 409)
    try:
        changes = await request.json()
        if not isinstance(changes, dict) or not set(changes).issubset(
                {'weekly_hours', 'target_weeks', 'preferred_days'}):
            raise InputError('Only scheduling options can be changed here.')
        data = validate_profile({**profile, **changes})
        plan = generate_schedule(data, completed_by_skill(uid(request), data['target_career']))
        STORE.save_profile(uid(request), data)
        deleted = STORE.insert_plan(uid(request), data['target_career'], plan['tasks'])
        for filename in deleted:
            delete_photo(filename)
        return {'message': 'Unfinished tasks were rescheduled; finished tasks and XP are safe.',
                'plan': plan['remaining_after_plan'], 'state': state_for_request(request)}
    except (InputError, ValueError, TypeError, KeyError) as exc:
        return user_error(str(exc))


def check_task_id(task_id):
    if not TASK_RE.fullmatch(task_id):
        raise HTTPException(404, detail='Task not found.')


@router.post('/api/tasks/{task_id}/status')
async def task_status(request: Request, task_id: str):
    require_csrf(request)
    check_task_id(task_id)
    try:
        body = await request.json()
    except ValueError:
        return user_error('Invalid JSON.')
    if not isinstance(body, dict) or not isinstance(body.get('completed'), bool):
        return user_error('completed must be true or false.')
    before = state_for_request(request)['tree']
    task = STORE.set_status(uid(request), task_id, body['completed'])
    if not task:
        return user_error('Task not found for this browser session.', 404)
    after = state_for_request(request)
    count = sum(t['completed'] and t['kind'] == 'learning' for t in after.get('tasks', []))
    message = (feedback_for_completion(count, task['kind'], after['tree'], before)
               if body['completed'] else 'Updated! You can return whenever you are ready.')
    return {'message': message, 'state': after}


@router.post('/api/tasks/{task_id}/proof')
async def upload_proof(request: Request, task_id: str, photo: UploadFile = File(...)):
    require_csrf(request)
    check_task_id(task_id)
    if not STORE.get_task(uid(request), task_id):
        return user_error('Task not found for this browser session.', 404)
    blob = await photo.read(MAX_IMAGE_BYTES + 1)
    extension = valid_image(blob, photo.content_type or '')
    await photo.close()
    if extension is None:
        return user_error('Upload a JPG, PNG or WEBP image smaller than 5 MB.')
    filename = uuid.uuid4().hex + extension
    (UPLOADS / filename).write_bytes(blob)
    old_file, exists = STORE.set_proof(uid(request), task_id, filename)
    if not exists:
        delete_photo(filename)
        return user_error('Task not found.', 404)
    delete_photo(old_file)
    return {'message': 'Photo saved as task evidence. It is not automatically graded.',
            'state': state_for_request(request)}


@router.get('/api/tasks/{task_id}/proof')
def read_proof(request: Request, task_id: str):
    check_task_id(task_id)
    task = STORE.get_task(uid(request), task_id)
    if not task or not task['proof_path'] or not PHOTO_RE.fullmatch(task['proof_path']):
        return user_error('Photo not found.', 404)
    image_file = UPLOADS / task['proof_path']
    if not image_file.is_file():
        return user_error('Photo not found.', 404)
    return FileResponse(
        image_file, media_type=mimetypes.guess_type(image_file.name)[0],
        headers={'X-Content-Type-Options': 'nosniff',
                 'Content-Security-Policy': "default-src 'none'; sandbox",
                 'Cache-Control': 'no-store'},
    )
