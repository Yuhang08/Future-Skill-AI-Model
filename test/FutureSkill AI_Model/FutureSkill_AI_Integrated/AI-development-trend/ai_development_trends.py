
"""
FutureSkill AI
AI Development Trend Analysis: 2021-2030

Historical: 2021-2025
Future scenarios: 2026-2030
Career impact + key drivers

Uses Python standard library only.
"""

import csv
import json


# ============================================
# 1. HISTORICAL AI DATA
# ============================================

# Percentage of survey respondents reporting
# organizational AI use in at least one
# business function.
#
# Source: Stanford AI Index Report 2026,
# Figure 4.3.1 (McKinsey survey data).
#
# Survey estimates, not a census.

AI_ADOPTION = {
    2021: 56,
    2022: 50,
    2023: 55,
    2024: 78,
    2025: 88
}

# Generative AI adoption:
# Same source, but a different AI category.
GENAI_ADOPTION = {
    2023: 33,
    2024: 71,
    2025: 79
}

SOURCE = (
    "Stanford AI Index Report 2026, "
    "Figure 4.3.1; McKinsey Global AI Surveys"
)


# ============================================
# 2. FIVE MAJOR DRIVERS
# ============================================

AI_DRIVERS = [
    {
        "id": "technology",
        "name": "Technological Breakthroughs",
        "description": (
            "Advances in generative AI, foundation "
            "models, reasoning and multimodal systems."
        ),
        "historical_impact": (
            "Expanded AI capabilities beyond "
            "traditional prediction."
        ),
        "future_impact": (
            "May support increasingly complex "
            "AI assistants and agents."
        )
    },
    {
        "id": "computing",
        "name": "Computing Infrastructure",
        "description": (
            "Growth of GPUs, cloud computing "
            "and AI data centers."
        ),
        "historical_impact": (
            "Enabled larger models and "
            "wider AI deployment."
        ),
        "future_impact": (
            "Capacity, energy use and computing "
            "costs may influence AI expansion."
        )
    },
    {
        "id": "investment",
        "name": "AI Investment",
        "description": (
            "Funding for research, AI products "
            "and supporting infrastructure."
        ),
        "historical_impact": (
            "Supported faster commercialization "
            "of AI technologies."
        ),
        "future_impact": (
            "Investment may accelerate innovation, "
            "depending on economic conditions."
        )
    },
    {
        "id": "productivity",
        "name": "Productivity Demand",
        "description": (
            "Business demand for automation, "
            "efficiency and better decisions."
        ),
        "historical_impact": (
            "Encouraged enterprise AI adoption."
        ),
        "future_impact": (
            "May accelerate AI integration "
            "into business workflows."
        )
    },
    {
        "id": "accessibility",
        "name": "AI Accessibility",
        "description": (
            "Easy-to-use applications, APIs, "
            "open models and cloud services."
        ),
        "historical_impact": (
            "Made AI accessible to more users "
            "and organizations."
        ),
        "future_impact": (
            "May increase adoption among "
            "smaller organizations."
        )
    }
]


# ============================================
# 3. HISTORICAL EVENTS
# ============================================

HISTORICAL_EVENTS = {
    2021: {
        "stage": "Predictive AI Expansion",
        "change": (
            "AI used in analytics, prediction "
            "and recommendation systems."
        ),
        "drivers": [
            "computing",
            "productivity"
        ]
    },
    2022: {
        "stage": "Generative AI Breakthrough",
        "change": (
            "Public launch of ChatGPT increased "
            "attention toward generative AI."
        ),
        "drivers": [
            "technology",
            "accessibility"
        ]
    },
    2023: {
        "stage": "Generative AI Expansion",
        "change": (
            "Text, image and code generation "
            "became more widely accessible."
        ),
        "drivers": [
            "technology",
            "investment",
            "accessibility"
        ]
    },
    2024: {
        "stage": "Enterprise AI Integration",
        "change": (
            "More organizations reported "
            "using AI in business functions."
        ),
        "drivers": [
            "productivity",
            "investment",
            "computing"
        ]
    },
    2025: {
        "stage": "AI Agents and Automation",
        "change": (
            "Organizations explored AI agents "
            "and increasingly integrated AI "
            "into business workflows."
        ),
        "drivers": [
            "technology",
            "productivity",
            "accessibility"
        ]
    }
}


