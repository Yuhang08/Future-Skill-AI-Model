
import csv
import json

# ========================================
# FUTURESKILL AI
# CAREER CATEGORY TREND MODEL
# ========================================

# Historical labels = qualitative analysis
# Future labels = directional scenarios
# Not measured employment growth rates

CAREER_DATA = [
    {
        "category": "AI & Data Science",
        "past": "Growing",
        "future": "Strong Growth",
        "drivers": [
            "AI adoption",
            "Big data demand",
            "Digital transformation"
        ],
        "impact": "More demand for AI and data skills",
        "skills": [
            "Python", "Machine Learning",
            "Statistics", "Data Analysis"
        ],
        "examples": [
            "AI Engineer", "Data Scientist"
        ]
    },
    {
        "category": "Software & IT",
        "past": "Growing",
        "future": "Growing",
        "drivers": [
            "Digital transformation",
            "AI-assisted development",
            "Cloud computing"
        ],
        "impact": "Routine coding changes; system skills grow",
        "skills": [
            "Programming", "Cloud",
            "System Design", "AI Tools"
        ],
        "examples": [
            "Software Developer", "Cloud Engineer"
        ]
    },
    {
        "category": "Cybersecurity",
        "past": "Growing",
        "future": "Strong Growth",
        "drivers": [
            "Cyber threats",
            "Data protection",
            "AI security risks"
        ],
        "impact": "Greater demand for security expertise",
        "skills": [
            "Cybersecurity", "Networking",
            "Risk Analysis", "AI Security"
        ],
        "examples": [
            "Security Analyst", "Security Engineer"
        ]
    },
    {
        "category": "Healthcare",
        "past": "Growing",
        "future": "Growing",
        "drivers": [
            "Population ageing",
            "Healthcare demand",
            "Medical technology"
        ],
        "impact": "More care demand and AI-assisted tasks",
        "skills": [
            "Clinical Knowledge",
            "Communication", "AI Literacy"
        ],
        "examples": [
            "Nurse", "Healthcare Specialist"
        ]
    },
    {
        "category": "Education",
        "past": "Transforming",
        "future": "Growing",
        "drivers": [
            "Education demand",
            "Digital learning",
            "AI-assisted teaching"
        ],
        "impact": "Teaching roles increasingly use AI",
        "skills": [
            "Teaching", "Digital Literacy",
            "Critical Thinking"
        ],
        "examples": [
            "Teacher", "Education Specialist"
        ]
    },
    {
        "category": "Engineering & Green Energy",
        "past": "Growing",
        "future": "Strong Growth",
        "drivers": [
            "Green transition",
            "Renewable energy investment",
            "Infrastructure demand"
        ],
        "impact": "More opportunities in energy engineering",
        "skills": [
            "Engineering", "Sustainability",
            "Energy Systems"
        ],
        "examples": [
            "Environmental Engineer",
            "Renewable Energy Engineer"
        ]
    },
    {
        "category": "Business & Finance",
        "past": "Transforming",
        "future": "Mixed",
        "drivers": [
            "Fintech innovation",
            "Process automation",
            "Economic change"
        ],
        "impact": "Routine finance tasks change",
        "skills": [
            "Financial Analysis", "Fintech",
            "Risk Management"
        ],
        "examples": [
            "Financial Analyst", "Bank Teller"
        ]
    },
    {
        "category": "Sales & Customer Service",
        "past": "Transforming",
        "future": "Mixed",
        "drivers": [
            "E-commerce",
            "AI customer service",
            "Consumer demand"
        ],
        "impact": "Routine service tasks become automated",
        "skills": [
            "Communication",
            "Digital Marketing", "CRM"
        ],
        "examples": [
            "Salesperson", "Customer Service Agent"
        ]
    },
    {
        "category": "Manufacturing & Logistics",
        "past": "Transforming",
        "future": "Mixed",
        "drivers": [
            "Robotics",
            "Supply chain restructuring",
            "Delivery demand"
        ],
        "impact": "Some routine tasks automated",
        "skills": [
            "Automation", "Logistics",
            "Technical Maintenance"
        ],
        "examples": [
            "Factory Worker", "Delivery Driver"
        ]
    },
    {
        "category": "Administrative & Clerical",
        "past": "Automation Pressure",
        "future": "Declining",
        "drivers": [
            "AI automation",
            "Digital documents",
            "Workflow software"
        ],
        "impact": "Lower demand for repetitive clerical tasks",
        "skills": [
            "Digital Tools", "Coordination",
            "Communication"
        ],
        "examples": [
            "Data Entry Clerk",
            "Administrative Assistant"
        ]
    }
]


