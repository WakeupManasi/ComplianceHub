# 🚀 ComplianceHub — Autonomous Multi-Agent Regulatory & Breach Intelligence Platform

**Group B2-505**

ComplianceHub is a **zero-human-intervention, event-driven, multi-agent AI platform** designed for continuous regulatory surveillance, semantic change detection, dark web intelligence, and predictive attack-vector inference — purpose-built for the **Indian financial compliance ecosystem**.

---

## 🧠 Architectural Thesis

Organizations operating within the Indian regulatory ecosystem — governed by **RBI, SEBI, and MCA** — face a dual threat:

- **Regulatory Drift**: Hundreds of circulars, notifications, and amendments published annually  
- **Credential Exposure**: Breached credentials appearing on dark web platforms within 48–96 hours  

Manual compliance systems fail under this scale and velocity.

**ComplianceHub solves this** using a **fully decoupled, event-driven, multi-agent architecture** comprising six autonomous agents, each responsible for a distinct intelligence domain.

---

## ✨ Features

- 🔍 **Automated Regulatory Scraping**  
  Continuously crawls RBI, SEBI, and MCA portals on a fixed schedule  

- 📄 **Document Version Tracking**  
  Maintains version history of every document  

- 🔄 **Change Detection Engine**  
  Detects precise differences between document versions  

- 🤖 **AI-Powered Analysis**  
  Classifies regulatory changes, assesses risk, and generates action items  

- 🕵️ **Dark Web Monitoring**  
  Integrates with HIBP, Flare, SpyCloud for breach intelligence  

- ⚠️ **Threat Prediction**  
  Maps breaches to attack vectors using MITRE ATT&CK framework  

- 📡 **Real-Time Dashboard**  
  Live updates via WebSockets (no refresh required)  

- 🔁 **Fault-Tolerant Pipeline**  
  Retry logic with exponential backoff and dead-letter queue handling  

---

## 🏗️ System Architecture
Compliancehub/
├── agents/
│ ├── scraping_agent.py
│ ├── preprocessing_layer.py
│ ├── diff_agent.py
│ ├── analysis_agent.py
│ ├── darkweb_agent.py
│ └── predictive_agent.py
│
├── api/
│ ├── views.py
│ ├── serializers.py
│ └── urls.py
│
├── config/
│ ├── settings.py
│ ├── celery.py
│ └── routing.py
│
├── db/
│ ├── models.py
│ └── indexes.py
│
├── frontend/
│ ├── templates/
│ ├── static/css/
│ └── static/js/
│
├── prompts/
│ └── analysis_prompts.py
│
├── orchestrator/
│ └── orchestrator.py
│
├── requirements.txt
├── .env.example
└── README.md


---

## 🤖 Agent Overview

| Agent | Responsibility |
|------|----------------|
| **Scraping Agent** | Crawls regulatory portals, manages crawl state |
| **Preprocessing Layer** | Extracts and normalizes text (PyMuPDF) |
| **Diff Agent** | Performs lexical + semantic change detection |
| **Analysis Agent** | Uses LLMs for classification & recommendations |
| **Dark Web Agent** | Fetches breach intelligence from APIs |
| **Predictive Agent** | Maps threats to MITRE ATT&CK tactics |

---

## ⚙️ Tech Stack

- **Backend**: Django, Django REST Framework  
- **Async Processing**: Celery + Redis  
- **Realtime**: Django Channels (WebSockets)  
- **Database**: MongoDB (MongoEngine)  
- **AI/LLM**: LangChain  
- **Vector DB**: ChromaDB  
- **Frontend**: HTML, CSS (Dark Mode), JavaScript, Chart.js  

---

## 🔄 Workflow Pipeline

1. Scraping Agent fetches regulatory documents  
2. Preprocessing Layer extracts and normalizes content  
3. Diff Agent detects changes between versions  
4. Analysis Agent evaluates impact using LLMs  
5. Dark Web Agent monitors credential leaks  
6. Predictive Agent maps threats and suggests mitigations  
7. Results streamed live to dashboard  

---

## 🧪 Fault Tolerance

- Automatic retries with exponential backoff  
- Dead-letter queue for failed jobs  
- Idempotent processing across agents  

---

## 👩‍💻 Contributors

- **Manasi Kulkarni** — [@WakeupManasi](https://github.com/WakeupManasi)  
- **Tanishka Patil** — [@TanishkaP03](https://github.com/TanishkaP03)  
- **Gaurav Pachpute** — [@gauravpachpute](https://github.com/gauravpachpute)  

---

## 📌 License

This project is developed for academic and research purposes.

---

## 💡 Future Enhancements

- Automated compliance report generation  
- Multi-jurisdiction support beyond India  
- Advanced anomaly detection using graph ML  
- SOC integration & alert pipelines  

---