# ============================================
# 4. HISTORICAL TREND ANALYSIS
# ============================================

def calculate_historical_trends():

    results = []
    previous_rate = None

    for year, rate in AI_ADOPTION.items():

        if previous_rate is None:
            annual_change = None
        else:
            annual_change = round(
                rate - previous_rate, 2
            )

        event = HISTORICAL_EVENTS[year]

        results.append({
            "year": year,
            "ai_adoption_percent": rate,
            "genai_adoption_percent":
                GENAI_ADOPTION.get(year),
            "annual_change_percentage_points":
                annual_change,
            "stage": event["stage"],
            "main_change": event["change"],
            "drivers": event["drivers"],
            "data_type": "historical_survey"
        })

        previous_rate = rate

    total_change = (
        AI_ADOPTION[2025] - AI_ADOPTION[2021]
    )

    return {
        "period": "2021-2025",
        "source": SOURCE,
        "total_change_percentage_points":
            total_change,
        "annual_data": results,
        "note": (
            "Survey samples and methods may differ "
            "across years. These data do not "
            "establish causation."
        )
    }


# ============================================
# 5. FUTURE ADOPTION SCENARIOS
# ============================================

# IMPORTANT:
# These are hypothetical 2030 targets.
# NOT real forecasts or official predictions.
#
# Values can be adjusted when stronger
# forecasting evidence becomes available.

SCENARIO_TARGETS = {
    "conservative": 90,
    "baseline": 95,
    "optimistic": 98
}


def forecast_ai_adoption(
    scenario="baseline",
    target_year=2030
):
    if scenario not in SCENARIO_TARGETS:
        raise ValueError(
            "Choose conservative, baseline "
            "or optimistic."
        )

    if not 2026 <= target_year <= 2030:
        raise ValueError(
            "Target year must be 2026-2030."
        )

    base_year = 2025
    base_adoption = AI_ADOPTION[base_year]

    final_target = SCENARIO_TARGETS[scenario]

    results = []

    for year in range(2026, target_year + 1):

        # Normalized time: 0 to 1
        t = (year - base_year) / 5

        # Smooth saturation curve
        progress = 1 - (1 - t) ** 2

        predicted_rate = (
            base_adoption
            + (final_target - base_adoption)
            * progress
        )

        results.append({
            "year": year,
            "ai_adoption_percent": round(
                min(100, predicted_rate), 2
            ),
            "scenario": scenario,
            "data_type": "hypothetical_scenario"
        })

    return results


def compare_scenarios():

    return {
        scenario: forecast_ai_adoption(scenario)
        for scenario in SCENARIO_TARGETS
    }


# ============================================
# 6. FUTURE TECHNOLOGY ROADMAP
# ============================================

FUTURE_ROADMAP = [
    {
        "year": 2026,
        "trend": "AI Assistants and Agents",
        "change": (
            "More tools support multi-step tasks."
        ),
        "reason": (
            "Advances in tool use and demand "
            "for productivity."
        ),
        "impact": (
            "More AI-assisted administrative "
            "and digital work."
        )
    },
    {
        "year": 2027,
        "trend": "Workflow Automation",
        "change": (
            "Potential wider automation of "
            "repetitive business processes."
        ),
        "reason": (
            "Organizations seek efficiency "
            "and scalable AI deployment."
        ),
        "impact": (
            "Greater need for workflow design "
            "and AI quality assurance."
        )
    },
    {
        "year": 2028,
        "trend": "Industry-Specific AI",
        "change": (
            "Potential growth in specialized "
            "AI for finance, health and education."
        ),
        "reason": (
            "Demand for specialized knowledge "
            "and reliable applications."
        ),
        "impact": (
            "Domain experts may increasingly "
            "work alongside AI."
        )
    },
    {
        "year": 2029,
        "trend": "Human-AI Collaboration",
        "change": (
            "Potential growth of supervised "
            "AI-supported workflows."
        ),
        "reason": (
            "Need for human judgment, "
            "oversight and accountability."
        ),
        "impact": (
            "More emphasis on critical thinking "
            "and AI evaluation."
        )
    },
    {
        "year": 2030,
        "trend": "AI-Integrated Workplaces",
        "change": (
            "AI may be embedded in more "
            "everyday enterprise applications."
        ),
        "reason": (
            "Maturing AI technology and "
            "ongoing digital transformation."
        ),
        "impact": (
            "AI literacy may become important "
            "in a wider range of occupations."
        )
    }
]


