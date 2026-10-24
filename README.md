# Future-Skill-AI-Model

> Future-Skill-AI-Model is an AI-powered partner system that enables users to freely input their datasets, whereby the built in AI shall predict which skills and jobs will emerge or decline, matches today’s workforce and tomorrow’s talent to the right future roles, and generates personalised reskilling pathways, while showing how each role and skill connects to the 17 UN Sustainable Development Goals.

---

## Team Information

| Field                  | Details                                     |
| ---------------------- | ------------------------------------------- |
| **Team Name**          | Francium Fluoride                           |
| **Team Domain**        | Domain 1                                    |
| **SDG Track (1–17)**   | SDG 4 — Quality education                   |
| **Team Leader**        | Chew Yu Hang                                |
| **University**         | Xiamen University Malaysia                  |
| **Number of Members**  | 3                                           |

## Links

| Resource          | Link                                           |
| ----------------- | ---------------------------------------------- |
| GitHub Repository | (https://github.com/Yuhang08/Future-Skill-AI-Model)  |
| Replit Project    | (https://replit.com/@tehyy623/Future-Skill-AI-Model) |
| Live Demo         | (https://future-skill-ai-model.onrender.com/)              |
| RunPod Endpoint   | None                                           |
| Slide Deck        | (https://www.canva.com/design/DAHY8lPJIu0/R1r_axxx3azZZKLuGaVGMw/edit)                    |
| Demo Video        | https://youtu.be/KTG0OxX6Ty0                 |

---

## Overview

## Problem

Fresh graduates may face challenges when transitioning from education into employment, particularly when they must determine how their existing knowledge, skills, and experience align with the requirements of a specific career role. Although they may have developed relevant capabilities through coursework, projects, internships, or other experiences, translating these capabilities into the terminology and expectations used in job descriptions can be difficult. They may also be uncertain about which missing skills are most important, which transferable skills they already possess, and where to begin improving their employability.

These decisions can become more complicated when job requirements, career information, and learning resources are scattered across different sources, making it difficult to compare expectations and identify suitable learning steps systematically. Without a structured way to connect their current capabilities with role-specific requirements, users may struggle to prioritise their development efforts.

This project investigates whether comparing a user's stated skills with documented career requirements can help fresh graduates understand their skill gaps, make more informed career decisions, and identify practical next steps. This remains a hypothesis to validate rather than a claim that all fresh graduates experience the same difficulties.

---

## Solution

FutureSkill AI will develop a prototype that helps fresh graduates translate their existing capabilities into a structured, role-specific reskilling plan. Users will be able to:

1. **Build a skill profile** by entering skills manually or submitting a CV through a tested workflow.
2. **Review and correct** skills extracted from their profile.
3. **Select a target career** from a curated set of roles with sourced skill requirements.
4. **Identify skill gaps** by comparing their reviewed profile with the selected role's requirements.
5. **Generate a prioritised reskilling roadmap** with explanations and relevant learning resources.
6. **Explore SDG connections** where a defensible relationship between the role and a relevant target exists.

### How AI contributes

AI will assist with extracting and standardising skills from unstructured CVs or experience descriptions, interpreting related terminology and transferable skills, and generating contextual explanations. Transparent matching rules and documented role requirements will distinguish existing matches, potential gaps, and uncertain results.

Using identified gaps, existing capabilities, preferred learning time, and verified learning resources, AI will help organise relevant learning steps into a personalised roadmap. Recommendations should explain which gap each step addresses; time estimates will be provided only when sufficiently supported.

For career-to-SDG explanations, AI will work within predefined target information and supporting evidence rather than generating unrestricted claims. Optional labour-market summaries may be introduced if time and reliable, dated data permit, clearly separating observed trends, published projections, and speculative scenarios.

### Implementation principle

FutureSkill AI adopts a **hybrid approach**: AI interprets unstructured information and generates contextual explanations, while curated data and transparent rules anchor role requirements, gap classifications, learning resources, and SDG mappings. This supports traceability and helps reduce unsupported recommendations. The platform is intended to support career planning and learning decisions, not guarantee employment or replace professional career advice.

---

### Key Features

F1. Curated Skills and Job Dataset: A small, sourced set of target roles and their stated skill requirements.

F2. Personal Skill Profile: Manual skill entry or a tested CV-input flow with user review.

F3. Skill Gap Analysis: Transparent comparison of the user's stated skills with the selected role's requirements.

F4. Personalised Reskilling Roadmap: Prioritised learning steps and relevant resources based on the identified gaps.

F5. Explainable Recommendations: A clear explanation of the criteria behind each gap and recommendation.

F6. Relevant SDG Mapping: A short, justified mapping to relevant SDG targets where appropriate.

### Tech Stack

| Layer           | Technology                   |
| --------------- | ---------------------------- |
| Frontend        | HTML, CSS, JavaScript        |
| Backend         | Python, FastAPI; Flask for the interview module|
| Database        | SQLite                       |
| AI / Compute    | OpenAI API — GPT-4.1 mini, with optional embedding and audio-transcription models|
| Hosting         | Render                       |
| Development     | Replit, PyCharm              |
| Version control | GitHub                       |

---

## Project Structure

The project is organised into the integrated website, feature-based review folders, development resources and submission documents.

The tree below shows the main directories and selected files.

```text
.
├── .github/
│   └── workflows/                   # CI workflow configuration
├── artifacts/
│   └── mockup-sandbox/               # Separate UI prototyping sandbox
├── docs/                            # Technical guides and supporting documentation
│   ├── previews/                    # Screenshots and UI animation examples
│   ├── explain-skill-gaps.md
│   ├── interview-practice-integration.md
│   └── pycharm-local-run.md
├── repository/                      # Feature-organised code, prototypes and tests
│   ├── 00 application/              # Application variants and browser checks
│   ├── 01 career_assessment/        # Assessment, matching and related checks
│   ├── 02 future_job_trend/         # Trend prototypes and reference files
│   ├── 03 employability_predictor/  # Earlier scenario implementation
│   ├── 04 reskilling/               # Selected learning-module files and checks
│   ├── 05 sdg_mapping/              # SDG Python and browser checks
│   ├── 06 frontend/                 # Theme and UI browser checks
│   ├── 07 multilingual/             # Language files and language checks
│   ├── 08 interview/                # Interview assets and integration checks
│   ├── 09 tests/                    # General integration and pathway checks
│   ├── 10_ai_explanations/          # Explanation tests and reference code
│   └── README.md
├── scripts/                         # Data imports, SDG audits and export utilities
├── src/                             # Integrated website source
│   ├── main.py                      # FastAPI application entry point
│   ├── assessment_scoring.py        # Questionnaire scoring
│   ├── career_engine.py             # Career matching and ranking
│   ├── career_profiles_clean.csv    # Career catalogue
│   ├── career_category_trends.csv
│   ├── career_category_trends.json
│   ├── data/                        # O*NET task and related evidence datasets
│   ├── hr_interview/                # Mounted Flask interview-practice module
│   │   ├── static/
│   │   └── templates/
│   ├── reskilling/                  # Learning, SDG and explanation services
│   │   ├── api.py
│   │   ├── catalog.py
│   │   ├── engine.py
│   │   ├── storage.py               # SQLite persistence
│   │   ├── index.html
│   │   └── static/
│   ├── static/                      # Main pages, styles, scripts and assets
│   │   ├── assets/
│   │   ├── i18n/
│   │   └── locales/
│   └── README.md
├── submission/
│   ├── REPLIT PROOF OF USE.pdf
│   ├── SDC2026_ Francium Fluoride_Preliminary_Technical Tools Declaration.pdf
│   └── SDC2026_FranciumFluoride_Preliminary.pdf
├── test/                            # Remaining earlier standalone prototypes
├── .gitignore
├── .replit                          # Replit runtime and development workflow
├── .replitignore
├── replit.md                        # Replit project notes
├── LICENSE
├── requirements.txt                 # Integrated application dependencies
├── run.py                           # Local/PyCharm launcher
└── README.md
```

### How the Folders Are Used

**`src/` — Integrated application**

The root `run.py` launcher and the Replit workflow load the FastAPI application
from `src/main.py`. The integrated website uses the modules, datasets and
frontend assets within `src/`.

**`repository/` — Feature-based organisation**

This directory groups related code, prototypes, assets and tests by feature.
Some files are earlier or alternative implementations, while others were moved
here during repository reorganisation. These folders are not independently
runnable replacements for the integrated application.

**`docs/` — Documentation and previews**

Contains setup guides, integration notes, screenshots and visual references.

**`scripts/` — Data and verification utilities**

Contains O*NET import tools, SDG evidence audits, exports and an optional
explanation-service smoke check.

**`submission/` — Hackathon materials**

Contains the preliminary submission, technical declaration and Replit
proof-of-use document.

Folder names containing spaces must be quoted when used in terminal commands.

### Architecture

The configured application architecture is:

```text
User's browser
HTML / CSS / JavaScript
        │
        ▼
FastAPI application — src/main.py
Hosted on Render
        │
        ├── Assessment scoring and career matching
        │
        ├── Career catalogue and O*NET evidence files
        │
        ├── Reskilling plans, scheduling and progress
        │       └── SQLite database and evidence uploads
        │
        ├── Qualitative trends and illustrative scenarios
        │
        ├── Exploratory occupational task-to-SDG analysis
        │
        ├── Optional skill-gap explanations ──► OpenAI API
        │
        └── Mounted Flask interview module ──► OpenAI API
                └── SQLite question-history index
```

| Component | Purpose |
| --- | --- |
| Render | Application hosting |
| Replit and PyCharm | Development and preview |
| GitHub | Source code and version control |
| FastAPI | Main application and API integration |
| Flask | Interview-practice module |
| SQLite | Learning profiles, tasks and interview question indexes |
| OpenAI API | Optional explanation and interview services |

The core assessment, career matching, learning-plan generation and SDG analysis
use rule-based logic. These features do not require GPU hosting or model
credentials.

Optional AI services depend on valid server-side configuration and provider
availability. RunPod is not used by the current application.

---

## How to Run

Use **Python 3.12** and run the following commands from the repository root.

### Current Reorganisation Status

At revision `0533ac1`, application startup is blocked by a relocated dependency:

```text
ModuleNotFoundError: No module named 'reskilling._prototype_catalog'
```

`src/reskilling/catalog.py` still imports that module from its own package,
while the file is now located at:

```text
repository/04 reskilling/_prototype_catalog.py
```

The required runtime package layout or its imports must be repaired before the
launch commands below can complete successfully.

### 1. Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Or on macOS/Linux:

```bash
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### 3. Start the Application

```bash
python run.py
```

Once startup succeeds, open:

**http://127.0.0.1:5000/**

In PyCharm, select the project's virtual environment and run the root
`run.py` file. See the
[中文 PyCharm 本地运行指南](docs/pycharm-local-run.md) for further instructions.

For Replit or a development server requiring an externally accessible port:

```bash
python -m uvicorn main:app --app-dir src --host 0.0.0.0 --port 5000
```

For Render, the equivalent start command uses its assigned port:

```bash
python -m uvicorn main:app --app-dir src --host 0.0.0.0 --port $PORT
```

### Main Pages

| Route | Purpose |
| --- | --- |
| `/` | Homepage and career assessment |
| `/career-overview` | Career overview workspace |
| `/careers` | Career browsing and search |
| `/my-profile` | Profile workspace |
| `/compare` | Career comparison |
| `/reskilling` | Skill ratings, learning plans and progress |
| `/ai-trend` | Future Job Trend: qualitative trend scenarios |
| `/uncertainty` | Employability Predictor: illustrative scenario exploration |
| `/sdg-impact` | Exploratory occupational task-to-SDG connections |
| `/interview-practice/` | Interview-practice interface and optional AI services |

Trend scenarios, employability calculations and SDG relevance scores are
exploratory prototype outputs. They have not been validated as employment
forecasts or measured SDG outcomes.

### Configuration and Storage

Core rule-based features require no model credentials. Optional AI features
require supported server-side configuration.

See the [skill-gap explanation guide](docs/explain-skill-gaps.md) and
[interview integration notes](docs/interview-practice-integration.md).

The local `run.py` launcher reads an optional root `.env` file. Hosted
deployments should configure environment variables through the hosting platform.

| Variable | Purpose |
| --- | --- |
| `FUTURESKILL_PORT` | Local `run.py` port; defaults to `5000` |
| `FUTURESKILL_DATA_DIR` | Private writable storage directory; defaults to `src/instance/` |
| `FUTURESKILL_DEV_INVENTORY` | Set to `1` to enable development screen-inventory routes |
| `OPENAI_API_KEY` | Credentials for the supported direct OpenAI integration |

Runtime databases and uploads are created separately and excluded from version
control. Keep credentials and private learner data out of Git.

Hosted persistence requires durable writable storage. Data stored on an
ephemeral filesystem may be lost during redeployment.

See [the application guide](src/README.md) for additional implementation details.
Some older documentation still references the previous folder layout.

### Run Tests

Tests are now distributed across the feature folders under `repository/`.

| Test Area | Current Location |
| --- | --- |
| Application browser checks | `repository/00 application/` |
| Assessment JavaScript checks | `repository/01 career_assessment/` |
| Learning-progress check | `repository/04 reskilling/` |
| SDG Python and browser checks | `repository/05 sdg_mapping/` |
| Theme and UI browser checks | `repository/06 frontend/` |
| Language checks | `repository/07 multilingual/` |
| Interview integration checks | `repository/08 interview/` |
| General integration and pathway checks | `repository/09 tests/` |
| Assessment-report and explanation Python checks | `repository/10_ai_explanations/` |

Run the language-pack and pathway-confirmation checks from the repository root:

```bash
node "repository/07 multilingual/language_packs.test.cjs"
node "repository/09 tests/pathway_confirmation.test.cjs"
```

After resolving runtime imports and test-relative paths, Python suites can be
discovered by feature folder. For example, on macOS/Linux:

```bash
PYTHONPATH=src python -m unittest discover -s "repository/05 sdg_mapping" -p "test_*.py" -v
```

On Windows PowerShell:

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s "repository/05 sdg_mapping" -p "test_*.py" -v
```

Some moved tests still reference their former source or fixture locations.
The CI workflow also still refers to the removed root `tests/` directory.
These internal paths require updating before the full suite can be treated
as working.

Browser checks require Chromium, a running application and a compatible
Node.js runtime. Consult each script for its base-URL configuration.

Automated Python checks do not verify successful live OpenAI requests.

---
---

## How We Use Replit 

- **Development:** We used Replit as a cloud workspace to develop and integrate the HTML, CSS and JavaScript frontend with our Python backend.

- **Prototyping:** Replit’s preview environment helped us review page layouts and refine the user journey across career assessment, reskilling and SDG exploration.

- **Version Control:** We connected our development workflow with GitHub to track changes, share updates and maintain a consistent project version.

- **Secrets:** AI integrations read credentials from server-side environment variables, allowing configuration through Replit Secrets without hard-coding API keys.

- **Hosting:** Replit supports our development and preview workflow. The public website is hosted on **Render**, using the code maintained in our GitHub repository.

📄 Proof of use: [`submission/REPLIT PROOF OF USE.pdf`](submission/REPLIT%20PROOF%20OF%20USE.pdf)

## How We Use RunPod *(Required)*

*Not applicable, we did not use RunPod for our project

---

## Challenges & Learnings

This was our first AI hackathon, and we began with limited experience in building a functional website. Each member brought different skills and ways of understanding the project. Some needed visual prototypes to communicate ideas, while others focused on application logic and getting the code to run. Aligning these perspectives became our first major challenge.

Integration was particularly difficult. We developed features across multiple versions and branches, with differences in dependencies, file structures and startup commands. A website that worked on one member’s computer would sometimes fail on another’s. Merging changes also occasionally overwrote important content or functionality, even when our AI prompts explicitly asked for them to be preserved. These setbacks showed us that clear instructions must be supported by careful code review, version control and testing.

As the deadline approached, we continued adding features without leaving enough time for debugging. Resolving the accumulated issues required considerable effort. Deploying the integrated prototype on Render eventually gave us a shared, accessible version that everyone could open and review.

Through this experience, we learned to treat AI-assisted development as an ongoing conversation. Clear context, screenshots, reference examples and descriptions of expected behaviour helped us communicate our ideas more effectively. Face-to-face discussions were equally valuable in keeping the team aligned.

We also learned to specify which functions and content must remain intact, review changes before merging, and test the complete user journey after integration. For future development, we will prioritise a stable core workflow, make smaller changes and reserve time for testing throughout the process.

## Future Improvements

**Add evidence-backed pathways for Malaysian careers**
Expand the five illustrative pathway templates into detailed profiles for an initial 10 Malaysian career roles, such as Software Developer, Data Analyst and Cybersecurity Analyst. Use employer-reviewed requirements and permitted local job-market data, with a source and review date for each skill requirement. This would make recommendations more relevant to local graduates and help users understand why a skill matters.

**Add skill checkpoints that adapt the learning roadmap**
Introduce short quizzes and practical exercises before and after learning activities. For example, a learner struggling with an SQL joins exercise could receive additional practice before progressing to a database project. Store assessment results and attempt history, then adjust upcoming tasks accordingly. Keep completed activities and demonstrated understanding visible as separate measures, giving users clearer feedback beyond XP and task completion.

## Team

| Name         | Role                | GitHub                                   |
| ------------ | ------------------- | ---------------------------------------- |
| Chew Yu Hang | Team Lead / Backend | [@username](https://github.com/Yuhang08) |
| Teh Yi Yang  | Frontend            | [@username](https://github.com/tehyy623) |
| Caleb Poh    | AI / Replit / Render| [@username](https://github.com/Francium-fluoride) |

---

## Submission Checklist

- [ / ] Team name, domain (Domain 1) and SDG track filled in
- [ / ] Slide deck link added
- [ / ] Demo video link added
- [ / ] Replit used, with proof of use in `submission/`
- [ X ] RunPod used, with proof of use in `submission/`
- [ / ] Submission template completed in `submission/`
- [ / ] "How to Run" steps verified
- [ / ] No API keys or secrets committed to the repository

## License

This project is licensed under the [Apache License 2.0](LICENSE).
