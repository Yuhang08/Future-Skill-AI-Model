# Future-Skill-AI-Model

> Future-Skill-AI-Model is an AI-powered partner system that enables users to freely input their datasets, whereby the built in AI shall predict which skills and jobs will emerge or decline, matches today’s workforce and tomorrow’s talent to the right future roles, and generates personalised reskilling pathways, while showing how each role and skill connects to the 17 UN Sustainable Development Goals.

---

## Team Information

| Field                  | Details                                     |
| ---------------------- | ------------------------------------------- |
| **Team Name**          | Francium fluoride                           |
| **Team Domain**        | Domain 1                                    |
| **SDG Track (1–17)**   | SDG 4 — Quality education                   |
| **Team Leader**        | Chew Yu Hang                                |
| **University**         | Xiamen University Malaysia                  |
| **Number of Members**  | 3                                           |

## Links

| Resource          | Link                                           |
| ----------------- | ---------------------------------------------- |
| GitHub Repository | [https://github.com/your-username/your-project](https://github.com/Yuhang08/Future-Skill-AI-Model)  |
| Replit Project    | https://replit.com/@your-username/your-project |
| Live Demo         | https://your-project.replit.app                |
| RunPod Endpoint   | https://api.runpod.ai/v2/your-endpoint-id      |
| Slide Deck        | https://example.com/slides                     |
| Demo Video        | https://example.com/demo-video                 |

---

## Overview

### Problem

Fresh graduates may find it difficult to translate their current skills into the requirements of a specific career role and decide which skills to develop first. Job requirements, available learning resources, and career information can be distributed across different sources.

The team will investigate whether a structured comparison of a user's stated skills against sourced role requirements can help users understand their gaps and choose their next learning steps.

This problem statement is a hypothesis to validate, not a claim that all fresh graduates experience the same difficulty.

### Solution

[Explain how your project uses AI to solve the problem and what makes it valuable.]
We shall develop a prototype that allows a fresh graduate to:

S1- Enter their current skills manually or submit a CV through a tested and clearly explained workflow.
S2- Review and correct the skills identified from their profile.
S3- Select a target role from a small, curated set of roles with sourced skill requirements.
S4- Compare their stated skills with the selected role's requirements.
S5- View a prioritised reskilling roadmap with explanations and relevant learning resources.
S6- See a concise explanation of the role's relevant SDG connection where a defensible link exists.
---------------------------------------------------------------------------------------------------------------
Contribution of AI to the solution is also listed as shown:
1. AI-assisted skill extraction and normalisation

The system analyses a user's CV or manually entered experience to identify potential skills and map different expressions of similar skills to standardised skill categories. Users can review and correct the extracted profile before it is used for recommendations.

2. Context-aware skill-gap analysis

The system compares the user's reviewed skill profile with documented requirements for a selected career role. AI assists in interpreting related terminology and transferable skills, while transparent matching rules classify requirements as existing matches, potential gaps or uncertain. Each result is linked to the relevant role requirement.

3. Personalised reskilling recommendations

Based on identified gaps, the user's existing capabilities, preferred learning time and verified learning resources, AI helps construct an ordered learning roadmap. Each recommendation explains which skill gap it addresses and why the learning step is relevant. Time estimates are presented only where sufficient information supports them.

4. Evidence-grounded career and SDG explanations

The platform provides concise explanations of how a selected role relates to relevant UN Sustainable Development Goal targets. AI may assist with explanation, but the mapping is constrained by predefined target information and supporting evidence rather than generated freely.

5. Optional labour-market trend summaries

If time and reliable data permit, the platform may summarise published reports and dated job-skill information to show reported changes in demand. These summaries will distinguish observed data and published projections from speculative scenarios; the prototype will not claim validated future-job predictions without an appropriate forecasting method and evidence.

AI implementation principle

The platform uses a hybrid approach: AI interprets unstructured information and generates contextual explanations, while curated data and transparent rules anchor role requirements, skill-gap classifications, learning resources and SDG mappings. This makes recommendations more traceable and reduces unsupported claims. The platform is intended to support career planning and learning decisions, not guarantee employment or replace professional career advice.
---------------------------------------------------------------------------------------------------------------
The preliminary prototype will focus on transparent skill matching and learning guidance. It will not claim to predict future employment, guarantee job placement, or measure job satisfaction.

### Key Features

F1. Curated Skills and Job Dataset: A small, sourced set of target roles and their stated skill requirements.
F2. Personal Skill Profile: Manual skill entry or a tested CV-input flow with user review.
F3. Skill Gap Analysis: Transparent comparison of the user's stated skills with the selected role's requirements.
F4. Personalised Reskilling Roadmap: Prioritised learning steps and relevant resources based on the identified gaps.
F5. Explainable Recommendations: A clear explanation of the criteria behind each gap and recommendation.
F6. Relevant SDG Mapping: A short, justified mapping to relevant SDG targets where appropriate.

### Tech Stack

| Layer         | Technology                   |
| ------------- | ---------------------------- |
| Frontend      | e.g. HTML, React             |
| Backend       | e.g. Python, Flask / FastAPI |
| Database      | e.g. PostgreSQL, SQLite      |
| AI / Compute  | RunPod (GPU)                 |
| Hosting / Dev | Replit                       |

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
User ──► Replit (App / API) ──► RunPod Endpoint (GPU model)
                │
                └──► Response returned to user
```

---

## How to Run

### Option 1 — Run on Replit (Recommended)

1. Open the [Replit Project](https://replit.com/@your-username/your-project), or import this repository via **Create Repl → Import from GitHub**.
2. Open the **Secrets** tab (🔒) and add the variables listed in `.env.example`:
   - `RUNPOD_API_KEY`
   - `RUNPOD_ENDPOINT_ID`
3. Click **Run**. Replit uses the `.replit` file to start `python src/main.py`.

### Option 2 — Run Locally

```bash
# 1. Clone the repository
git clone https://github.com/your-username/your-project.git
cd your-project

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env            # then fill in your values

# 5. Run the app
python src/main.py
```

### Run Tests

```bash
python -m unittest discover tests
```

---

## How We Use Replit *(Required)*

Describe how your team used Replit. For example:

- **Development:** Collaborative coding in a shared Repl using Multiplayer.
- **Hosting:** The app is deployed with Replit Deployments at the Live Demo link above.
- **Secrets:** API keys are stored in Replit Secrets, never in the code.

📄 Proof of use: [`submission/REPLIT PROOF OF USE.pdf`](submission/REPLIT%20PROOF%20OF%20USE.pdf)

## How We Use RunPod *(Required)*

Describe how your team used RunPod. For example:

- **Workload:** Model inference (e.g. text generation, image processing) runs on a RunPod GPU.
- **Setup:** `runpod/handler.py` is deployed as a **RunPod Serverless Endpoint**.
- **Integration:** The Replit app sends requests to the endpoint using `RUNPOD_API_KEY` and `RUNPOD_ENDPOINT_ID`.

Example request:

```bash
curl -X POST https://api.runpod.ai/v2/$RUNPOD_ENDPOINT_ID/runsync \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"input": {"prompt": "Hello"}}'
```

📄 Proof of use: [`submission/RUNPOD PROOF OF USE.pdf`](submission/RUNPOD%20PROOF%20OF%20USE.pdf)

---

## Challenges & Learnings

- What challenges did you face, and how did you overcome them?
- What did your team learn?

## Future Improvements

- [ ] Improvement 1
- [ ] Improvement 2

## Team

| Name        | Role                | GitHub                                   |
| ----------- | ------------------- | ---------------------------------------- |
| Member Name | Team Lead / Backend | [@username](https://github.com/username) |
| Member Name | Frontend            | [@username](https://github.com/username) |
| Member Name | AI / RunPod         | [@username](https://github.com/username) |

---

## Submission Checklist

- [ ] Team name, domain (Domain 1 / Domain 2) and SDG track filled in
- [ ] Slide deck link added
- [ ] Demo video link added
- [ ] Replit used, with proof of use in `submission/`
- [ ] RunPod used, with proof of use in `submission/`
- [ ] Submission template completed in `submission/`
- [ ] "How to Run" steps verified
- [ ] No API keys or secrets committed to the repository

## License

This project is licensed under the [Apache License 2.0](LICENSE).
