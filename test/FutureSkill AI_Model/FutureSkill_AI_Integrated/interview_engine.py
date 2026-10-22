"""LLM question and feedback engine. All score ranges are coaching heuristics."""
import json
import os
import re
from difflib import SequenceMatcher
from openai import OpenAI

MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
_client = None


def client():
    global _client
    if _client is None:
        _client = OpenAI(timeout=40.0, max_retries=1)
    return _client


def llm_json(instructions, payload):
    response = client().responses.create(
        model=MODEL,
        instructions=instructions + "\nReturn only a valid JSON object, no markdown fences.",
        input=json.dumps(payload, ensure_ascii=False),
        text={"format": {"type": "json_object"}},
        max_output_tokens=1100,
        store=False,
    )
    return json.loads(response.output_text)


def initial_question(role, mode, language):
    result = llm_json(
        "You are a supportive and professional mock interviewer. Create one realistic first interview question "
        "for the specified career and mode. Do not ask for sensitive personal details. "
        'Return JSON {"question":"...","focus":"..."}. Use the requested language.',
        {"role": role, "mode": mode, "language": language},
    )
    return {"question": str(result["question"])[:600], "focus": str(result.get("focus", "General communication"))[:200]}


def feedback_for(question, answer, role, mode, language):
    result = llm_json(
        "Evaluate the *content* of a mock interview answer as a coach. Avoid assessing accent, appearance, "
        "identity or suitability for employment. Do not pretend a simulated score predicts hiring. "
        "Do not invent the candidate's experiences. Evaluate using these coaching dimensions scored 0-100: "
        "relevance, clarity, evidence, depth, language. Language means understandable wording, not accent. "
        "If the response is too brief to assess, give low evidence/depth scores and explain gently. "
        "Scores are subjective practice heuristics, not scientific measurements. "
        'Return JSON with fields "scores" (an object with keys relevance,clarity,evidence,depth,language and integer values), '
        '"strengths" (array of 1-3 short strings), "improvements" (array of 2-3 actionable strings), '
        '"example_answer" (a clearly fictional illustrative sample answer), "summary" (one sentence). '
        "Use the requested language for human-readable feedback.",
        {"question": question, "answer": answer, "role": role, "mode": mode, "language": language},
    )
    names = ("relevance", "clarity", "evidence", "depth", "language")
    scores = {}
    for key in names:
        try:
            scores[key] = max(0, min(100, int(result.get("scores", {}).get(key, 0))))
        except (TypeError, ValueError):
            scores[key] = 0
    total = round(sum(scores[k] * w for k, w in zip(names, (0.30, 0.25, 0.20, 0.15, 0.10))), 1)
    return {
        "scores": scores,
        "total": total,
        "strengths": [str(x)[:300] for x in result.get("strengths", [])[:3]],
        "improvements": [str(x)[:350] for x in result.get("improvements", [])[:3]],
        "example_answer": str(result.get("example_answer", ""))[:1600],
        "summary": str(result.get("summary", ""))[:500],
    }


def _normalize_question(text):
    """Normalize wording for a conservative duplicate check."""
    return " ".join(re.findall(r"[\w]+", text.casefold(), flags=re.UNICODE))


def _too_similar(candidate, previous):
    a = _normalize_question(candidate)
    if not a:
        return True
    for old in previous:
        b = _normalize_question(old)
        if a == b or SequenceMatcher(None, a, b).ratio() >= 0.82:
            return True
        wa, wb = set(a.split()), set(b.split())
        if len(wa) >= 5 and len(wb) >= 5 and len(wa & wb) / len(wa | wb) >= 0.80:
            return True
    return False


def adaptive_plan(history):
    """Rule-based learning focus; not a measure of hiring potential."""
    last = history[-1]["feedback"]
    dimensions = last["scores"]
    overall = float(last["total"])
    weakest = min(dimensions, key=dimensions.get)
    if overall >= 80 and min(dimensions.values()) >= 60:
        return {"difficulty": "challenge", "focus": "go deeper with a new scenario", "weakest": weakest}
    if overall < 60:
        return {"difficulty": "scaffold", "focus": f"ask an accessible specific follow-up targeting {weakest}", "weakest": weakest}
    return {"difficulty": "standard", "focus": f"practice {weakest} using a fresh question", "weakest": weakest}


