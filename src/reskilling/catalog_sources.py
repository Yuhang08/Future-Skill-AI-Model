"""Reviewed citation allowlist, not a database of validated job requirements.

Technical documentation supports learning topics only. Its presence must never
upgrade an illustrative catalogue target into an occupational benchmark.
"""

CATALOG_SOURCE_ID = "local-illustrative-catalog"

SOURCES = {
    CATALOG_SOURCE_ID: {
        "id": CATALOG_SOURCE_ID,
        "title": "FutureSkill illustrative reskilling catalogue",
        "kind": "illustrative_catalog",
        "local_path": "reskilling/catalog.py",
        "url": None,
        "accessed_on": None,
        "published_on": None,
        "supports": "Provenance of existing example targets, weights, hours, prerequisites, objectives and projects.",
        "limitations": [
            "Original authorship and evidence for numeric choices are not documented.",
            "Not an independently validated occupational requirement or proficiency standard.",
        ],
    },
    "python-tutorial-3.12": {
        "id": "python-tutorial-3.12",
        "title": "Python 3.12 documentation — The Python Tutorial",
        "kind": "technical_learning_reference",
        "local_path": None,
        "url": "https://docs.python.org/3.12/tutorial/",
        "accessed_on": "2026-10-22",
        "published_on": None,
        "supports": "Python foundations: variables, control flow, functions and data structures.",
        "limitations": [
            "Assumes some general programming knowledge; not a complete beginner curriculum.",
            "Does not establish career-specific targets, weights, hours or job demand.",
        ],
    },
    "postgresql-sql-tutorial-18": {
        "id": "postgresql-sql-tutorial-18",
        "title": "PostgreSQL 18 documentation — The SQL Language",
        "kind": "technical_learning_reference",
        "local_path": None,
        "url": "https://www.postgresql.org/docs/18/tutorial-sql.html",
        "accessed_on": "2026-10-22",
        "published_on": None,
        "supports": "SQL learning topics: querying tables, joins and aggregate functions.",
        "limitations": [
            "Examples use PostgreSQL; SQL dialects can differ.",
            "Does not establish career-specific targets, weights, hours or job demand.",
        ],
    },
    "pandas-intro-tutorials-2.3": {
        "id": "pandas-intro-tutorials-2.3",
        "title": "pandas 2.3 documentation — Getting started tutorials",
        "kind": "technical_learning_reference",
        "local_path": None,
        "url": "https://pandas.pydata.org/pandas-docs/version/2.3/getting_started/intro_tutorials/index.html",
        "accessed_on": "2026-10-22",
        "published_on": None,
        "supports": "Tabular-data input/output, filtering, summary statistics and combining tables.",
        "limitations": [
            "A technical reference, not a verified course or occupational standard.",
            "Does not establish career-specific targets, weights, hours or job demand.",
        ],
    },
}
