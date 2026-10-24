"""Flask interview module mounted inside FutureSkill's FastAPI application."""
import threading
import time
import uuid

from flask import Flask, jsonify, make_response, render_template, request

from reskilling.explanation_provider import ProviderSettings

from .career_data import find_career, find_career_id, get_careers
from .history_store import all_text, global_count, init, insert
from .interview_engine import adaptive_plan, feedback_for, generate_question, report
from .semantic_validator import check_question, embed
from .speech_service import transcribe

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["MAX_CONTENT_LENGTH"] = 11 * 1024 * 1024

sessions = {}
lock = threading.RLock()
TTL = 3600
MODES = {"HR", "Technical", "Mixed"}
LANGUAGES = {"English", "中文", "Bahasa Melayu"}


def fail(message, code=400):
    return jsonify(error=message), code


def provider_available():
    # Presence/configuration check only; it never contacts the provider.
    try:
        ProviderSettings.from_environment()
    except Exception:
        return False
    return True


def guest_id():
    value = request.cookies.get("fs_guest", "")
    if len(value) == 64 and all(character in "0123456789abcdef" for character in value):
        return value
    return None


def ensure_guest(response, guest):
    if not guest_id():
        response.set_cookie(
            "fs_guest", guest, httponly=True, secure=request.is_secure,
            samesite="Lax", max_age=365 * 24 * 3600, path="/",
        )
    return response


def current_session(data):
    session_id = str(data.get("session_id", ""))
    if len(session_id) != 32 or not all(character in "0123456789abcdef" for character in session_id):
        return None
    with lock:
        entry = sessions.get(session_id)
        if not entry:
            return None
        if time.time() - entry["created"] > TTL or entry["guest"] != guest_id():
            sessions.pop(session_id, None)
            return None
        return entry


def cache_embedding(question):
    return embed(question)


@app.get("/")
def home():
    return render_template("interview.html")


@app.get("/api/careers")
def careers():
    try:
        items = get_careers()
    except (OSError, ValueError):
        return fail("The career catalogue is temporarily unavailable.", 503)
    options = [
        {
            "id": item["id"],
            "title": item["title"],
            "supported_context": bool(item["skills"] or item["description"]),
        }
        for item in items
    ]
    return jsonify(
        careers=[item["title"] for item in items],
        career_options=options,
        count=len(items),
        source="FutureSkill canonical career catalogue",
    )


@app.get("/api/interview/availability")
def availability():
    return jsonify(available=provider_available())


@app.get("/api/interview/history-count")
def count_history():
    guest = guest_id()
    return jsonify(
        personal_count=len(all_text(guest)) if guest else 0,
        global_count=global_count(),
    )


@app.post("/api/interview/start")
def start():
    data = request.get_json(silent=True) or {}
    role = str(data.get("role", ""))
    mode = str(data.get("mode", "Mixed"))
    language = str(data.get("language", "English"))
    try:
        question_count = int(data.get("question_count", 5))
    except (ValueError, TypeError):
        return fail("Choose 3, 5 or 10 interview questions.")
    if mode not in MODES or language not in LANGUAGES or question_count not in (3, 5, 10):
        return fail("Choose a valid interview type, language and question count.")
    if not provider_available():
        return fail("AI interview practice is temporarily unavailable.", 503)
    try:
        facts = find_career(role)
    except (OSError, ValueError):
        return fail("The career catalogue is temporarily unavailable.", 503)
    if not facts:
        return fail("Choose a career from the supported FutureSkill catalogue.")
    career_id = str(data.get("career_id", ""))
    id_facts = find_career_id(career_id) if career_id else facts
    if career_id and (not id_facts or id_facts["title"] != facts["title"]):
        return fail("The selected career no longer matches the supported catalogue.")

    guest = guest_id() or uuid.uuid4().hex + uuid.uuid4().hex
    session_id = uuid.uuid4().hex
    try:
        previous = all_text(guest)
        question = pick(role, mode, language, facts, previous, [], None)
    except Exception:
        # Keep provider and credential details out of logs and learner-facing errors.
        app.logger.warning("Interview question generation failed; provider details redacted.")
        return fail("AI interview practice is temporarily unavailable.", 503)

    with lock:
        sessions[session_id] = {
            "created": time.time(),
            "guest": guest,
            "role": role,
            "mode": mode,
            "language": language,
            "question": question,
            "history": [],
            "awaiting_next": False,
            "max_questions": question_count,
            "previous": previous,
            "facts": facts,
        }
    response = make_response(jsonify(
        session_id=session_id,
        question_number=1,
        max_questions=question_count,
        practice_scope="general" if not facts.get("skills") and not facts.get("description") else "catalogue_context",
        **question,
    ))
    return ensure_guest(response, guest)