def next_question(role, mode, language, history):
    # Include all prior questions to minimize repeats throughout the session.
    prior_questions = [item["question"] for item in history]
    compact = [
        {"question": x["question"], "answer": x["answer"][:650],
         "feedback_summary": x["feedback"]["summary"]}
        for x in history[-3:]
    ]
    plan = adaptive_plan(history)
    instructions = (
        "You are a supportive mock HR interviewer. Return exactly ONE distinct question in JSON "
        'with keys "question" and "focus". Respect the requested language and interview mode. '
        "Do not ask for sensitive attributes. Avoid repeating topics and questions on the prior list. "
        "For 'challenge', ask a more demanding but reasonable scenario question. "
        "For 'scaffold', ask a concise supportive clarifying question; do not overwhelm the learner. "
        "For 'standard', ask a fresh question that helps practice the listed skill. "
        "Do not equate practice scores with eligibility for employment."
    )
    payload = {"role": role, "mode": mode, "language": language,
               "history": compact, "all_previous_questions": prior_questions,
               "adaptive_plan": plan}
    for attempt in range(3):
        payload["retry_instruction"] = (
            "The last candidate question was too similar. Choose a clearly different skill or scenario."
            if attempt else ""
        )
        result = llm_json(instructions, payload)
        question = str(result.get("question", "")).strip()[:600]
        if question and not _too_similar(question, prior_questions):
            return {"question": question, "focus": str(result.get("focus", plan["focus"]))[:200],
                    "difficulty": plan["difficulty"]}
    # Avoid silently returning a repeated question; let API present a retry message.
    raise ValueError("Could not generate a sufficiently distinct interview question")


DIMENSION_LABELS = {
    "relevance": {"English": "Answer relevance", "中文": "回答切题度"},
    "clarity": {"English": "Communication clarity", "中文": "表达清晰度"},
    "evidence": {"English": "Examples and evidence", "中文": "举例与证据"},
    "depth": {"English": "Depth of explanation", "中文": "回答深度"},
    "language": {"English": "Understandable wording", "中文": "用词易懂程度"},
}


def report(history, role, language="English"):
    """Summarize practice evidence; never predict hiring or personal worth."""
    if not history:
        raise ValueError("No answers to summarize")
    lang = language if language in ("English", "中文") else "English"
    keys = tuple(DIMENSION_LABELS)
    averages = {k: round(sum(x["feedback"]["scores"][k] for x in history) / len(history), 1) for k in keys}
    overall = round(sum(x["feedback"]["total"] for x in history) / len(history), 1)
    high = sorted(keys, key=lambda k: (-averages[k], k))[:2]
    low = sorted(keys, key=lambda k: (averages[k], k))[:2]
    proficiency = []
    for key in keys:
        value = averages[key]
        level = ("Developing" if value < 60 else "Practicing" if value < 80 else "Strong in this practice")
        if lang == "中文":
            level = ("基础加强" if value < 60 else "持续练习" if value < 80 else "本次练习表现良好")
        proficiency.append({"key": key, "label": DIMENSION_LABELS[key][lang], "score": value, "level": level})
    # These thresholds are product heuristics, not scientific or employer standards.
    enough = len(history) >= 3
    minimum = min(averages.values())
    if not enough:
        state = "insufficient_evidence"
    elif overall >= 80 and minimum >= 65:
        state = "try_real_interviews"
    elif overall >= 60:
        state = "practice_and_apply"
    else:
        state = "focus_practice_first"
    chinese = lang == "中文"
    messages = {
        "insufficient_evidence": ("已完成题目较少，建议至少练习 3 题再查看较完整的准备度。" if chinese else "Only a few answers are available. Try at least 3 questions for a more useful practice summary."),
        "try_real_interviews": ("可以考虑尝试真实面试，并继续练习薄弱环节。" if chinese else "Consider trying real interviews while continuing to practice your weaker areas."),
        "practice_and_apply": ("可以边申请边练习，优先改善分数较低的能力。" if chinese else "You can practice and apply in parallel, prioritizing weaker answer skills."),
        "focus_practice_first": ("建议先进行几轮针对性练习，再重新模拟面试；这不代表你不能申请职位。" if chinese else "Consider a few focused practice sessions before another mock interview; this does not mean you cannot apply."),
    }
    strengths = [{"dimension": DIMENSION_LABELS[k][lang], "score": averages[k],
                  "example": next((str(i["feedback"]["strengths"][0]) for i in history
                      if i["feedback"].get("strengths") and i["feedback"]["scores"][k] >= averages[k]), "")}
                 for k in high]
    improvements = [{"dimension": DIMENSION_LABELS[k][lang], "score": averages[k],
                     "action": ("用 STAR 结构回答，并补充你亲自做了什么及结果。" if chinese else
                                "Use a specific STAR example: situation, task, your action and result.") if k == "evidence" else
                               ("先直接回答问题，再解释原因并举一个具体例子。" if chinese else
                                "Answer the question first, then explain why and give a concrete example.")}
                    for k in low]
    return {
        "role": role,
        "questions_completed": len(history),
        "overall": overall,
        "average_dimensions": averages,
        "proficiency": proficiency,
        "strengths_summary": strengths,
        "weaknesses_summary": improvements,
        "readiness": {"status": state, "message": messages[state],
                      "evidence_count": len(history), "is_preliminary": not enough},
        "practice_priorities": low,
        "history": history,
        "disclaimer": ("这些是 AI 对本次回答的主观练习估计，不是职业胜任力认证或录取预测。" if chinese else
                       "These are subjective AI estimates of practice answers, not a skills certification or hiring prediction."),
    }
