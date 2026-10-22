"""Rule: <150 strict all; >=150 strict recent 100, exact older; strict session always."""
import re
from difflib import SequenceMatcher

def norm(text):
    return ' '.join(re.findall(r'\w+', text.casefold()))

def lexical(a,b):
    return SequenceMatcher(None,norm(a),norm(b)).ratio()

def partition(personal_questions):
    if len(personal_questions) < 150:
        return [], personal_questions
    return personal_questions[:-100], personal_questions[-100:]

def exact_duplicate(candidate, previous):
    return any(norm(candidate)==norm(x) for x in previous)

def word_duplicate(candidate, previous, threshold=0.82):
    return any(lexical(candidate,x)>=threshold for x in previous)