# ========================================
# 1. CLASSIFICATION
# ========================================

# Scores are labels only.
# They are NOT growth percentages.

TREND_SCORE = {
    "Strong Growth": 2,
    "Growing": 1,
    "Mixed": 0,
    "Declining": -1
}


def classify_direction(category):
    future = category["future"]

    if future == "Strong Growth":
        return "Increase"

    if future == "Growing":
        return "Increase"

    if future == "Declining":
        return "Decrease"

    return "Mixed / Uncertain"


# ========================================
# 2. FUTURE SCENARIO MODEL
# ========================================

def forecast_category(category_name):

    for item in CAREER_DATA:

        if item["category"].lower() == category_name.lower():

            future = item["future"]

            return {
                "category": item["category"],
                "historical_period": "2021-2025",
                "historical_trend": item["past"],
                "forecast_period": "2026-2030",
                "future_trend": future,
                "direction": classify_direction(item),
                "scenario_score": TREND_SCORE[future],
                "major_drivers": item["drivers"],
                "employment_impact": item["impact"],
                "future_skills": item["skills"],
                "example_careers": item["examples"],
                "model_type": "rule_based_scenario",
                "forecast_is_quantitative": False
            }

    return {
        "error": "Career category not found"
    }


# ========================================
# 3. ALL CATEGORY REPORTS
# ========================================

def analyze_all_categories():

    return [
        forecast_category(item["category"])
        for item in CAREER_DATA
    ]


# ========================================
# 4. FILTER GROWING / DECLINING
# ========================================

def get_growing_categories():

    return [
        item
        for item in analyze_all_categories()
        if item["direction"] == "Increase"
    ]


def get_declining_categories():

    return [
        item
        for item in analyze_all_categories()
        if item["direction"] == "Decrease"
    ]


def get_mixed_categories():

    return [
        item
        for item in analyze_all_categories()
        if item["direction"] == "Mixed / Uncertain"
    ]


# ========================================
# 5. WEBSITE API FUNCTION
# ========================================

def get_career_trend_report():

    return {
        "project": "FutureSkill AI",
        "historical_period": "2021-2025",
        "forecast_period": "2026-2030",
        "model_type": "Rule-based Scenario",
        "geographic_scope": "Global",
        "categories": analyze_all_categories(),
        "sources": [
            "WEF Future of Jobs Report 2025"
        ],
        "limitations": [
            "Historical labels are qualitative",
            "Future outcomes are scenario estimates",
            "No annual employment counts supplied",
            "Country-specific results may differ"
        ]
    }


# ========================================
# 6. EXPORT CSV AND JSON
# ========================================

def export_report():

    report = get_career_trend_report()

    with open(
        "career_category_trends.json",
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
        "career_category_trends.csv",
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "Career Category",
            "Historical Trend 2021-2025",
            "Future Trend 2026-2030",
            "Increase or Decrease",
            "Reasons",
            "Impact",
            "Future Skills"
        ])

        for item in report["categories"]:

            writer.writerow([
                item["category"],
                item["historical_trend"],
                item["future_trend"],
                item["direction"],
                "; ".join(item["major_drivers"]),
                item["employment_impact"],
                "; ".join(item["future_skills"])
            ])

    return report


# ========================================
# 7. RUN
# ========================================

if __name__ == "__main__":

    report = export_report()

    print("\nFUTURESKILL AI CAREER TREND")
    print("=" * 50)

    for item in report["categories"]:

        print("\nCareer:", item["category"])
        print("Past:", item["historical_trend"])
        print("Future:", item["future_trend"])
        print("Direction:", item["direction"])
        print(
            "Reasons:",
            ", ".join(item["major_drivers"])
        )

    print("\nFiles generated:")
    print("career_category_trends.json")
    print("career_category_trends.csv")
