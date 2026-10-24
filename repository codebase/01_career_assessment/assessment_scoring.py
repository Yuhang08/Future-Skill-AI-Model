
# =============================================
# FUTURESKILL AI
# ASSESSMENT SCORING SYSTEM
# =============================================

RIASEC = ["R", "I", "A", "S", "E", "C"]

SUBJECTS = [
    "IT",
    "Math",
    "Education",
    "Health",
    "Business",
    "Engineering"
]

SKILLS = [
    "MathSkill",
    "CodingSkill",
    "DataSkill",
    "CommunicationSkill",
    "LeadershipSkill",
    "CreativeSkill"
]


# =============================================
# 1. VALIDATE QUESTIONNAIRE ANSWERS
# =============================================

def validate_answers(answers, categories, count):

    if set(answers.keys()) != set(categories):
        raise ValueError(
            "Missing or unexpected categories"
        )

    for category in categories:

        values = answers[category]

        if len(values) != count:
            raise ValueError(
                f"{category} must have {count} answers"
            )

        for value in values:

            if type(value) is not int:
                raise ValueError(
                    "Answers must be integers"
                )

            if not 1 <= value <= 5:
                raise ValueError(
                    "Answers must be between 1 and 5"
                )


# =============================================
# 2. CALCULATE RIASEC SCORES
# =============================================

def calculate_riasec(answers):

    validate_answers(
        answers,
        RIASEC,
        count=4
    )

    scores = {}

    for dimension in RIASEC:

        total = sum(answers[dimension])

        # Maximum score = 4 x 5 = 20
        score = total / 20 * 100

        scores[dimension] = round(score, 2)

    return scores


# =============================================
# 3. IDENTIFY TOP 3 RIASEC TYPES
# =============================================

def get_top_three(scores):

    sorted_types = sorted(
        RIASEC,
        key=lambda d: scores[d],
        reverse=True
    )

    return "".join(sorted_types[:3])


# =============================================
# 4. CALCULATE SUBJECT PREFERENCES
# =============================================

def calculate_subject_preferences(answers):

    validate_answers(
        answers,
        SUBJECTS,
        count=2
    )

    preferences = {}

    for subject in SUBJECTS:

        total = sum(answers[subject])

        average = total / 2

        preferences[subject] = round(
            average, 2
        )

    return preferences


# =============================================
# 5. CALCULATE SKILLS SCORES
# =============================================

def calculate_skills(answers):

    validate_answers(
        {k: [v] for k, v in answers.items()},
        SKILLS,
        count=1
    )

    return answers.copy()


# =============================================
# 6. COMPLETE ASSESSMENT
# =============================================

def calculate_assessment(
    riasec_answers,
    subject_answers,
    skill_answers
):

    riasec_scores = calculate_riasec(
        riasec_answers
    )

    subject_scores = calculate_subject_preferences(
        subject_answers
    )

    skill_scores = calculate_skills(
        skill_answers
    )

    top_three = get_top_three(
        riasec_scores
    )

    return {
        "riasec_scores": riasec_scores,
        "riasec_top3": top_three,
        "subject_preferences": subject_scores,
        "skills": skill_scores
    }


# =============================================
# 7. DEMO USER ANSWERS
# =============================================

if __name__ == "__main__":

    riasec_answers = {
        "R": [2, 2, 2, 2],
        "I": [5, 5, 5, 5],
        "A": [3, 3, 3, 2],
        "S": [5, 5, 5, 5],
        "E": [5, 5, 5, 4],
        "C": [4, 4, 4, 5]
    }

    subject_answers = {
        "IT": [4, 5],
        "Math": [5, 5],
        "Education": [4, 5],
        "Health": [2, 2],
        "Business": [2, 3],
        "Engineering": [4, 5]
    }

    skill_answers = {
        "MathSkill": 5,
        "CodingSkill": 4,
        "DataSkill": 5,
        "CommunicationSkill": 5,
        "LeadershipSkill": 5,
        "CreativeSkill": 5
    }

    result = calculate_assessment(
        riasec_answers,
        subject_answers,
        skill_answers
    )

    print("\n===== FUTURESKILL AI RESULTS =====")

    print("\nRIASEC SCORES:")

    for dimension, score in result[
        "riasec_scores"
    ].items():
        print(f"{dimension}: {score}")

    print(
        "\nTop 3 RIASEC:",
        result["riasec_top3"]
    )

    print("\nSUBJECT PREFERENCES:")

    for subject, score in result[
        "subject_preferences"
    ].items():
        print(f"{subject}: {score}/5")

    print("\nSKILLS:")

    for skill, score in result[
        "skills"
    ].items():
        print(f"{skill}: {score}/5")
