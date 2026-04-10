ComplianceHub — Autonomous Multi-Agent Regulatory & Breach Intelligence Platform

A zero-human-intervention, event-driven, multi-agent AI system for continuous regulatory surveillance,
semantic change detection, dark web credential intelligence, and predictive attack-vector inference —
purpose-architected for the Indian financial compliance continuum.

Architectural Thesis
Organizations operating under the Indian regulatory compliance continuum — governed by the Reserve Bank of India (RBI), the Securities and Exchange Board of India (SEBI), and the Ministry of Corporate Affairs (MCA) — face a dual-vector existential threat: regulatory drift compounded by credential surface exposure. Manual compliance monitoring pipelines collapse under the combinatorial pressure of hundreds of gazette notifications, master circulars, and policy amendments published annually. The RBI alone issued over 600 discrete notifications in 2024. Simultaneously, exfiltrated credentials surface on dark web forums within 48–96 hours of breach execution — frequently antedating any organizational incident response.
ComplianceHub dissolves both threat vectors through a fully decoupled, event-driven, multi-agent AI architecture: six autonomous agents, each owning a discrete epistemic domain, communicating asynchronously via a Redis-backed inter-process message bus, converging at a WebSocket-native real-time intelligence dashboard. The system eliminates human-in-the-loop dependencies entirely — from document acquisition through semantic analysis, breach detection, and predictive threat modeling — delivering continuous operational intelligence as a stream, not a report.

System Architecture
ComplianceHub is structured as an event-driven, pipeline-based multi-agent system. Each agent is an independent Python module exposing LangChain-compatible tool functions. Agents communicate exclusively via a Redis pub/sub message bus, enabling full decoupling — no agent holds a direct Python reference to any sibling agent. All inter-agent coupling is mediated through a typed event schema.
The orchestration layer is a custom LangChain orchestrator class managing agent lifecycle transitions, event routing, failure state tracking, and execution context persistence in Redis hash maps keyed by execution_id. Per-agent timeouts enforce bounded execution windows; unrecoverable failures after three retry attempts are quarantined to a MongoDB dead-letter queue (DLQ) for asynchronous operator triage.

Agentic Integration

Agent Specifications
Agent 1 — Scraping Agent
The system's data acquisition perimeter. Operates as a Celery Beat-scheduled LangChain AgentExecutor with per-authority scraping tool functions. Maintains a crawl state manifest in MongoDB to enforce URL-level deduplication prior to initiating any network operation.
Document Acquisition Decision Tree:

Compute SHA-256 of normalized URL (lowercase, trailing slash stripped, query parameters lexicographically sorted)
Query raw_documents collection on url_hash unique index
If record found and doc_hash matches stored value — skip entirely; no I/O incurred
If record found with divergent doc_hash — flag as mutated document; initiate versioned re-acquisition
If record absent — new document; download, extract, and persist as inaugural version entry

Agent 2 — Dark Web Intelligence Agent
Interfaces exclusively with licensed threat intelligence APIs — zero direct dark web traversal is performed. Triggered by analysis.complete events where risk_level = HIGH, and on a fixed schedule for continuous baseline monitoring of all registered organizational domains.
Integrated Intelligence Providers:
ProviderCapabilityHave I Been Pwned (HIBP)Domain-level breach enumeration via /breaches?domain= endpointFlare SystemsStealer log monitoring, paste site indexing, dark web forum scanning with real-time webhook callbacksSpyCloudRecaptured breach records including plaintext credential exposure; ATO Prevention API for account takeover signals

Agent 3 — Diff Agent (Change Detection Engine)
Compares block-hash arrays of the inbound document version against the previously persisted version. Operates in two selectable modes dispatched per document type and structural complexity.
Lexical Diff Mode (Default): Implements Myers' diff algorithm via Python's difflib.SequenceMatcher at token granularity — not character level — for semantic accuracy. Produces structured change objects:

Semantic Diff Mode (ChromaDB-Enhanced): Activated when significant structural reordering produces false positives in lexical mode. Sentence-level embeddings stored in ChromaDB are compared via cosine similarity; a threshold of 0.85 determines semantic equivalence. Clauses falling below threshold are classified as genuine modifications regardless of positional correspondence — preventing regulatory intent alterations from being masked by document restructuring operations.

Agent 4 — Analysis Agent (LLM Core)
The primary LLM inference interface. Consumes structured diff reports and produces actionable compliance intelligence via LangChain AgentExecutor with Pydantic-validated output parsing.

Project Structure
compliancehub/
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

Deployment & Process Orchestration

1. Clone Repository
bashgit clone <repo-url>
cd compliancehub
2. Provision Virtual Environment
bashpython3 -m venv venv
source venv/bin/activate
3. Install Dependency Graph
bashpip install -r requirements.txt
4. Apply Django Migrations
bashpython manage.py migrate
5. Start Infrastructure Services
bash# Redis — message broker and cache layer
redis-server

# ChromaDB — vector embedding store
chroma run --host localhost --port 8000
6. Start Django ASGI Application Server
bash# Development
python manage.py runserver

# Production — Daphne ASGI with WebSocket support
daphne -p 8000 config.asgi:application
7. Start Celery Worker Pool
bash# 4 concurrent workers per agent task group
celery -A config worker --loglevel=info --concurrency=4
8. Start Celery Beat Scheduler
bashcelery -A config beat --loglevel=info
9. Start Flower (Optional — Task Monitoring Interface)
bashcelery -A config flower --port=5555

Research Group & Contributors

Group: B2-5O5
Manasi Kulkarni  Github handle-@WakeupManasi
Tanishka Patil   Github handle-@TanishkaP03
Gaurav Pachpute  Github handle-@gauravpachpute

ComplianceHub — Autonomous Multi-Agent Regulatory & Breach Intelligence Platform
Group B2-505
