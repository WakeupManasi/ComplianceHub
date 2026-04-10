# Autonomous Compliance & Regulatory Intelligence System (A to Z)

## 1. Project Overview
This system is an AI-powered pipeline that automates the monitoring and analysis of regulatory changes in the Indian financial landscape. It targets the **Autonomous Compliance** problem by reducing the time from "Regulation Published" to "Impact Report Generated" from days to minutes.

---

## 2. The Multi-Agent Architecture
The system uses a swarm of **7 specialized AI Agents** working in a pipeline:

| Agent | Task | Tech Used |
| :--- | :--- | :--- |
| **Monitor Agent** | Scrapes RBI/SEBI sites every hour for new PDF/HTML notifications. | `BeautifulSoup4`, `Requests` |
| **Scraper Agent** | Downloads documents and extracts text. | `PyMuPDF` (PDF), `LXML` (HTML) |
| **Diff Agent** | Compares current regulation to the previous version to find clause-level changes. | `Difflib`, `Regex` |
| **Classifier Agent** | Categorizes changes (KYC, Cyber, FEMA) and assigns an impact score (Critical to Low). | `Keyword Ontology` |
| **Mapper Agent** | Maps changes to specific departments (Credit, IT, Legal) and products (Home Loans, UPI). | `Domain-driven Heuristics` |
| **Drafter Agent** | Drafts actual policy amendment text for internal use. | `LLM (GPT-4o / LangChain)` |
| **Reporter Agent** | Compiles all findings into a ready-to-use executive impact report. | `Report Templates` |

---

## 3. Database Schema (The "A to Z" Data)
I have built the following model structure in `regulatory_intel/models.py`:

- **`RegulatorySource`**: Tracks RBI, SEBI, MCA, etc.
- **`RegulatoryDocument`**: Stores PDFs, raw text, summaries, and impact levels.
- **`ClauseDiff`**: Records the exact delta (Old vs New) for modified clauses.
- **`ImpactMapping`**: Links changes to your company's Departments, Policies, and Systems.
- **`ImpactReport`**: The final output containing executive summaries and SOP changes.
- **`AgentLog`**: Full audit trail of everything the AI agents do.

---

## 4. How to Use the System

### A. Accessing the Dashboard
Go to `http://127.0.0.1:8000/intel/`. This will give you a bird's eye view of the entire regulatory landscape.

### B. Scanning for New Rules
1. Click the **"Scan Regulators"** button.
2. The **Monitor Agent** will visit the RBI and SEBI websites.
3. If new circulars are found, they will appear in the "Recent Documents" list.

### C. Running AI Analysis
1. Click on any new document.
2. Click **"Run Analysis"**.
3. Watch the **Agent Activity** feed. The agents will extract text, find diffs, map them to your departments, and generate a draft report.

### D. Reviewing and Approving
1. Go to the **"Reports"** tab.
2. Open the generated report.
3. Review the **AI-drafted Policy Amendments**.
4. Click **"Approve Report"** to mark it as ready for implementation.

---

## 5. Technical Stack Details
- **Backend**: Django (Python 3.13)
- **AI/LLM**: LangChain, OpenAI API (prepared for GPT-4o-mini)
- **Database**: SQLite3 (Local development)
- **Vector Search**: ChromaDB (installed for future RAG capabilities)
- **Frontend**: Custom Tailwind CSS + JavaScript (Glassmorphism layout)

---

## 6. Important Files I Created/Modified
1. `regulatory_intel/agents.py`: The "brain" of the project containing all agent logic.
2. `core/forms.py`: Fixed the registration bug (A-to-Z compatibility).
3. `templates/regulatory_intel/`: 7 premium UI templates for the dashboard and reports.
4. `regulatory_intel/views.py`: Controls the orchestration of the AI pipeline.
5. `requirements.txt`: Updated with 14+ new intelligence-category packages.

---