# ============================================
# 7. CAREER IMPACT ANALYSIS
# ============================================

# Qualitative outlooks informed by WEF 2025.
# These are NOT numerical growth predictions.
# Automation exposure does not imply job loss.

CAREER_IMPACTS = {
    "AI Engineer": {
        "outlook": "Potential Growth",
        "ai_impact": (
            "AI adoption may create more demand "
            "for development and integration."
        ),
        "opportunities": [
            "AI model development",
            "AI application engineering"
        ],
        "risks": [
            "Rapid skill obsolescence",
            "High demand for continuous learning"
        ],
        "future_skills": [
            "Python",
            "Machine Learning",
            "Mathematics",
            "MLOps"
        ],
        "related_drivers": [
            "technology", "investment"
        ]
    },
    "Data Scientist": {
        "outlook": "Potential Growth",
        "ai_impact": (
            "Routine analysis may be assisted "
            "by AI while advanced analytical "
            "judgment remains important."
        ),
        "opportunities": [
            "Predictive analytics",
            "AI evaluation"
        ],
        "risks": [
            "Automation of routine reporting"
        ],
        "future_skills": [
            "Statistics",
            "Python",
            "SQL",
            "Machine Learning"
        ],
        "related_drivers": [
            "technology", "productivity"
        ]
    },
    "Software Developer": {
        "outlook": "Changing and Growing",
        "ai_impact": (
            "AI may automate parts of coding "
            "while increasing emphasis on "
            "architecture and testing."
        ),
        "opportunities": [
            "AI integration",
            "System architecture"
        ],
        "risks": [
            "Automation of routine coding tasks"
        ],
        "future_skills": [
            "Programming",
            "System Design",
            "Testing",
            "AI Tools"
        ],
        "related_drivers": [
            "technology", "productivity"
        ]
    },
    "Cybersecurity Analyst": {
        "outlook": "Potential Growth",
        "ai_impact": (
            "AI can support threat detection "
            "but also introduce new security risks."
        ),
        "opportunities": [
            "AI security",
            "Threat detection"
        ],
        "risks": [
            "AI-enabled cyber threats"
        ],
        "future_skills": [
            "Cybersecurity",
            "AI Security",
            "Risk Analysis"
        ],
        "related_drivers": [
            "technology", "computing"
        ]
    },
    "Administrative Clerk": {
        "outlook": "Automation Pressure",
        "ai_impact": (
            "Routine document processing "
            "and data tasks may be automated."
        ),
        "opportunities": [
            "Workflow coordination",
            "Digital administration"
        ],
        "risks": [
            "Reduced demand for repetitive tasks"
        ],
        "future_skills": [
            "Digital Literacy",
            "Communication",
            "Workflow Management"
        ],
        "related_drivers": [
            "productivity", "accessibility"
        ]
    },
    "Teacher": {
        "outlook": "Role Transformation",
        "ai_impact": (
            "AI may assist lesson preparation "
            "and personalized learning."
        ),
        "opportunities": [
            "AI-assisted education",
            "Personalized teaching"
        ],
        "risks": [
            "Inaccurate AI-generated materials"
        ],
        "future_skills": [
            "Teaching",
            "AI Literacy",
            "Critical Thinking"
        ],
        "related_drivers": [
            "technology", "accessibility"
        ]
    },
    "Healthcare Professional": {
        "outlook": "Role Transformation",
        "ai_impact": (
            "AI may support clinical analysis "
            "and administrative workflows, "
            "with professional oversight."
        ),
        "opportunities": [
            "AI-assisted care",
            "Healthcare analytics"
        ],
        "risks": [
            "Privacy and reliability concerns"
        ],
        "future_skills": [
            "Clinical Expertise",
            "AI Literacy",
            "Ethics",
            "Communication"
        ],
        "related_drivers": [
            "technology", "investment"
        ]
    }
}


