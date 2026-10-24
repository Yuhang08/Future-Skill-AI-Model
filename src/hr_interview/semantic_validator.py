"""Question similarity checks; embeddings share the configured server-side client."""
import math
import os

from .interview_engine import client
from .question_policy import partition, exact_duplicate, word_duplicate


def embed(text):
    result = client().embeddings.create(
        model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
        input=text,
    )
    return result.data[0].embedding


def cosine(first, second):
    dot = sum(a * b for a, b in zip(first, second))
    first_norm = math.sqrt(sum(value * value for value in first))
    second_norm = math.sqrt(sum(value * value for value in second))
    return dot / (first_norm * second_norm) if first_norm and second_norm else 0.0


def check_question(candidate, history, session_questions, embed_lookup):
    """Apply the source feature's lexical and semantic duplicate thresholds."""
    old, recent = partition(history)
    if exact_duplicate(candidate, history + session_questions):
        return False, "Exact duplicate"
    if word_duplicate(candidate, recent + session_questions, 0.82):
        return False, "Very similar wording"
    vector = embed_lookup(candidate)
    for question in session_questions:
        if cosine(vector, embed_lookup(question)) >= 0.82:
            return False, "Similar within this interview"
    for question in recent:
        if cosine(vector, embed_lookup(question)) >= 0.86:
            return False, "Similar to recent personal history"
    return True, "Approved"
