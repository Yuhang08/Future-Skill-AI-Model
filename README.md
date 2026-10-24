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
| GitHub Repository | [https://github.com/your-username/your-project](https://github.com/Yuhang08/Future-Skill-AI-Model)  |
| Replit Project    | [https://replit.com/@your-username/your-project](https://replit.com/@tehyy623/Future-Skill-AI-Model) |
| Live Demo         | [https://your-project.replit.app  ](https://future-skill-ai-model.onrender.com/)              |
| RunPod Endpoint   | None                                           |
| Slide Deck        | [https://example.com/slides ](https://www.canva.com/design/DAHY8lPJIu0/R1r_axxx3azZZKLuGaVGMw/edit)                    |
| Demo Video        | https://example.com/demo-video                 |

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

```
.
├── docs/                    # Screenshots, diagrams
├── runpod/
│   └── handler.py           # RunPod serverless handler (GPU workload)
├── src/
│   ├── main.py              # Application entry point
│   └── utils.py             # Helper functions
├── submission/              # Required submission documents
│   ├── REPLIT PROOF OF USE.pdf
│   ├── RUNPOD PROOF OF USE.pdf
│   └── Submission Template SDC Hackathon.pdf
├── tests/
│   └── test_utils.py        # Unit tests
├── .env.example             # Example environment variables
├── .gitignore
├── .replit                  # Replit run configuration
├── LICENSE
├── requirements.txt         # Python dependencies
└── README.md
```

### Architecture

```
User ──► Replit (App / API) ──► Render (GPU model)
                │
                └──► Response returned to user
```

---

## How to Run

The integrated FastAPI website starts at `src/main.py`. The older standalone
prototypes under `test/`, submission material and existing source datasets are
preserved. See [the website guide](src/README.md) for features, limitations and
private-data handling.

For PyCharm, select a Python 3.12 virtual environment, install the requirements,
then right-click the root [`run.py`](run.py) and choose **Run**. See the
[中文 PyCharm 本地运行指南](docs/pycharm-local-run.md) for updating from GitHub,
page addresses, optional settings and changing the local port.

```bash
# Run these commands from the repository root.
python -m pip install -r requirements.txt
python -m uvicorn main:app --app-dir src --host 0.0.0.0 --port 5000
```

Open `/` for the assessment, `/reskilling` for pathways, `/ai-trend` for
qualitative trends, `/uncertainty` for illustrative scenarios and `/sdg-impact`
for evidence-limited career connections. No model credential or RunPod endpoint
is required for these rule-based prototype pages.

The optional skill-gap explanation service requires supported server-side model
credentials; see [its contract and configuration](docs/explain-skill-gaps.md).
Do not commit credentials or private learner data. `FUTURESKILL_DATA_DIR` can
select a private writable storage location instead of the default `src/instance/`.
Development screen inventory is opt-in with `FUTURESKILL_DEV_INVENTORY=1`.
The earlier RunPod architecture notes elsewhere in this document are not a
claim that the current website has a working RunPod connection.

### Run Tests

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
node tests/assessment_progress.test.cjs
```

On PowerShell, set `$env:PYTHONPATH = "src"` first. Browser regression scripts
in `tests/` require Chromium and a running app. No real-provider request is
performed by the automated Python tests.

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
- [ ] Slide deck link added
- [ ] Demo video link added
- [ / ] Replit used, with proof of use in `submission/`
- [ X ] RunPod used, with proof of use in `submission/`
- [ / ] Submission template completed in `submission/`
- [ ] "How to Run" steps verified
- [ / ] No API keys or secrets committed to the repository

## License

This project is licensed under the [Apache License 2.0](LICENSE).
