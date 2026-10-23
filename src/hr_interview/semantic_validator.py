"""Semantic duplicate checks using stored vectors. Missing vectors are embedded once."""
import math
import os
from openai import OpenAI
from .question_policy import partition,exact_duplicate,word_duplicate

def embed(text):
    result = OpenAI().embeddings.create(
        model=os.getenv('EMBEDDING_MODEL','text-embedding-3-small'), input=text)
    return result.data[0].embedding

def cosine(a,b):
    x=sum(v*w for v,w in zip(a,b))
    na=math.sqrt(sum(v*v for v in a)); nb=math.sqrt(sum(v*v for v in b))
    return x/(na*nb) if na and nb else 0.0

def check_question(candidate, history, session_questions, embed_lookup):
    """history list of question strings, oldest-first; embed_lookup(question) caches embeddings.
    Thresholds experimental, need calibration on real question pairs.
    """
    old, recent = partition(history)
    if exact_duplicate(candidate, history+session_questions):
        return False, 'Exact duplicate'
    if word_duplicate(candidate, recent+session_questions, 0.82):
        return False, 'Very similar wording'
    vec = embed_lookup(candidate)
    for q in session_questions:
        if cosine(vec,embed_lookup(q)) >= 0.82:
            return False, 'Similar within this interview'
    for q in recent:
        if cosine(vec,embed_lookup(q)) >= 0.86:
            return False, 'Similar to recent personal history'
    return True, 'Approved'
