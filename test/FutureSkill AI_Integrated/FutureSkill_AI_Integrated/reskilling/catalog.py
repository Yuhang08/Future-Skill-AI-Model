"""Illustrative skills catalog, not a verified labour-market forecast.

0..5 self-ratings are NOT verified competency assessments. Replace these
examples with properly sourced skills and validated proficiency benchmarks.
"""


def skill(required, importance, hours, objective, project, prerequisites=()):
    return {
        "required": required, "importance": importance,
        "hours_per_level": hours, "objective": objective,
        "project": project, "prerequisites": list(prerequisites),
    }


CAREERS = {
    "Data Analyst": {
        "description": "Turn data into clear, useful insights.",
        "skills": {
            "Excel": skill(3, 0.75, 3, "Clean a spreadsheet and use formulas and pivot tables", "Create an Excel summary dashboard"),
            "Python Basics": skill(3, 0.85, 5, "Use variables, loops, functions and CSV files", "Write a script that summarises a CSV file"),
            "SQL": skill(4, 1.0, 5, "Query and join tables with SELECT, JOIN and GROUP BY", "Answer five realistic questions with SQL"),
            "Statistics": skill(3, 0.95, 6, "Interpret averages, spread and basic relationships", "Analyse an anonymised survey dataset"),
            "Pandas": skill(3, 0.95, 6, "Load, filter, clean and group tabular datasets", "Prepare and explain a cleaned dataset", ["Python Basics"]),
            "Data Visualisation": skill(3, 0.90, 4, "Create and interpret appropriate data charts", "Build three charts and explain each insight", ["Pandas"]),
        }
    },
    "Software Developer": {
        "description": "Build practical, maintainable software.",
        "skills": {
            "Python Basics": skill(3, 0.95, 5, "Write functions, loops and clean Python code", "Build a command-line habit tracker"),
            "Git & GitHub": skill(3, 0.85, 3, "Commit changes and collaborate with Git", "Publish a small repository with a README"),
            "Algorithms": skill(3, 1.0, 7, "Solve problems with lists, dictionaries and searching", "Solve five small coding challenges", ["Python Basics"]),
            "Web Basics": skill(3, 0.9, 5, "Use HTML, CSS and JavaScript basics", "Build a responsive personal webpage"),
            "APIs": skill(3, 0.9, 6, "Design and consume JSON-based APIs", "Build a simple task-list API", ["Python Basics"]),
            "Testing": skill(3, 0.9, 5, "Write tests and understand debugging", "Add automated tests to a project", ["Python Basics"]),
        }
    },
    "Cybersecurity Analyst": {
        "description": "Understand systems and improve security practices.",
        "skills": {
            "Networking": skill(4, 1.0, 6, "Explain IP, DNS, ports and network layers", "Draw and describe a sample network"),
            "Operating Systems": skill(3, 0.9, 5, "Use basic operating-system and command-line tools", "Document safe system-inspection commands"),
            "Python Basics": skill(2, 0.75, 5, "Write scripts for simple automation", "Build a safe log-summary script"),
            "Security Fundamentals": skill(4, 1.0, 6, "Explain authentication, encryption and common risks", "Create a security awareness checklist", ["Networking"]),
            "Log Analysis": skill(3, 0.95, 5, "Interpret routine system and access logs", "Find patterns in a synthetic log file", ["Operating Systems"]),
            "Risk Communication": skill(3, 0.8, 4, "Explain technical risks and mitigations clearly", "Write a one-page security briefing", ["Security Fundamentals"]),
        }
    },
    "UI/UX Designer": {
        "description": "Create accessible, user-centred digital experiences.",
        "skills": {
            "User Research": skill(3, 0.95, 5, "Plan interviews and identify user needs", "Write a small user-research summary"),
            "Wireframing": skill(4, 1.0, 5, "Sketch user journeys and wireframes", "Design a five-screen user flow"),
            "Visual Design": skill(3, 0.9, 5, "Apply layout, typography and colour", "Redesign a simple landing page"),
            "Prototyping": skill(3, 0.95, 5, "Create and test clickable prototypes", "Build a clickable app prototype", ["Wireframing"]),
            "Accessibility": skill(3, 0.95, 4, "Apply basic inclusive-design principles", "Audit a mock interface for accessibility", ["Visual Design"]),
            "Usability Testing": skill(3, 0.95, 5, "Observe users and document usability issues", "Test a prototype and write an improvement plan", ["Prototyping"]),
        }
    },
    "Digital Marketing Specialist": {
        "description": "Plan campaigns and evaluate marketing performance.",
        "skills": {
            "Content Strategy": skill(3, 0.9, 5, "Identify an audience and map content objectives", "Create a one-month content calendar"),
            "Copywriting": skill(3, 0.85, 4, "Write clear and audience-aware marketing messages", "Draft five variations of a campaign message"),
            "SEO Basics": skill(3, 0.9, 5, "Explain search intent and page optimisation", "Improve a sample webpage content outline"),
            "Analytics": skill(4, 1.0, 6, "Interpret engagement and conversion measures", "Create a basic campaign performance report"),
            "Campaign Planning": skill(3, 0.9, 5, "Set campaign goals, audiences and milestones", "Plan a small responsible marketing campaign", ["Content Strategy"]),
            "Reporting": skill(3, 0.85, 4, "Communicate results with charts and recommendations", "Write a one-page campaign retrospective", ["Analytics"]),
        }
    },
}

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def public_catalog():
    return {
        name: {
            "description": role["description"],
            "skills": {
                key: {"required": value["required"], "importance": value["importance"]}
                for key, value in role["skills"].items()
            },
        }
        for name, role in CAREERS.items()
    }