def pick(role, mode, language, facts, previous, current, adaptive):
    recent_answer = adaptive.get("last_answer", "") if adaptive else ""
    difficulty = adaptive.get("difficulty", "standard") if adaptive else "standard"
    focus_history = previous[-20:] + current
    for _attempt in range(3):
        question = generate_question(
            role, mode, language, focus_history, facts, difficulty, recent_answer
        )
        approved, _reason = check_question(
            question["question"], previous, current, cache_embedding
        )
        if approved:
            return question
        focus_history.append(question["question"])
    raise ValueError("Could not generate a sufficiently distinct interview question")


@app.post("/api/interview/transcribe")
def transcript():
    session = current_session(request.form)
    if not session:
        return fail("Interview session expired. Start a new practice session.", 404)
    audio = request.files.get("audio")
    if not audio:
        return fail("No recording was received.")
    try:
        return jsonify(transcript=transcribe(audio))
    except ValueError as error:
        return fail(str(error))
    except Exception:
        app.logger.warning("Optional interview transcription failed; provider details redacted.")
        return fail("Audio transcription is temporarily unavailable. You can type your answer.", 503)


@app.post("/api/interview/feedback")
def feedback():
    data = request.get_json(silent=True) or {}
    session = current_session(data)
    if not session:
        return fail("Interview session expired. Start a new practice session.", 404)
    answer = str(data.get("answer", "")).strip()
    if not 3 <= len(answer) <= 3500:
        return fail("Keep your answer between 3 and 3,500 characters.")
    with lock:
        if session["awaiting_next"]:
            return fail("This answer has already been submitted.", 409)
        session["awaiting_next"] = True
    try:
        result = feedback_for(
            session["question"]["question"], answer,
            session["role"], session["mode"], session["language"],
        )
        # The persistent index stores question text and career only, never answers.
        insert(session["guest"], str(data["session_id"]),
               session["question"]["question"], session["role"])
        with lock:
            session["history"].append({
                "question": session["question"]["question"],
                "answer": answer,
                "feedback": result,
            })
        return jsonify(
            feedback=result,
            finished=len(session["history"]) >= session["max_questions"],
        )
    except Exception:
        with lock:
            session["awaiting_next"] = False
        app.logger.warning("Interview feedback failed; provider details redacted.")
        return fail("Feedback is temporarily unavailable. Your answer was not saved.", 503)


@app.post("/api/interview/next")
def next_question():
    data = request.get_json(silent=True) or {}
    session = current_session(data)
    if not session:
        return fail("Interview session expired. Start a new practice session.", 404)
    if not session["awaiting_next"]:
        return fail("Submit your answer before moving to the next question.", 409)
    if len(session["history"]) >= session["max_questions"]:
        result = report(session["history"], session["role"], session["language"])
        with lock:
            sessions.pop(str(data["session_id"]), None)
        return jsonify(finished=True, report=result)
    past = list(session["history"])
    adaptive = adaptive_plan(past)
    adaptive["last_answer"] = past[-1]["answer"]
    try:
        question = pick(
            session["role"], session["mode"], session["language"],
            session["facts"], session["previous"],
            [item["question"] for item in past], adaptive,
        )
    except Exception:
        app.logger.warning("Next interview question failed; provider details redacted.")
        return fail("A new question is temporarily unavailable. Your current feedback is still here.", 503)
    with lock:
        session["question"] = question
        session["awaiting_next"] = False
    return jsonify(
        finished=False,
        question_number=len(past) + 1,
        max_questions=session["max_questions"],
        **question,
    )


@app.post("/api/interview/end")
def end():
    data = request.get_json(silent=True) or {}
    session = current_session(data)
    if not session:
        return fail("Interview session expired. Start a new practice session.", 404)
    if not session["history"]:
        return fail("Answer a question before viewing the report.")
    result = report(session["history"], session["role"], session["language"])
    with lock:
        sessions.pop(str(data["session_id"]), None)
    return jsonify(report=result)


@app.errorhandler(413)
def large_upload(_error):
    return fail("Maximum audio upload is 10 MB.", 413)


init()
