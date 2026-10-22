"""Transcribe browser audio with OpenAI; audio is not saved to disk."""
from io import BytesIO
from openai import OpenAI

ALLOWED = {"audio/webm": "webm", "audio/mp4": "mp4", "audio/ogg": "ogg", "audio/wav": "wav"}


def transcribe(upload):
    mime = upload.mimetype.split(";")[0].strip().lower()
    if mime not in ALLOWED:
        raise ValueError("Unsupported audio type. Use webm, mp4, ogg or wav.")
    data = upload.read()
    if not data or len(data) > 10 * 1024 * 1024:
        raise ValueError("Recording must be between 1 byte and 10 MB.")
    stream = BytesIO(data)
    stream.name = "answer." + ALLOWED[mime]
    result = OpenAI(timeout=45.0, max_retries=1).audio.transcriptions.create(
        model="gpt-4o-mini-transcribe", file=stream,
    )
    return result.text
