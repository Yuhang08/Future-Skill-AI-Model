"""Conservative duplicate checks over prior personal interview questions."""
import re
from difflib import SequenceMatcher


def norm(text):
    return " ".join(re.findall(r"\w+", text.casefold()))


def lexical(first, second):
    return SequenceMatcher(None, norm(first), norm(second)).ratio()


def partition(personal_questions):
    if len(personal_questions) < 150:
        return [], personal_questions
    return personal_questions[:-100], personal_questions[-100:]


def exact_duplicate(candidate, previous):
    return any(norm(candidate) == norm(question) for question in previous)


def word_duplicate(candidate, previous, threshold=0.82):
    return any(lexical(candidate, question) >= threshold for question in previous)
