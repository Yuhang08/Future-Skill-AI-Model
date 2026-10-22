"""Explainable personalised reskilling recommender and scheduling algorithm.

The model is rule-based, not a trained machine-learning model. Hours and
requirements are illustrative assumptions. Task completion measures planned
practice, not verified mastery.
"""

import math
from datetime import date, timedelta
from .catalog import CAREERS, DAYS

WEEKLY_LEARNING_SHARE = 0.80
EPS = 1e-7


class InputError(ValueError):
    pass


def validate_profile(raw):
    if not isinstance(raw, dict):
        raise InputError("Please submit the questionnaire as a JSON object.")
    career = raw.get("target_career")
    if career not in CAREERS:
        raise InputError("Please choose an available target career.")

    try:
        hours = float(raw.get("weekly_hours"))
        weeks = int(raw.get("target_weeks"))
    except (TypeError, ValueError, OverflowError):
        raise InputError("Enter valid study hours and the number of weeks.") from None
    if not (1 <= hours <= 40 and math.isfinite(hours)):
        raise InputError("Weekly hours must be between 1 and 40.")
    if not (1 <= weeks <= 52):
        raise InputError("Choose a plan duration between 1 and 52 weeks.")

    preferred_days = raw.get("preferred_days")
    if (not isinstance(preferred_days, list) or not preferred_days or
            any(day not in DAYS for day in preferred_days) or
            len(set(preferred_days)) != len(preferred_days)):
        raise InputError("Choose at least one valid study day, without duplicates.")

    skill_levels = raw.get("skills")
    if not isinstance(skill_levels, dict):
        raise InputError("Please rate your current skills.")
    clean_skills = {}
    for name in CAREERS[career]["skills"]:
        value = skill_levels.get(name)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not (0 <= value <= 5):
            raise InputError(f"Rate {name} from 0 to 5.")
        clean_skills[name] = float(value)

    user_type = raw.get("user_type", "student")
    if user_type not in ("student", "employed", "career_changer", "returning"):
        raise InputError("Select a valid current situation.")
    learning_style = raw.get("learning_style", "project")
    if learning_style not in ("project", "video", "reading"):
        raise InputError("Select a learning preference.")
    experience = raw.get("experience", "beginner")
    if experience not in ("beginner", "some", "experienced"):
        raise InputError("Select a valid experience level.")

    def short_string(value, limit):
        if not isinstance(value, str):
            return ""
        return value.strip()[:limit]

    return {
        "user_type": user_type,
        "current_industry": short_string(raw.get("current_industry", ""), 80),
        "experience": experience,
        "target_career": career,
        "personal_goal": short_string(raw.get("personal_goal", ""), 200),
        "skills": clean_skills,
        "weekly_hours": round(hours, 2),
        "target_weeks": weeks,
        "preferred_days": sorted(preferred_days, key=DAYS.index),
        "learning_style": learning_style,
    }


def skill_gaps(profile):
    role = CAREERS[profile["target_career"]]["skills"]
    gaps = {}
    for name, detail in role.items():
        current = profile["skills"][name]
        required = detail["required"]
        gap = max(0, required - current)
        # Neutral factor 1.0: no invented occupation/skills trend forecasting.
        score = gap / 5 * detail["importance"]
        gaps[name] = {
            "current": current, "required": required, "gap": gap,
            "importance": detail["importance"], "priority": round(score, 3),
            "estimated_hours": round(gap * detail["hours_per_level"], 2),
            "objective": detail["objective"], "project": detail["project"],
            "prerequisites": detail["prerequisites"],
        }
    return gaps


def _activity(style, experience, project):
    intro = "Start with a guided example; " if experience == "beginner" else "Try a quick diagnostic; "
    if style == "video":
        return intro + "watch a lesson, practise, then work toward: " + project
    if style == "reading":
        return intro + "read a guide, practise, then work toward: " + project
    return intro + "build a small part of: " + project


