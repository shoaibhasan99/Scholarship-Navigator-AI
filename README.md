# 🎓 Scholarship Navigator AI

**Scholarship Dhundo, Future Banao.**

Scholarship Navigator AI is a multi-agent AI system that helps students discover international scholarship opportunities, check eligibility, verify official requirements, and prepare an application roadmap from their academic profile.

> Built for the **HEC-NCEAC & PEC Generative & Agentic AI Training — Cohort 11 | Hackathon 2**

---

## ✨ What It Does

Students upload their:

- CV / Resume
- Academic Transcript
- IELTS Report *(optional)*

Then select:

- Target country
- Degree level

The system runs a coordinated AI workflow to:

1. Extract the student's academic profile.
2. Discover relevant scholarship opportunities.
3. Check deterministic eligibility requirements.
4. Verify uncertain scholarship criteria using official sources.
5. Generate an application-oriented roadmap and missing-document checklist.

---

## 🤖 Multi-Agent Architecture

Scholarship Navigator AI uses specialized agents instead of relying on a single prompt.

| Agent | Responsibility |
|---|---|
| 🧠 **Profile Agent** | Extracts student information from uploaded documents |
| 🔎 **Discovery Agent** | Finds relevant scholarship opportunities |
| 🛡️ **Eligibility Agent** | Checks profile requirements such as CGPA, degree and English proficiency |
| ✅ **Evidence Agent** | Verifies uncertain requirements against official sources |
| 📋 **Planner Agent** | Builds the final scholarship/application roadmap |

The workflow is orchestrated using **LangGraph**.

---

## 🌍 Supported Destinations

The current version supports scholarship discovery for:

- 🇰🇷 South Korea
- 🇨🇳 China
- 🇯🇵 Japan
- 🇹🇼 Taiwan
- 🇩🇪 Germany
- 🇲🇾 Malaysia
- 🇸🇬 Singapore
- 🇭🇰 Hong Kong

Supported study levels:

- Master's
- PhD

---

## 🔍 Scholarship Information Shown

Where available, the interface displays:

- Scholarship name
- Opening date
- Application deadline
- IELTS requirement
- TOEFL requirement
- Minimum CGPA
- Required degree
- Funding information
- Eligibility status
- Missing documents
- Official scholarship source
- Previous-cycle dates for reference

> **Note:** Scholarship requirements and deadlines can change. Applicants should always confirm final information on the linked official source before applying.

---

## 🧰 Tech Stack

### Frontend
- React
- Vite
- JavaScript
- CSS
- Lucide React

### Backend
- Python
- FastAPI
- Pydantic
- LangGraph

### AI / Search
- OpenAI-compatible LLM workflow
- Tavily search
- Multi-agent orchestration
- Official-source verification

### Document Processing
- PDF parsing
- Structured profile extraction

---

## 🏗️ Project Structure

```text
Scholarship-Navigator-AI/
│
├── backend/
│   ├── agents/
│   │   ├── discovery_agent.py
│   │   ├── eligibility_agent.py
│   │   ├── evidence_agent.py
│   │   ├── planner_agent.py
│   │   ├── profile_agent.py
│   │   └── scholarship_verifier_agent.py
│   │
│   ├── tools/
│   │   └── document_parser.py
│   │
│   ├── graph.py
│   ├── main.py
│   ├── models.py
│   ├── state.py
│   └── test_models.py
│
├── data/
│   ├── evidence.json
│   └── scholarships.json
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
│
├── .env.example
├── .gitignore
└── README.md
```

---

## ⚙️ Environment Variables

Create a `.env` file in the project root based on `.env.example`.

```env
OPENAI_API_KEY=your_openai_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

Never commit your real `.env` file or API keys.

---

## 🚀 Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/shoaibhasan99/Scholarship-Navigator-AI.git
cd Scholarship-Navigator-AI
```

### 2. Start the backend

Create and activate a Python virtual environment, install the backend dependencies, and run FastAPI.

```bash
cd backend
python -m venv .venv
```

**Windows PowerShell**

```powershell
.\.venv\Scripts\Activate.ps1
```

Then install the required Python packages and start the API:

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

The backend will run at:

```text
http://127.0.0.1:8000
```

### 3. Start the frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Vite will display the local frontend URL in the terminal.

---

## 🔄 Application Flow

```text
Student Documents
       │
       ▼
  Profile Agent
       │
       ▼
 Discovery Agent
       │
       ▼
Eligibility Agent
       │
       ▼
 Evidence Agent
       │
       ▼
 Planner Agent
       │
       ▼
Scholarship Matches
```

---

## 🧠 Why Agentic AI?

Scholarship applications involve several different reasoning tasks:

- Understanding a student profile
- Searching for opportunities
- Comparing academic requirements
- Resolving uncertain information
- Checking evidence
- Planning next actions

Separating these responsibilities into specialized agents makes the workflow easier to reason about, extend, and verify.

---

## 🛡️ Evidence-First Design

A central goal of the project is to avoid presenting uncertain scholarship requirements as confirmed facts.

The system attempts to:

- Prefer official university or scholarship sources
- Separate known requirements from uncertain ones
- Verify uncertain criteria where possible
- Preserve official source links
- Mark historical application dates as previous-cycle references

---

## 🎯 Product Goal

The project aims to reduce the time students spend manually searching through university websites and scholarship pages while helping them understand:

> **Which opportunities are relevant to me, why do I qualify, and what should I do next?**

---

## 📌 Hackathon Submission

| Item | Link |
|---|---|
| 💻 GitHub Repository | https://github.com/shoaibhasan99/Scholarship-Navigator-AI |
| 🌐 Live Application | *Coming soon* |
| 📄 PRD | *Coming soon* |
| 🖥️ Presentation Slides | *Coming soon* |
| 🎥 Presentation Video | *Coming soon* |

---

## 🚧 Current Limitations

- Scholarship information may change after discovery.
- Some official pages may not expose complete requirements in machine-readable form.
- Previous-cycle dates are shown only as historical references.
- Search quality depends on the availability and accessibility of official web sources.
- Users should always verify final requirements directly with the scholarship provider.

---

## 🔮 Future Improvements

- Personalized scholarship ranking
- Saved scholarship lists
- Deadline reminders
- Application progress tracking
- Email notifications
- SOP / motivation-letter assistance
- More countries and scholarship providers
- Improved document extraction
- Production deployment with persistent storage

---

## 👨‍💻 Author

**Shoaib Hasan**

AI / Computer Vision enthusiast building intelligent systems with Python, deep learning, and agentic AI.

GitHub: [@shoaibhasan99](https://github.com/shoaibhasan99)

---

## ⭐ Support

If you find the project useful, consider giving the repository a ⭐ on GitHub.
