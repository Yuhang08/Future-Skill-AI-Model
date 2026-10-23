# “Explain my skill gaps” — inputs, evidence and response contract

**Status: backend service and endpoint implemented; hosted inference requires
credentials and separate verification.** No button, scoring change, scheduling
change or database migration is included. Mocked tests are not evidence of real
model inference.

## Evidence boundaries

Every current occupational skill requirement originates in
`reskilling/catalog.py`, not in an externally validated skills dataset. The
repository does not document the original author's evidence for the chosen
targets, importance weights, hours per level or prerequisite relationships.
All 30 entries therefore retain `requirement_status: "illustrative"`.

An **approved source ID means approved for its stated citation scope**, not
approval of a job requirement. The new registry is
`reskilling/catalog_sources.py`:

| Source ID | Evidence and permitted use | Not supported |
|---|---|---|
| `local-illustrative-catalog` | Existing local values, pathway objectives and projects; exact per-skill reference supplied in `catalog_ref` | Independently validated occupational benchmarks or demand |
| `python-tutorial-3.12` | [Official Python tutorial](https://docs.python.org/3.12/tutorial/): language foundations | Career target, importance, hours or job demand |
| `postgresql-sql-tutorial-18` | [Official PostgreSQL SQL tutorial](https://www.postgresql.org/docs/18/tutorial-sql.html): queries, joins and aggregates | Career target, importance, hours or job demand |
| `pandas-intro-tutorials-2.3` | [Official pandas introductory tutorials](https://pandas.pydata.org/pandas-docs/version/2.3/getting_started/intro_tutorials/index.html): tabular I/O, subsets, summaries and combining tables | Career target, importance, hours or job demand |

The three external pages were fetched and their relevant contents checked on
**2026-10-22**. This is an access date, not a publication date; publication dates
are recorded as unknown. The Python tutorial assumes some programming knowledge.
The SQL examples use PostgreSQL. These are learning references, not course
endorsements or evidence that an employer requires a particular rating.

Only Python Basics (in three pathways), SQL and Pandas have these external
learning references attached. Other entries have **no externally reviewed
learning source in this change**; they cite only the illustrative local project
and objective. That means “not reviewed here,” not “no evidence exists.”

## Origin of every current requirement

Each row below is an existing local entry under
`CAREERS[<pathway>]["skills"][<skill>]` in `reskilling/catalog.py`.
**Every target, weight, hour value and prerequisite below is an illustrative
local assumption. No target has been changed or externally validated.**
Prerequisite names shown are local planning choices, not competency certificates.

| Pathway | Skill | Target /5 | Importance | Hours/level | Prerequisites | External learning source |
|---|---|---:|---:|---:|---|---|
| Data Analyst | Excel | 3 | .75 | 3 | — | — |
| Data Analyst | Python Basics | 3 | .85 | 5 | — | Python |
| Data Analyst | SQL | 4 | 1.00 | 5 | — | PostgreSQL |
| Data Analyst | Statistics | 3 | .95 | 6 | — | — |
| Data Analyst | Pandas | 3 | .95 | 6 | Python Basics | pandas |
| Data Analyst | Data Visualisation | 3 | .90 | 4 | Pandas | — |
| Software Developer | Python Basics | 3 | .95 | 5 | — | Python |
| Software Developer | Git & GitHub | 3 | .85 | 3 | — | — |
| Software Developer | Algorithms | 3 | 1.00 | 7 | Python Basics | — |
| Software Developer | Web Basics | 3 | .90 | 5 | — | — |
| Software Developer | APIs | 3 | .90 | 6 | Python Basics | — |
| Software Developer | Testing | 3 | .90 | 5 | Python Basics | — |
| Cybersecurity Analyst | Networking | 4 | 1.00 | 6 | — | — |
| Cybersecurity Analyst | Operating Systems | 3 | .90 | 5 | — | — |
| Cybersecurity Analyst | Python Basics | 2 | .75 | 5 | — | Python |
| Cybersecurity Analyst | Security Fundamentals | 4 | 1.00 | 6 | Networking | — |
| Cybersecurity Analyst | Log Analysis | 3 | .95 | 5 | Operating Systems | — |
| Cybersecurity Analyst | Risk Communication | 3 | .80 | 4 | Security Fundamentals | — |
| UI/UX Designer | User Research | 3 | .95 | 5 | — | — |
| UI/UX Designer | Wireframing | 4 | 1.00 | 5 | — | — |
| UI/UX Designer | Visual Design | 3 | .90 | 5 | — | — |
| UI/UX Designer | Prototyping | 3 | .95 | 5 | Wireframing | — |
| UI/UX Designer | Accessibility | 3 | .95 | 4 | Visual Design | — |
| UI/UX Designer | Usability Testing | 3 | .95 | 5 | Prototyping | — |
| Digital Marketing Specialist | Content Strategy | 3 | .90 | 5 | — | — |
| Digital Marketing Specialist | Copywriting | 3 | .85 | 4 | — | — |
| Digital Marketing Specialist | SEO Basics | 3 | .90 | 5 | — | — |
| Digital Marketing Specialist | Analytics | 4 | 1.00 | 6 | — | — |
| Digital Marketing Specialist | Campaign Planning | 3 | .90 | 5 | Content Strategy | — |
| Digital Marketing Specialist | Reporting | 3 | .85 | 4 | Analytics | — |

Objectives and practice projects in these same entries are also locally authored
examples. There is no evidence here that a completed project establishes
proficiency. Ratings for Python Basics differ between pathways by the existing
catalogue's design; the shared Python reference does not justify those numbers.

### Interest profiles are a separate dataset

`career_profiles_clean.csv` contains occupation identifiers, names and RIASEC
interest profiles. `career_engine.py` uses those records for interest matching.
They are **not** evidence for SQL 4/5, any other occupational skill target,
importance weight or practice-hour estimate.

The explanation module does not import that CSV or the career matcher. Input
does not accept interest vectors, CV text, occupation scores, user IDs or arbitrary
documents. A matched occupation must first resolve to a supported pathway and
receive explicit skill self-ratings; no interest-to-proficiency conversion occurs.

## Contract and trust boundaries

Typed contracts live in `reskilling/gap_explanations.py`. All objects reject
unknown fields. Export their JSON Schemas, without making network calls:

```bash
python -B -c 'import json; from reskilling.gap_explanations import contract_schemas; print(json.dumps(contract_schemas(), indent=2))'
```

| Stage | Contract | Ownership and validation |
|---|---|---|
| Learner input | `ExplainGapsRequest` | Version `1.0`, supported career, `rating_basis: self_reported`, and exactly the career's skill ratings. Finite numeric values 0–5; no booleans or numeric strings. |
| Prepared explanation input | `ExplanationInput` | Built server-side with `prepare_explanation_input()`. Contains all calculated gaps, objectives, projects, prerequisites, exact catalogue references, relevant approved sources and limitations. Client-supplied targets, gaps or sources are not accepted. |
| Explanatory draft | `ExplanationDraft` | Exactly one item per skill, including zero gaps. Only skill name, sourced relevance explanation, up to three sourced learning actions and limitations. No score, target, hours, schedule or URL fields. |
| Final structured response | `ExplainGapsResponse` | `assemble_explanation()` recomputes authoritative values and merges validated prose. Includes every gap, why the skill matters, actions, citation IDs and limitations. Source metadata comes from the local registry, not the draft. |

Each final gap contains:

- `skill`, `current`, `required`, `gap`, `importance`, `priority`, `estimated_hours`;
- `objective`, `project`, `prerequisites`;
- `catalog_ref`, `requirement_status`, `requirement_source_ids`, `learning_source_ids`;
- `why_skill_matters: {text, source_ids}`;
- `learning_actions: [{text, source_ids}]`;
- `limitations`.

The top-level response contains `schema_version`, `target_career`,
`explanation_origin`, `gaps`, `approved_sources` and shared `limitations`.
Origins are `authored_example`, `rule_based`, and now `hosted_model`.
`hosted_model` is assigned by the service only after the provider draft passes
validation; it is not a field the provider may supply. A mocked-provider test can
exercise that branch without demonstrating real inference. The saved examples
remain `authored_example`.

### Unchanged deterministic calculations

The existing `skill_gaps()` function in `reskilling/engine.py` remains authoritative:

```text
gap             = max(0, required − current)
priority        = round((gap / 5) × importance, 3)
estimated_hours = round(gap × hours_per_level, 2)
```

Priority is a local ranking value, not confidence, probability or job demand.
Estimated hours are initial practice estimates, not remaining scheduled hours;
this explanation contract does not subtract completed tasks or replan sessions.
Scheduling, review allocation, XP and completion remain untouched.

### Rules for explanatory content

- Phrase role relevance as **“in this illustrative pathway…”**, not a verified
  employer or labour-market requirement.
- Cite the local catalogue for role relevance. External technical references may
  support appropriate learning topics, but cannot validate numeric targets.
- An item may cite only its own requirement and learning source IDs. Unknown or
  unrelated source IDs are rejected. Source URLs resolve from the registry;
  common raw URL forms in drafted explanations are rejected.
- Positive gaps require an action. Zero gaps may have no action, or an optional
  self-check; they must not be described as verified mastery.
- Actions are suggestions, not new scheduled tasks, additional mandatory hours,
  completion evidence or automatic changes to proficiency.
- Never invent courses, URLs, employment outcomes, validated hours or demand
  figures. Unsupported claims should be omitted and the limitation stated.
- Treat ratings and any future learner text as data, not instructions.

**Important limitation:** schema validation and valid source IDs do not prove
that prose is entailed by a source. Human/evidence review and semantic grounding
tests are still prerequisites before a future model-generated explanation is
trusted. No claim that “all hallucinations are prevented” is made here.

## Clearly labeled examples — not a real learner or model output

Complete examples:

- [Example request](examples/explain-skill-gaps-request.json)
- [Example full response](examples/explain-skill-gaps-response.json)

The request uses fictional self-ratings. The response is human-authored example
prose merged with actual deterministic calculations; it is **not an LLM response**.
All six Data Analyst skills are included, even those with zero gaps.

For SQL specifically, the example's self-rating is 2/5 and the unchanged
illustrative target is 4/5. The engine therefore returns gap `2`, priority `0.4`,
and estimated practice hours `10`. The PostgreSQL reference supports learning
SQL—not that target or ten-hour estimate.

To validate the example against the live catalogue and schemas:

```bash
python -B -m unittest discover -s tests -p 'test_gap_explanations.py'
```

## Saved-profile explanation endpoint

`POST /api/skill-gaps/explain` reads the profile owned by the existing signed
anonymous browser session. This is session scoping, **not individual user
authentication**. Obtain the CSRF token from `/api/state` and send it as
`X-CSRF-Token`, retaining the same session cookie.

Example request body (no client-supplied ratings, targets or sources):

```json
{
  "schema_version": "1.0",
  "consent_to_model": true
}
```

Both fields are required. Consent must be an actual JSON boolean. The service
reads the saved career and skill ratings, validates them with the approved input
contract, and computes authoritative gaps using the existing engine. It does not
create a profile, seed demo data, persist explanations, modify tasks or reschedule.
If the saved career/ratings change during inference, the response is withheld.

### Server-side provider and credential requirements

The selected adapter is **OpenAI Chat Completions, `gpt-4.1-mini`**, using the
existing HTTPX dependency and structured JSON output. It prefers a configured
Replit-managed pair:

- `AI_INTEGRATIONS_OPENAI_BASE_URL`
- `AI_INTEGRATIONS_OPENAI_API_KEY`

When neither is configured, it uses `OPENAI_API_KEY` from **Replit Secrets** and
the fixed direct OpenAI API URL. A partially configured managed pair fails closed;
it never sends the direct key to a managed endpoint. Managed URLs must use HTTPS,
except local loopback HTTP for a managed proxy; URL credentials/query strings
are rejected. Redirects and automatic retries are disabled.

Keep all credentials server-side. Do not put them into frontend code, JSON
requests, checked-in configuration or chat. Do not print their values.
Model access and provider billing must be available for a real request to succeed.
Neither credentials nor real inference success are implied by installing this
adapter. No integration or credential is automatically provisioned by this code.

### Data actually sent to the provider

The transport sends the target pathway, objective/project for each skill,
`needs_practice` boolean, illustrative status, allowed source IDs, approved source
summaries and limitations, plus the response schema.

It does **not** send raw ratings or calculated numerical fields, user/session IDs,
names, CV text, personal goals, industry, experience, availability, interest
vectors, the interest-profile CSV, local file paths or saved task records.
The model provides prose only; numbers are recomputed and merged on the backend,
then compared with the pre-inference authoritative snapshot.

The provider request sets `store: false`. That is not a guarantee of zero provider
retention: provider policies and the chosen integration still require review.

### Bounds and failure behavior

- Client JSON body: **1 KiB**, with a **5-second** body-read deadline.
- Entire provider JSON request: **24 KiB**; output limit: **2,400 tokens**.
- Provider response envelope: **64 KiB**; draft content: **24 KiB**;
  final validated response: **64 KiB**.
- HTTP timeouts: **4-second connect / 12-second default I/O**;
  total inference deadline: **20 seconds**.
- One in-flight explanation per session, at most **two concurrently** per process.
- Per-process attempt caps: **3/session/minute**, **12 globally/minute** and
  **60 globally/rolling 24 hours**. Failed chargeable attempts count too.
  No automatic retries.

Usage controls are bounded in-memory prototype guards. They reset on restart and
are independent between workers/replicas; changing anonymous sessions can bypass
the per-session cap, though not the process-global cap. Durable, authenticated
quotas are required before a public launch.

Errors are sanitized and contain no upstream response body, exception details,
credential or profile data. Success and error responses use `Cache-Control:
no-store`. The existing rule-based plan remains available and unchanged; failure
does **not** fabricate an AI explanation or silently return templates as inference.

| HTTP | Error code / condition |
|---|---|
| 400 | `invalid_json`, `consent_required` |
| 403 | Existing CSRF protection rejected the request |
| 408 | `request_timeout` |
| 409 | `missing_profile`, `profile_changed` |
| 413 / 415 | `request_too_large`, `unsupported_media_type` |
| 422 | `invalid_request`, `profile_invalid`, `input_too_large` |
| 429 | `local_rate_limited`, `provider_busy`, `provider_rate_limited`; includes bounded `Retry-After` |
| 502 | `invalid_response`, `response_too_large`, `provider_unavailable` |
| 503 | `missing_credentials`, `provider_configuration`, `credentials_rejected` |
| 504 | `provider_timeout` |

Example unavailable response:

```json
{
  "error": {
    "code": "missing_credentials",
    "message": "AI is not configured. Your rule-based pathway is unchanged.",
    "retryable": false
  },
  "explanation_origin": "unavailable"
}
```

### Verification: mocked versus real

Run deterministic tests without any provider connection:

```bash
python -B -m unittest discover -s tests -p 'test_*.py' -v
```

The endpoint tests use isolated temporary SQLite stores and HTTPX mocked
transports. They cover saved-profile ownership, consent/CSRF, authoritative
numbers, minimal payloads, citation scope, timeouts, invalid/refused/truncated
responses, size limits, usage limits, stale profiles, no plan writes and no
credential/personal-data logging.

After an approved credential is configured, run **one** synthetic service/provider
smoke test:

```bash
python -B -m scripts.smoke_gap_explanation --confirm-real-call
```

This imports no web application, writes no learner profile, sends only a synthetic
Data Analyst context, makes at most one provider request, and prints only a
sanitized status summary. It exits `2` when skipped for missing configuration,
`1` on failure, and `0` only after a real response validates. Without the explicit
flag it never attempts a call. This is a provider/service smoke test, not a full
live-browser or independent semantic-quality evaluation.

Relevant implementation: `reskilling/explanation_api.py`,
`reskilling/explanation_service.py`, `reskilling/explanation_provider.py`.