def generate_schedule(profile, completed_hours=None, start_day=None):
    """Create finite tasks in up to target_weeks, preserving completed practice.

    A prerequisite is scheduled before dependent skills. Completion credit is
    only deducted from the remaining *practice-hour* estimate; skills are never
    automatically marked mastered after task completion.
    """
    if completed_hours is None:
        completed_hours = {}
    if start_day is None:
        start_day = date.today()
    elif isinstance(start_day, str):
        start_day = date.fromisoformat(start_day)
    catalog = CAREERS[profile["target_career"]]["skills"]
    gaps = skill_gaps(profile)
    remaining = {
        s: max(0., gaps[s]["estimated_hours"] - max(0., float(completed_hours.get(s, 0))))
        for s in gaps
    }
    original_remaining = sum(remaining.values())
    weekly_hours = profile["weekly_hours"]
    day_count = len(profile["preferred_days"])
    per_day = weekly_hours * WEEKLY_LEARNING_SHARE / day_count
    review_per_day = weekly_hours * (1 - WEEKLY_LEARNING_SHARE) / day_count
    projected_weeks = math.ceil(original_remaining / (weekly_hours * WEEKLY_LEARNING_SHARE)) if original_remaining else 0
    tasks = []
    week_summaries = []

    for week in range(1, profile["target_weeks"] + 1):
        dates = []
        for day_name in profile["preferred_days"]:
            offset = (DAYS.index(day_name) - start_day.weekday()) % 7
            session_date = start_day + timedelta(days=offset + 7 * (week - 1))
            dates.append((session_date, day_name))
        dates.sort()
        count = 0
        for on_day, day_name in dates:
            left = per_day
            had_learning = False
            while left > EPS:
                eligible = [
                    name for name, detail in catalog.items()
                    if remaining[name] > EPS
                    and all(remaining.get(p, 0) < EPS for p in detail["prerequisites"])
                ]
                if not eligible:
                    break
                skill = max(eligible, key=lambda s: (gaps[s]["priority"], -list(catalog).index(s)))
                duration = min(2.0, left, remaining[skill])
                if duration < EPS:
                    break
                remaining[skill] -= duration
                left -= duration
                count += 1
                had_learning = True
                tasks.append({
                    "week_index": week,
                    "day": day_name,
                    "due_date": on_day.isoformat(),
                    "skill": skill,
                    "hours": round(duration, 2),
                    "objective": catalog[skill]["objective"],
                    "activity": _activity(profile["learning_style"], profile["experience"], catalog[skill]["project"]),
                    "kind": "learning",
                })
            if had_learning:
                count += 1
                tasks.append({
                    "week_index": week, "day": day_name,
                    "due_date": on_day.isoformat(), "skill": "Review & reflect",
                    "hours": round(review_per_day, 2),
                    "objective": "Review what you practised and note one question for next time.",
                    "activity": "Use this session as flexible revision or catch-up time.",
                    "kind": "review",
                })
        if count:
            week_summaries.append({"week": week, "task_count": count})
        if all(v < EPS for v in remaining.values()):
            break

    scheduled_learning_hours = round(sum(x["hours"] for x in tasks if x["kind"] == "learning"), 2)
    outstanding = {name: round(hrs, 2) for name, hrs in remaining.items() if hrs >= 0.01}
    total_estimate = round(sum(item["estimated_hours"] for item in gaps.values()), 2)
    if not total_estimate:
        note = "Your self-ratings currently meet the example requirements. Try a project or skill verification next."
    elif outstanding:
        note = "Your selected timeline covers part of the estimated practice time. Extend the plan if you want to schedule all remaining practice."
    else:
        note = "The estimated practice hours fit within your selected timeframe. Practical assessments are still needed to verify mastery."
    return {
        "gaps": gaps,
        "estimated_total_hours": total_estimate,
        "remaining_before_plan": round(original_remaining, 2),
        "estimated_weeks_remaining": projected_weeks,
        "scheduled_learning_hours": scheduled_learning_hours,
        "remaining_after_plan": outstanding,
        "message": note,
        "tasks": tasks,
        "weeks": week_summaries,
    }


def tree_details(points):
    stages = [
        (0, "Seed", "🌰", "You have planted the first seed. Starting matters."),
        (10, "Sprout", "🌱", "Your learning is taking root."),
        (35, "Seedling", "🪴", "Your consistent practice is helping this grow."),
        (80, "Young tree", "🌳", "You've built a growing collection of learning wins."),
        (150, "Thriving tree", "🌲", "Your learning garden is flourishing."),
        (250, "Learning forest", "🌳🌳", "Look at the collection of projects and practice you have built!"),
    ]
    current = stages[0]
    for stage in stages:
        if points >= stage[0]:
            current = stage
    next_stage = next((stage for stage in stages if stage[0] > points), None)
    return {
        "name": current[1], "emoji": current[2], "message": current[3],
        "points": points, "next_points": next_stage[0] if next_stage else None,
        "next_name": next_stage[1] if next_stage else None,
    }


def points_for_task(task):
    return max(2, round(float(task["hours"]) * 4)) if task["kind"] == "review" else max(3, round(float(task["hours"]) * 10))


def feedback_for_completion(done_count, kind, tree_now, tree_before):
    if tree_now["name"] != tree_before["name"]:
        return f"🌱 New growth: {tree_now['name']}! Your completed practice helped your learning tree grow."
    if kind == "review":
        return "A review session completed! Reflection is part of learning, too. 🌿"
    if done_count == 1:
        return "Your first task is complete! One practical step at a time. 🌱"
    return f"Nice progress — {done_count} learning tasks completed. Your tree grows with each completed step. 🌿"
