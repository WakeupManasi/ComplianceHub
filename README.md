ComplianceHub — Autonomous Multi-Agent Regulatory & Breach Intelligence Platform

A zero-human-intervention, event-driven, multi-agent AI system for continuous regulatory surveillance,
semantic change detection, dark web credential intelligence, and predictive attack-vector inference —
purpose-architected for the Indian financial compliance continuum.

Architectural Thesis
Organizations operating under the Indian regulatory compliance continuum — governed by the Reserve Bank of India (RBI), the Securities and Exchange Board of India (SEBI), and the Ministry of Corporate Affairs (MCA) — face a dual-vector existential threat: regulatory drift compounded by credential surface exposure. Manual compliance monitoring pipelines collapse under the combinatorial pressure of hundreds of gazette notifications, master circulars, and policy amendments published annually. The RBI alone issued over 600 discrete notifications in 2024. Simultaneously, exfiltrated credentials surface on dark web forums within 48–96 hours of breach execution — frequently antedating any organizational incident response.
ComplianceHub dissolves both threat vectors through a fully decoupled, event-driven, multi-agent AI architecture: six autonomous agents, each owning a discrete epistemic domain.


✨ Features

🔍 Automated Regulatory Scraping — Continuously crawls RBI, SEBI, and MCA portals on a fixed schedule
📄 Document Version Tracking — Stores every version of every document with full change history
🔄 Change Detection — Detects exactly what changed between two versions of a regulation
🤖 AI-Powered Analysis — Uses LLMs to classify the change, assess risk, and generate compliance action items
🕵️ Dark Web Monitoring — Checks breach intelligence APIs (HIBP, Flare, SpyCloud) for leaked credentials or data
⚠️ Threat Prediction — Maps breach signals to likely attack vectors using MITRE ATT&CK and suggests remediation steps
📡 Real-Time Dashboard — Live updates pushed via WebSocket; no page refresh needed
🔁 Fault-Tolerant Pipeline — Automatic retries with exponential backoff; failed tasks go to a dead-letter queue
Research Group & Contributors

Project Structure
Compliancehub/
├── agents/
│   ├── scraping_agent.py          # Document acquisition, URL deduplication, crawl state
│   ├── preprocessing_layer.py     # PyMuPDF extraction, normalization, block hashing
│   ├── diff_agent.py              # Myers' lexical + ChromaDB semantic diff engine
│   ├── analysis_agent.py          # LangChain AgentExecutor, tool definitions, prompt templates
│   ├── darkweb_agent.py           # HIBP / Flare / SpyCloud API integrations, severity tiering
│   └── predictive_agent.py        # MITRE ATT&CK correlated threat inference, playbook generation
├── api/
│   ├── views.py                   # Django REST Framework viewsets
│   ├── serializers.py             # Pydantic / DRF serializer definitions
│   └── urls.py                    # API route declarations
├── config/
│   ├── settings.py                # Django configuration; environment variable loading via python-decouple
│   ├── celery.py                  # Celery application instance and Beat schedule registry
│   └── routing.py                 # Django Channels ASGI WebSocket routing
├── db/
│   ├── models.py                  # MongoEngine document schema definitions
│   └── indexes.py                 # Index provisioning scripts
├── frontend/
│   ├── templates/                 # Django-rendered HTML templates
│   ├── static/css/                # Dark-mode terminal stylesheet
│   └── static/js/                 # WebSocket client, Chart.js initialization, toast notifications
├── prompts/
│   └── analysis_prompts.py        # Parameterized LangChain prompt templates with context injection
├── orchestrator/
│   └── orchestrator.py            # Agent lifecycle manager, event router, DLQ handler, retry logic
├── requirements.txt
├── .env.example
└── README.md

Group: B2-5O5
Manasi Kulkarni  Github handle-@WakeupManasi
Tanishka Patil   Github handle-@TanishkaP03
Gaurav Pachpute  Github handle-@gauravpachpute

ComplianceHub — Autonomous Multi-Agent Regulatory & Breach Intelligence Platform
Group B2-505
