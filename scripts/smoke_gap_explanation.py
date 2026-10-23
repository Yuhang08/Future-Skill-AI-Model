"""One explicitly authorized, synthetic service/provider smoke call.

Run from repository root:
PYTHONPATH=src python -B -m scripts.smoke_gap_explanation --confirm-real-call
Does not import the web app, create profiles, modify storage or print model text.
"""
import argparse
import asyncio
import json

from reskilling.catalog import CAREERS
from reskilling.explanation_provider import ExplanationFailure, MODEL
from reskilling.explanation_service import GapExplanationService


async def smoke():
    profile = {
        "target_career": "Data Analyst",
        "skills": {
            name: (2 if name == "SQL" else detail["required"])
            for name, detail in CAREERS["Data Analyst"]["skills"].items()
        },
    }
    try:
        result = await GapExplanationService().explain(profile, "synthetic-smoke")
    except ExplanationFailure as error:
        skipped = error.code in ("missing_credentials", "provider_configuration")
        print(json.dumps({
            "status": "skipped" if skipped else "failed",
            "code": error.code, "provider": "openai", "model": MODEL,
        }))
        return 2 if skipped else 1
    print(json.dumps({
        "status": "real_provider_smoke_passed", "provider": "openai", "model": MODEL,
        "skills_checked": len(result.gaps),
        "numerical_fields_unchanged": True,
        "citation_scope_validated": True,
        "semantic_grounding_independently_verified": False,
    }))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confirm-real-call", action="store_true")
    args = parser.parse_args()
    if not args.confirm_real_call:
        print(json.dumps({"status": "skipped", "code": "real_call_not_authorized"}))
        return 2
    return asyncio.run(smoke())


if __name__ == "__main__":
    raise SystemExit(main())
