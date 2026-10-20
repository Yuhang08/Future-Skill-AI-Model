
RIASEC = {
    "R": {
        "name": "Realistic (实际型)",
        "questions": [
            "I enjoy repairing machines.",
            "I enjoy working with tools.",
            "I enjoy building physical objects.",
            "I enjoy practical hands-on tasks.",
            "I enjoy operating equipment.",
            "I enjoy working outdoors.",
            "I enjoy assembling things.",
            "I enjoy solving practical problems."
        ]
    },
    "I": {
        "name": "Investigative (研究型)",
        "questions": [
            "I enjoy analysing data.",
            "I enjoy solving complex problems.",
            "I enjoy investigating scientific questions.",
            "I enjoy understanding how things work.",
            "I enjoy using logic to solve problems.",
            "I enjoy conducting experiments.",
            "I enjoy researching new information.",
            "I enjoy identifying patterns in data."
        ]
    },
    "A": {
        "name": "Artistic (艺术型)",
        "questions": [
            "I enjoy creating artwork.",
            "I enjoy writing creatively.",
            "I enjoy designing new things.",
            "I enjoy expressing original ideas.",
            "I enjoy exploring different forms of art.",
            "I enjoy creating visual content.",
            "I enjoy thinking of imaginative solutions.",
            "I enjoy doing creative projects."
        ]
    },
    "S": {
        "name": "Social (社会型)",
        "questions": [
            "I enjoy helping other people.",
            "I enjoy teaching others.",
            "I enjoy listening to people's problems.",
            "I enjoy working in a team.",
            "I enjoy explaining ideas to others.",
            "I enjoy supporting people who need help.",
            "I enjoy guiding others in learning.",
            "I enjoy cooperating with others."
        ]
    },
    "E": {
        "name": "Enterprising (企业型)",
        "questions": [
            "I enjoy leading a team.",
            "I enjoy persuading others.",
            "I enjoy presenting my ideas.",
            "I enjoy organising projects.",
            "I enjoy making decisions.",
            "I enjoy starting new initiatives.",
            "I enjoy negotiating with others.",
            "I enjoy working towards ambitious goals."
        ]
    },
    "C": {
        "name": "Conventional (常规型)",
        "questions": [
            "I enjoy organising records.",
            "I enjoy checking details carefully.",
            "I enjoy following clear procedures.",
            "I enjoy arranging schedules.",
            "I enjoy maintaining accurate information.",
            "I enjoy organising files and documents.",
            "I enjoy working with structured data.",
            "I enjoy keeping information consistent."
        ]
    }
}


def collect_answers():
    """Ask the customer all 48 questions."""

    answers = {}

    print("=" * 55)
    print("       FUTURESKILL AI - RIASEC QUESTIONNAIRE")
    print("=" * 55)
    print("\nRate each statement from 1 to 5:")
    print("1 = Strongly disagree")
    print("2 = Disagree")
    print("3 = Neutral")
    print("4 = Agree")
    print("5 = Strongly agree")

    for element, details in RIASEC.items():
        answers[element] = []

        print(f"\n--- {details['name']} ---")

        for number, question in enumerate(
            details["questions"], start=1
        ):
            while True:
                try:
                    score = int(input(
                        f"Question {number}/8: {question}\n"
                        "Your answer (1-5): "
                    ))

                    if 1 <= score <= 5:
                        answers[element].append(score)
                        break

                    print("Please enter a number from 1 to 5.")

                except ValueError:
                    print("Invalid input. Please enter 1, 2, 3, 4, or 5.")

    return answers


def calculate_riasec(answers):
    """Calculate each element using the user's formula."""

    scores = {}

    for element in RIASEC:
        total = sum(answers[element])

        # Maximum score = 5 * 8 = 40
        scores[element] = total / (5 * 8) * 100

    return scores


def main():
    answers = collect_answers()
    scores = calculate_riasec(answers)

    print("\n" + "=" * 55)
    print("YOUR RIASEC RESULTS")
    print("=" * 55)

    for element, score in scores.items():
        print(f"{element} - {RIASEC[element]['name']}: {score:.1f}%")

    top_three = sorted(
        scores,
        key=scores.get,
        reverse=True
    )[:3]

    print("\nYour top 3 interest types:")
    for element in top_three:
        print(f"{element} - {RIASEC[element]['name']}")

    print("\nThese results describe your stated interests,")
    print("not a guarantee of career success.")


if __name__ == "__main__":
    main()