def analyze_career_impact(career_name):

    for career, details in CAREER_IMPACTS.items():
        if career.lower() == career_name.lower():

            return {
                "career": career,
                **details,
                "analysis_type":
                    "qualitative_scenario",
                "note": (
                    "Not a numerical employment "
                    "forecast or proven causal effect."
                )
            }

    return {
        "career": career_name,
        "outlook": "Insufficient Evidence",
        "note": (
            "Career-specific impact data "
            "not yet available."
        )
    }


# ============================================
# 8. COMBINED WEBSITE API
# ============================================

def get_ai_trend_report():

    return {
        "project": "FutureSkill AI",
        "historical_trends":
            calculate_historical_trends(),
        "major_drivers": AI_DRIVERS,
        "future_scenarios":
            compare_scenarios(),
        "future_roadmap": FUTURE_ROADMAP,
        "career_impacts": [
            analyze_career_impact(name)
            for name in CAREER_IMPACTS
        ],
        "sources": [
            SOURCE,
            "WEF Future of Jobs Report 2025"
        ],
        "limitations": [
            "Historical data are survey estimates.",
            "Future percentages are scenario assumptions.",
            "Future roadmap is hypothetical.",
            "Career impacts are qualitative.",
            "Drivers are not proven causal rankings."
        ]
    }


# ============================================
# 9. EXPORT JSON AND CSV
# ============================================

def export_report():

    report = get_ai_trend_report()

    with open(
            "ai_trend_report.json",
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            report,
            file,
            indent=2,
            ensure_ascii=False
        )

    with open(
            "ai_trend_table.csv",
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "Year",
            "Historical AI Adoption (%)",
            "Conservative Scenario (%)",
            "Baseline Scenario (%)",
            "Optimistic Scenario (%)",
            "Main Development"
        ])

        historical = {
            item["year"]: item
            for item in report[
                "historical_trends"
            ]["annual_data"]
        }

        scenarios = {}

        for name, rows in (
            report["future_scenarios"].items()
        ):
            scenarios[name] = {
                item["year"]:
                    item["ai_adoption_percent"]
                for item in rows
            }

        roadmap = {
            item["year"]: item["trend"]
            for item in FUTURE_ROADMAP
        }

        for year in range(2021, 2031):

            past = historical.get(year)

            writer.writerow([
                year,
                (
                    past["ai_adoption_percent"]
                    if past else ""
                ),
                scenarios["conservative"].get(
                    year, ""
                ),
                scenarios["baseline"].get(
                    year, ""
                ),
                scenarios["optimistic"].get(
                    year, ""
                ),
                (
                    past["stage"]
                    if past
                    else roadmap.get(year, "")
                )
            ])

    return report


# ============================================
# 10. RUN THE PROGRAM
# ============================================

if __name__ == "__main__":

    report = export_report()

    print("=== FUTURESKILL AI TREND REPORT ===")

    print("\nHistorical AI Adoption:")

    for item in report[
        "historical_trends"
    ]["annual_data"]:
        print(
            item["year"],
            str(item["ai_adoption_percent"]) + "%"
        )

    print("\nFuture AI Scenarios (2030):")

    for name, values in (
        report["future_scenarios"].items()
    ):
        print(
            name,
            str(values[-1][
                "ai_adoption_percent"
            ]) + "%"
        )

    print("\nExample Career Impact:")

    print(json.dumps(
        analyze_career_impact("Data Scientist"),
        indent=2
    ))

    print("\nFiles created:")
    print("- ai_trend_report.json")
    print("- ai_trend_table.csv")