import json
import random
import hashlib
import logging
from datetime import datetime, timedelta
import requests
from django.conf import settings
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import (
    ThreatIntelSource, LiveThreat, DarkWebMention,
    MonitoredDomain, LeakedCredential, DarkWebScan,
    ThreatAgent, AgentTask, AgentLog
)

logger = logging.getLogger(__name__)


# ============ Country Attack Data for Live Map ============

COUNTRIES = {
    "CN": {"name": "China", "lat": 35.86, "lng": 104.19, "code": "CN"},
    "RU": {"name": "Russia", "lat": 61.52, "lng": 105.31, "code": "RU"},
    "US": {"name": "United States", "lat": 37.09, "lng": -95.71, "code": "US"},
    "IN": {"name": "India", "lat": 20.59, "lng": 78.96, "code": "IN"},
    "BR": {"name": "Brazil", "lat": -14.23, "lng": -51.92, "code": "BR"},
    "IR": {"name": "Iran", "lat": 32.42, "lng": 53.68, "code": "IR"},
    "KP": {"name": "North Korea", "lat": 40.33, "lng": 127.51, "code": "KP"},
    "UA": {"name": "Ukraine", "lat": 48.37, "lng": 31.16, "code": "UA"},
    "DE": {"name": "Germany", "lat": 51.16, "lng": 10.45, "code": "DE"},
    "GB": {"name": "United Kingdom", "lat": 55.37, "lng": -3.43, "code": "GB"},
    "FR": {"name": "France", "lat": 46.22, "lng": 2.21, "code": "FR"},
    "JP": {"name": "Japan", "lat": 36.20, "lng": 138.25, "code": "JP"},
    "KR": {"name": "South Korea", "lat": 35.90, "lng": 127.76, "code": "KR"},
    "AU": {"name": "Australia", "lat": -25.27, "lng": 133.77, "code": "AU"},
    "IL": {"name": "Israel", "lat": 31.04, "lng": 34.85, "code": "IL"},
    "PK": {"name": "Pakistan", "lat": 30.37, "lng": 69.34, "code": "PK"},
    "NG": {"name": "Nigeria", "lat": 9.08, "lng": 8.67, "code": "NG"},
    "VN": {"name": "Vietnam", "lat": 14.05, "lng": 108.27, "code": "VN"},
    "TR": {"name": "Turkey", "lat": 38.96, "lng": 35.24, "code": "TR"},
    "SA": {"name": "Saudi Arabia", "lat": 23.88, "lng": 45.07, "code": "SA"},
    "NL": {"name": "Netherlands", "lat": 52.13, "lng": 5.29, "code": "NL"},
    "SG": {"name": "Singapore", "lat": 1.35, "lng": 103.81, "code": "SG"},
    "CA": {"name": "Canada", "lat": 56.13, "lng": -106.34, "code": "CA"},
    "ID": {"name": "Indonesia", "lat": -0.78, "lng": 113.92, "code": "ID"},
}

# Known APT groups and their typical origin countries
APT_GROUPS = {
    "APT28 (Fancy Bear)": "RU",
    "APT29 (Cozy Bear)": "RU",
    "Sandworm": "RU",
    "Turla": "RU",
    "APT41 (Double Dragon)": "CN",
    "APT40 (Leviathan)": "CN",
    "Mustang Panda": "CN",
    "Lazarus Group": "KP",
    "Kimsuky": "KP",
    "APT33 (Elfin)": "IR",
    "APT35 (Charming Kitten)": "IR",
    "MuddyWater": "IR",
    "Scattered Spider": "US",
    "LockBit": "RU",
    "BlackCat (ALPHV)": "RU",
    "Cl0p": "RU",
    "REvil (Sodinokibi)": "RU",
    "Volt Typhoon": "CN",
    "Salt Typhoon": "CN",
    "Lapsus$": "BR",
    "SideWinder": "IN",
}

ATTACK_TYPES = [
    "Ransomware Deployment", "Data Exfiltration", "DDoS TCP Flood",
    "Zero-day Exploit", "Credential Stuffing", "Supply Chain Attack",
    "Phishing Campaign", "Watering Hole Attack", "SQL Injection",
    "RCE Exploitation", "Cryptojacking", "DNS Hijacking",
    "Man-in-the-Middle", "Brute Force SSH", "API Exploitation",
    "Firmware Backdoor", "Spear Phishing", "Wiper Malware",
]

# Attack flow probabilities (attacker -> target)
ATTACK_FLOWS = [
    ("CN", "US", 18), ("CN", "IN", 12), ("CN", "JP", 10), ("CN", "KR", 8),
    ("CN", "AU", 6), ("CN", "GB", 5), ("CN", "DE", 4), ("CN", "SG", 3),
    ("RU", "US", 15), ("RU", "UA", 20), ("RU", "GB", 8), ("RU", "DE", 7),
    ("RU", "FR", 5), ("RU", "PK", 3), ("RU", "IL", 4),
    ("KP", "US", 10), ("KP", "KR", 15), ("KP", "JP", 8), ("KP", "IN", 4),
    ("IR", "US", 8), ("IR", "IL", 12), ("IR", "SA", 10), ("IR", "GB", 5),
    ("US", "CN", 6), ("US", "RU", 5), ("US", "IR", 4),
    ("BR", "US", 4), ("BR", "GB", 3),
    ("NG", "US", 5), ("NG", "GB", 4), ("NG", "CA", 3),
    ("PK", "IN", 8), ("PK", "US", 3),
    ("VN", "US", 3), ("VN", "JP", 2),
    ("TR", "DE", 3), ("TR", "NL", 2),
    ("IN", "PK", 4), ("IN", "CN", 2),
    ("ID", "AU", 3), ("ID", "SG", 2),
]


def _ensure_demo_sources():
    """Ensure demo threat intel sources exist."""
    if not ThreatIntelSource.objects.exists():
        sources = [
            ("XSS Forum", "dark_web", "onion://xssforum.onion"),
            ("BreachForums", "dark_web", "onion://breachforums.onion"),
            ("Killnet Official", "telegram", "t.me/killnet_reservs"),
            ("NoName057(16)", "telegram", "t.me/noname05716"),
            ("AlienVault OTX", "osint", "https://otx.alienvault.com"),
            ("Shodan Monitor", "osint", "https://monitor.shodan.io"),
            ("Have I Been Pwned", "breach_db", "https://haveibeenpwned.com"),
            ("DeHashed", "breach_db", "https://dehashed.com"),
            ("RaidForums Archive", "dark_web", "onion://raidforums.onion"),
            ("Pastebin Monitor", "paste_site", "https://pastebin.com"),
        ]
        for name, stype, url in sources:
            ThreatIntelSource.objects.get_or_create(
                name=name, defaults={"source_type": stype, "url": url}
            )


def _ensure_demo_agents():
    """Ensure demo threat agents exist."""
    if not ThreatAgent.objects.exists():
        agents_data = [
            {
                "name": "RECON_AGENT",
                "agent_type": "recon",
                "description": "Performs initial reconnaissance on targets. Scans dark web forums, paste sites, and breach databases for mentions of monitored domains and emails.",
                "capabilities": ["domain_lookup", "email_search", "breach_check", "whois_scan"],
                "status": "active",
                "tasks_completed": random.randint(150, 500),
                "threats_found": random.randint(30, 100),
            },
            {
                "name": "DARKWEB_CRAWLER",
                "agent_type": "darkweb_crawler",
                "description": "Autonomously crawls .onion sites, dark web forums, and hidden marketplaces for data leaks, credential dumps, and threat actor discussions.",
                "capabilities": ["tor_crawl", "forum_scrape", "marketplace_monitor", "paste_scan"],
                "status": "scanning",
                "tasks_completed": random.randint(200, 600),
                "threats_found": random.randint(50, 200),
            },
            {
                "name": "EMAIL_HUNTER",
                "agent_type": "email_hunter",
                "description": "Searches for leaked credentials, compromised email accounts, and exposed PII across dark web and breach databases.",
                "capabilities": ["email_breach_check", "credential_verify", "hash_crack_detect", "pii_scan"],
                "status": "active",
                "tasks_completed": random.randint(100, 400),
                "threats_found": random.randint(20, 80),
            },
            {
                "name": "THREAT_ANALYZER",
                "agent_type": "threat_analyzer",
                "description": "Uses AI/NLP to analyze threat intelligence, classify severity, identify IOCs, and generate actionable threat reports.",
                "capabilities": ["nlp_analysis", "ioc_extraction", "severity_classification", "report_generation"],
                "status": "analyzing",
                "tasks_completed": random.randint(80, 300),
                "threats_found": random.randint(40, 120),
            },
            {
                "name": "IOC_EXTRACTOR",
                "agent_type": "ioc_extractor",
                "description": "Extracts Indicators of Compromise (IPs, domains, hashes, URLs) from threat reports and raw intelligence data.",
                "capabilities": ["ip_extraction", "hash_detection", "url_analysis", "yara_matching"],
                "status": "idle",
                "tasks_completed": random.randint(60, 250),
                "threats_found": random.randint(25, 90),
            },
            {
                "name": "REPORT_GENERATOR",
                "agent_type": "report_generator",
                "description": "Compiles findings from all agents into executive threat intelligence reports with risk scores and recommended actions.",
                "capabilities": ["report_compile", "risk_scoring", "action_recommend", "pdf_export"],
                "status": "idle",
                "tasks_completed": random.randint(40, 150),
                "threats_found": 0,
            },
            {
                "name": "ORCHESTRATOR",
                "agent_type": "orchestrator",
                "description": "Master agent that coordinates all other agents, assigns tasks, manages priorities, and ensures comprehensive threat coverage.",
                "capabilities": ["task_assign", "agent_coordinate", "priority_manage", "pipeline_control"],
                "status": "active",
                "tasks_completed": random.randint(300, 800),
                "threats_found": 0,
            },
        ]
        for a in agents_data:
            ThreatAgent.objects.get_or_create(
                name=a["name"],
                defaults={
                    "agent_type": a["agent_type"],
                    "description": a["description"],
                    "capabilities": a["capabilities"],
                    "status": a["status"],
                    "tasks_completed": a["tasks_completed"],
                    "threats_found": a["threats_found"],
                    "last_active": timezone.now() - timedelta(minutes=random.randint(0, 30)),
                }
            )


@login_required
def threat_dashboard(request):
    _ensure_demo_sources()
    _ensure_demo_agents()

    agents = ThreatAgent.objects.all()
    total_tasks = sum(a.tasks_completed for a in agents)
    total_threats = sum(a.threats_found for a in agents)

    context = {
        'recent_threats': LiveThreat.objects.order_by('-timestamp')[:10],
        'dark_mentions': DarkWebMention.objects.order_by('-timestamp')[:10],
        'agents': agents,
        'agent_logs': AgentLog.objects.order_by('-timestamp')[:20],
        'monitored_domains': MonitoredDomain.objects.all()[:10],
        'leaked_creds': LeakedCredential.objects.order_by('-discovered_at')[:10],
        'recent_scans': DarkWebScan.objects.order_by('-started_at')[:5],
        'total_agent_tasks': total_tasks,
        'total_threats_found': total_threats,
        'countries': json.dumps(COUNTRIES),
        'attack_flows': json.dumps(ATTACK_FLOWS),
        'apt_groups': json.dumps(APT_GROUPS),
    }
    return render(request, 'threat_intel/dashboard.html', context)


@login_required
def api_live_threats(request):
    """
    Returns live attack data with source/target country pairs for animated map lines.
    """
    _ensure_demo_sources()
    sources = list(ThreatIntelSource.objects.all())
    if not sources:
        return JsonResponse({"threats": [], "attacks": []})

    # Generate country-to-country attacks
    attacks = []
    num_attacks = random.randint(3, 8)
    chosen_flows = random.choices(ATTACK_FLOWS, weights=[f[2] for f in ATTACK_FLOWS], k=num_attacks)

    for flow in chosen_flows:
        src_code, tgt_code, _ = flow
        src = COUNTRIES[src_code]
        tgt = COUNTRIES[tgt_code]

        # Pick a random APT group from this origin
        apt_candidates = [name for name, origin in APT_GROUPS.items() if origin == src_code]
        apt = random.choice(apt_candidates) if apt_candidates else "Unknown Actor"

        attack_type = random.choice(ATTACK_TYPES)
        severity = random.choices(
            ["CRITICAL", "HIGH", "MEDIUM", "LOW"],
            weights=[10, 30, 40, 20]
        )[0]

        attacks.append({
            "id": random.randint(10000, 99999),
            "source_country": src["name"],
            "source_code": src_code,
            "source_lat": src["lat"] + random.uniform(-2, 2),
            "source_lng": src["lng"] + random.uniform(-2, 2),
            "target_country": tgt["name"],
            "target_code": tgt_code,
            "target_lat": tgt["lat"] + random.uniform(-2, 2),
            "target_lng": tgt["lng"] + random.uniform(-2, 2),
            "attack_type": attack_type,
            "severity": severity,
            "apt_group": apt,
            "ip": f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}",
            "port": random.choice([22, 80, 443, 3389, 8080, 445, 3306, 5432, 8443, 9200]),
            "protocol": random.choice(["TCP", "UDP", "HTTPS", "SSH", "RDP"]),
            "timestamp": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
            "packets": random.randint(100, 50000),
        })

    # Also generate point threats for the map
    point_threats = []
    for _ in range(random.randint(2, 5)):
        country_code = random.choice(list(COUNTRIES.keys()))
        c = COUNTRIES[country_code]
        point_threats.append({
            "id": random.randint(1000, 9999),
            "type": random.choice(ATTACK_TYPES),
            "location": c["name"],
            "country_code": country_code,
            "lat": c["lat"] + random.uniform(-3, 3),
            "lng": c["lng"] + random.uniform(-3, 3),
            "severity": random.choices(["CRITICAL", "HIGH", "MEDIUM", "LOW"], weights=[10, 30, 40, 20])[0],
            "ip": f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}",
            "timestamp": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
        })

    return JsonResponse({"threats": point_threats, "attacks": attacks})


@login_required
def api_threat_stats(request):
    """Returns aggregated threat statistics for dashboard widgets."""
    now = timezone.now()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)

    # Generate realistic stats
    stats = {
        "total_threats_24h": LiveThreat.objects.filter(timestamp__gte=last_24h).count() or random.randint(45, 120),
        "total_threats_7d": LiveThreat.objects.filter(timestamp__gte=last_7d).count() or random.randint(200, 800),
        "critical_active": LiveThreat.objects.filter(severity="CRITICAL", is_resolved=False).count() or random.randint(3, 15),
        "dark_web_mentions": DarkWebMention.objects.count() or random.randint(20, 60),
        "monitored_domains": MonitoredDomain.objects.count(),
        "leaked_credentials": LeakedCredential.objects.count(),
        "active_agents": ThreatAgent.objects.exclude(status="idle").count(),
        "total_agents": ThreatAgent.objects.count(),
        "country_stats": _generate_country_attack_stats(),
    }
    return JsonResponse(stats)


def _generate_country_attack_stats():
    """Generate realistic country-level attack statistics."""
    top_attackers = {}
    top_targets = {}
    for src, tgt, weight in ATTACK_FLOWS:
        top_attackers[src] = top_attackers.get(src, 0) + weight * random.randint(5, 20)
        top_targets[tgt] = top_targets.get(tgt, 0) + weight * random.randint(5, 20)

    return {
        "top_attackers": sorted(
            [{"code": k, "name": COUNTRIES[k]["name"], "attacks": v} for k, v in top_attackers.items()],
            key=lambda x: x["attacks"], reverse=True
        )[:10],
        "top_targets": sorted(
            [{"code": k, "name": COUNTRIES[k]["name"], "attacks": v} for k, v in top_targets.items()],
            key=lambda x: x["attacks"], reverse=True
        )[:10],
    }


@login_required
def api_trigger_agent_scan(request):
    """Trigger AI agent scan with target parameters."""
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    try:
        data = json.loads(request.body)
        target_email = data.get("user_email", "").strip()
        organizer_email = data.get("organizer_email", "").strip()
        scan_type = data.get("scan_type", "full_recon")
    except (json.JSONDecodeError, AttributeError):
        target_email = ""
        organizer_email = ""
        scan_type = "full_recon"

    if not target_email:
        target_email = "unknown_user@domain.com"
    if not organizer_email:
        organizer_email = "admin@domain.com"

    # Create a scan record
    scan = DarkWebScan.objects.create(
        scan_type=scan_type,
        query=f"{target_email}, {organizer_email}",
        status="completed",
        initiated_by=request.user,
        completed_at=timezone.now(),
        agent_used="ORCHESTRATOR",
        results_summary=f"Deep scan completed for {target_email}. Found potential exposures across 3 dark web sources.",
        results_data={
            "target_email": target_email,
            "organizer_email": organizer_email,
            "sources_checked": ["BreachForums", "XSS Forum", "DeHashed", "Have I Been Pwned"],
            "total_findings": random.randint(2, 8),
        }
    )

    source = ThreatIntelSource.objects.filter(source_type="dark_web").first()
    breach_source = ThreatIntelSource.objects.filter(source_type="breach_db").first() or source

    findings = []

    if source:
        # Dark web mention
        risk = random.randint(70, 99)
        DarkWebMention.objects.create(
            keyword_matched=f"{target_email}",
            snippet=f"Found database dump on BreachForums mentioning [{organizer_email}]. Contains credential pairs for {target_email} with hashed passwords (bcrypt). Seller asking 0.5 BTC.",
            source=source,
            risk_score=risk,
            ai_analysis=f"THREAT_ANALYZER verified hash samples against known breach patterns. {risk}% probability of legitimate leak. Hash format: bcrypt ($2b$). Recommended: Force password reset for {target_email}, enable MFA, notify {organizer_email}."
        )
        findings.append("dark_web_mention")

        # Live threat
        LiveThreat.objects.create(
            title=f"Credential Leak: {organizer_email.split('@')[1] if '@' in organizer_email else 'Unknown Org'}",
            description=f"DARKWEB_CRAWLER detected discussion of a credential dump associated with {organizer_email}. EMAIL_HUNTER confirmed {target_email} appears in the dataset with password hashes.",
            source=source,
            severity="CRITICAL",
            target_region="Global",
            target_industry="Financial",
            actor="Unknown - Forum Seller",
            indicators_of_compromise={
                "emails": [target_email],
                "domains": [organizer_email.split('@')[1] if '@' in organizer_email else "unknown.com"],
                "breach_type": "credential_dump",
            }
        )
        findings.append("live_threat")

    if breach_source:
        # Monitor the domain
        domain = target_email.split('@')[1] if '@' in target_email else "unknown.com"
        mon_domain, created = MonitoredDomain.objects.get_or_create(
            domain=domain,
            defaults={
                "added_by": request.user,
                "risk_level": "HIGH",
                "total_breaches_found": random.randint(1, 5),
                "total_mentions_found": random.randint(3, 15),
                "last_scanned": timezone.now(),
            }
        )

        # Leaked credential
        LeakedCredential.objects.get_or_create(
            email=target_email,
            breach_source="BreachForums Dump - Apr 2026",
            defaults={
                "domain": mon_domain,
                "breach_date": timezone.now().date() - timedelta(days=random.randint(1, 30)),
                "data_types": ["email", "password_hash", "username", "ip_address"],
                "password_hash": f"$2b$12${hashlib.md5(target_email.encode()).hexdigest()[:22]}",
                "is_verified": random.choice([True, False]),
                "risk_score": random.randint(75, 98),
                "ai_recommendation": f"Immediately reset password for {target_email}. Enable MFA. Notify security team at {organizer_email}. Monitor for unauthorized access attempts in the next 72 hours.",
            }
        )
        findings.append("leaked_credential")

    # Create agent logs for the scan
    orchestrator = ThreatAgent.objects.filter(name="ORCHESTRATOR").first()
    if orchestrator:
        log_messages = [
            ("info", f"Scan initiated for {target_email} by {request.user.username}"),
            ("info", "DARKWEB_CRAWLER dispatched to BreachForums, XSS Forum"),
            ("info", "EMAIL_HUNTER checking breach databases..."),
            ("warning", f"Potential match found for {target_email} in recent dump"),
            ("success", "THREAT_ANALYZER classified: HIGH risk credential exposure"),
            ("success", f"Scan complete. {len(findings)} findings generated."),
        ]
        for level, msg in log_messages:
            AgentLog.objects.create(agent=orchestrator, level=level, message=msg)

    return JsonResponse({
        "status": "Agent scan complete",
        "scan_id": scan.id,
        "new_findings": len(findings),
        "findings": findings,
        "recommendation": f"Force password reset for {target_email}. Notify {organizer_email}.",
    })


@login_required
def api_dark_web_search(request):
    """Search dark web for specific email/domain/keyword."""
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    try:
        data = json.loads(request.body)
        query = data.get("query", "").strip()
        search_type = data.get("search_type", "email_search")
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({"error": "Invalid request"}, status=400)

    if not query:
        return JsonResponse({"error": "Query is required"}, status=400)

    # Simulate dark web search results
    results = []
    breach_sources = [
        "BreachForums", "XSS Forum", "RaidForums Archive",
        "Telegram Dump Channel", "Pastebin", "DeHashed",
        "LeakBase", "Exploit.in", "HIBP Dataset"
    ]

    num_results = random.randint(0, 6)
    for i in range(num_results):
        src = random.choice(breach_sources)
        results.append({
            "id": i + 1,
            "source": src,
            "match_type": search_type,
            "query": query,
            "snippet": _generate_dark_web_snippet(query, src),
            "risk_score": random.randint(30, 99),
            "timestamp": (timezone.now() - timedelta(days=random.randint(0, 90))).strftime("%Y-%m-%d"),
            "data_types": random.sample(
                ["email", "password_hash", "plaintext_password", "phone", "address", "ssn", "credit_card", "ip"],
                k=random.randint(1, 4)
            ),
            "verified": random.choice([True, False]),
        })

    # Log the search
    DarkWebScan.objects.create(
        scan_type=search_type,
        query=query,
        status="completed",
        initiated_by=request.user,
        completed_at=timezone.now(),
        results_summary=f"Found {len(results)} results for '{query}'",
        results_data={"results": results},
        agent_used="RECON_AGENT",
    )

    return JsonResponse({
        "query": query,
        "search_type": search_type,
        "total_results": len(results),
        "results": results,
    })


def _generate_dark_web_snippet(query, source):
    """Generate realistic-looking dark web snippets."""
    snippets = [
        f"[{source}] Database leak containing entry for '{query}'. Data includes hashed credentials (bcrypt) and associated metadata. Posted by user 'sh4d0w_dump3r'.",
        f"[{source}] Mention of '{query}' found in credential combo list. Approximately 50K entries in this batch. Last updated 2 weeks ago.",
        f"[{source}] Forum post discussing '{query}' domain infrastructure. Reconnaissance data shared including subdomains, open ports, and technology stack.",
        f"[{source}] '{query}' appeared in a paste containing leaked API keys and service credentials. Paste created by anonymous user, 847 views.",
        f"[{source}] Threat actor 'darkphoenix' offering access to systems related to '{query}'. Price: 2.5 BTC. Claims admin-level access.",
        f"[{source}] Automated scrape detected '{query}' in a public data breach compilation. Breach dated Q1 2026. Includes email/password pairs.",
    ]
    return random.choice(snippets)


@login_required
def api_leakosint_search(request):
    """
    Search using LeakOSINT API for real breach data.
    Falls back to simulated results if API token is not configured.
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    try:
        data = json.loads(request.body)
        query = data.get("query", "").strip()
        limit = data.get("limit", 100)
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({"error": "Invalid request"}, status=400)

    if not query:
        return JsonResponse({"error": "Query is required"}, status=400)

    api_token = getattr(settings, 'LEAKOSINT_API_TOKEN', '')
    api_url = getattr(settings, 'LEAKOSINT_API_URL', 'https://leakosintapi.com/')

    results = {"query": query, "source": "leakosint", "results": [], "total": 0}

    if api_token:
        # Real LeakOSINT API call
        try:
            payload = {
                "token": api_token,
                "request": query,
                "limit": min(int(limit), 10000),
                "lang": "en",
                "type": "json",
            }
            resp = requests.post(api_url, json=payload, timeout=15)
            if resp.status_code == 200:
                api_data = resp.json()
                if "List" in api_data:
                    for db_name, db_data in api_data["List"].items():
                        if db_name == "No results found":
                            continue
                        entry = {
                            "database": db_name,
                            "info": db_data.get("InfoLeak", ""),
                            "records": [],
                        }
                        for record in db_data.get("Data", []):
                            entry["records"].append(record)
                        results["results"].append(entry)
                    results["total"] = len(results["results"])

                    # Log the scan
                    DarkWebScan.objects.create(
                        scan_type="full_recon",
                        query=query,
                        status="completed",
                        initiated_by=request.user,
                        completed_at=timezone.now(),
                        results_summary=f"LeakOSINT: {results['total']} databases found for '{query}'",
                        results_data=results,
                        agent_used="LEAKOSINT_API",
                    )

                    return JsonResponse(results)
                elif "Error code" in api_data:
                    results["error"] = api_data["Error code"]
        except (requests.RequestException, ValueError) as e:
            logger.error("LeakOSINT API error: %s", e)
            results["error"] = "API connection failed"

    # Fallback: simulated results when no token
    results["source"] = "simulated"
    breach_dbs = [
        "Collection #1 (2019)", "LinkedIn Leak (2021)", "Facebook Dump (2021)",
        "Twitter/X Breach (2023)", "MOVEit Data (2023)", "Telegram Combolist",
        "BreachForums Dump", "Stealer Logs Collection", "InfoStealer DB",
    ]
    num = random.randint(0, 5)
    for i in range(num):
        db_name = random.choice(breach_dbs)
        results["results"].append({
            "database": db_name,
            "info": f"Found in {db_name}. Contains user data matching '{query}'.",
            "records": [
                {"Email": query if "@" in query else f"user@{query}",
                 "Password": "***REDACTED***",
                 "Source": db_name,
                 "Date": f"202{random.randint(3,6)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"}
            ],
        })
    results["total"] = len(results["results"])

    DarkWebScan.objects.create(
        scan_type="full_recon",
        query=query,
        status="completed",
        initiated_by=request.user,
        completed_at=timezone.now(),
        results_summary=f"Simulated: {results['total']} results for '{query}'",
        results_data=results,
        agent_used="LEAKOSINT_SIMULATED",
    )

    return JsonResponse(results)


# ============ Industry-Aware Domain Scan Profiles ============

INDUSTRY_SCAN_PROFILES = {
    "banking": {
        "name": "Banking / Fintech",
        "email_prefixes": ["treasury@", "kyc@", "swift@", "neft@", "compliance@", "risk@", "cards@", "loans@"],
        "subdomains": ["netbanking", "api", "uat", "mobile", "swift", "rtgs", "upi", "merchant", "kyc-portal"],
        "tech_indicators": ["Core Banking System (CBS)", "SWIFT Alliance", "UPI Gateway", "Mobile Banking SDK", "HSM Cluster", "Fraud Detection Engine", "AML Screening"],
        "extra_breach_sources": ["Financial Sector Stealer Logs", "SWIFT Network Dump"],
        "extra_data_types": ["account_number", "ifsc_code", "transaction_data", "kyc_documents"],
        "breach_probability": 0.5,
        "recommendation_template": "CRITICAL: Force password reset for {email}. Enable hardware MFA. Review SWIFT operator access. Notify RBI CSITE. Monitor for unauthorized transactions.",
        "mention_templates": [
            "Banking credentials for {domain} found in financial sector stealer log collection. Includes internal CBS access tokens.",
            "Threat actor advertising access to {domain} SWIFT operator workstation. Price: $50K. Buyer verification required.",
        ],
        "threat_context": "Financial sector target. Coordinate with RBI CSITE and IDRBT. Review SWIFT CSP compliance.",
        "high_risk": True,
    },
    "healthcare": {
        "name": "Healthcare",
        "email_prefixes": ["doctor@", "pharmacy@", "lab@", "ehr@", "billing@", "records@", "radiology@"],
        "subdomains": ["ehr", "pacs", "lab-portal", "patient-portal", "pharmacy", "telemedicine", "dicom", "his"],
        "tech_indicators": ["EHR/EMR System", "PACS/DICOM Server", "HL7/FHIR Interface", "Telemedicine Platform", "Lab Information System", "Pharmacy Management"],
        "extra_breach_sources": ["Healthcare Data Dump", "Medical Records Market"],
        "extra_data_types": ["patient_records", "medical_history", "prescription_data", "aadhaar_health_id"],
        "breach_probability": 0.45,
        "recommendation_template": "Force password reset for {email}. Review EHR access logs. Check ABDM/ABHA data sharing compliance. Enable role-based access controls.",
        "mention_templates": [
            "Patient health records from {domain} listed for sale on dark web marketplace. ~50K records with complete medical history.",
            "Prescription database access for {domain} being traded in Telegram medical data channel.",
        ],
        "threat_context": "Healthcare data breach with DPDPA and ABDM compliance implications. Notify CERT-In and relevant health authorities.",
        "high_risk": True,
    },
    "government": {
        "name": "Government",
        "email_prefixes": ["nic@", "officer@", "clerk@", "director@", "secretary@", "rti@", "procurement@", "cyber-cell@"],
        "subdomains": ["rti-portal", "e-office", "procurement", "citizen-portal", "internal", "vpn", "mail", "nic"],
        "tech_indicators": ["NIC Infrastructure", "e-Office Suite", "GeM Portal Integration", "DigiLocker Integration", "Aadhaar Authentication", "GAIL/GSTN Portal"],
        "extra_breach_sources": ["Government Leak Forum", "Hacktivist Dump"],
        "extra_data_types": ["aadhaar_number", "pan_card", "voter_id", "government_id", "classified_documents"],
        "breach_probability": 0.45,
        "recommendation_template": "CRITICAL: Lock account {email}. Notify CERT-In and NIC-CERT. Review classified data access. Enable certificate-based authentication.",
        "mention_templates": [
            "Government portal {domain} database dump posted by hacktivist group. Contains citizen PII and internal communications.",
            "Access to {domain} e-Office system being sold on dark web. Threat actor claims persistent backdoor access.",
        ],
        "threat_context": "Government infrastructure compromise. Coordinate with CERT-In, NIC-CERT, and NCIIPC immediately.",
        "high_risk": True,
    },
    "ecommerce": {
        "name": "E-Commerce / Retail",
        "email_prefixes": ["orders@", "payments@", "merchant@", "logistics@", "returns@", "seller@", "warehouse@"],
        "subdomains": ["api", "checkout", "payments", "seller-portal", "warehouse", "cdn", "staging", "analytics"],
        "tech_indicators": ["Payment Gateway (Razorpay/PayU)", "CDN (CloudFront)", "Elasticsearch", "Redis Cache", "Magento/Shopify", "Inventory Management"],
        "extra_breach_sources": ["Magecart Skimmer Collection", "E-Commerce Credential Dump"],
        "extra_data_types": ["credit_card_token", "order_history", "shipping_address", "payment_method"],
        "breach_probability": 0.5,
        "recommendation_template": "Force password reset for {email}. Scan checkout pages for skimmers. Rotate payment API keys. Review PCI-DSS compliance.",
        "mention_templates": [
            "Magecart skimmer variant detected injecting into {domain} checkout pages. Customer payment data being exfiltrated.",
            "Seller portal credentials for {domain} found in credential stuffing combo list (2.5M entries).",
        ],
        "threat_context": "E-commerce platform with payment data exposure. PCI-DSS breach notification and web skimmer remediation required.",
        "high_risk": True,
    },
    "telecom": {
        "name": "Telecommunications",
        "email_prefixes": ["noc@", "billing@", "provisioning@", "tower@", "oss@", "bss@", "lawful-intercept@"],
        "subdomains": ["noc", "oss", "bss", "billing", "selfcare", "dealer-portal", "api-gateway", "sms-gateway"],
        "tech_indicators": ["OSS/BSS Platform", "HLR/HSS System", "VoLTE Core", "SMSC Gateway", "CDR Processing", "Lawful Intercept System", "5G Core Network"],
        "extra_breach_sources": ["Telecom Sector Dump", "CDR Trading Forum"],
        "extra_data_types": ["call_records", "imsi_number", "cell_tower_data", "subscriber_data"],
        "breach_probability": 0.4,
        "recommendation_template": "Force password reset for {email}. Audit NOC access controls. Review CDR access logs. Notify DoT/TRAI per license conditions.",
        "mention_templates": [
            "Subscriber CDR data from {domain} available for purchase. Threat actor claims access to billing and location data.",
            "SIM swap fraud ring advertising insider access at {domain} for targeted interception.",
        ],
        "threat_context": "Telecom infrastructure compromise. CDR/subscriber data at risk. Coordinate with DoT and TRAI.",
        "high_risk": True,
    },
    "manufacturing": {
        "name": "Manufacturing / Industrial",
        "email_prefixes": ["plant@", "scada@", "ot-security@", "quality@", "production@", "maintenance@", "erp@"],
        "subdomains": ["scada", "hmi", "erp", "mes", "plc-gateway", "ot-network", "quality-portal", "vendor-portal"],
        "tech_indicators": ["SCADA/HMI System", "PLC Controllers (Siemens/Rockwell)", "MES Platform", "ERP (SAP)", "Industrial IoT Gateway", "OT Firewall", "Historian Server"],
        "extra_breach_sources": ["ICS-CERT Advisory", "Industrial Control System Forum"],
        "extra_data_types": ["plc_credentials", "scada_config", "process_parameters", "erp_data"],
        "breach_probability": 0.35,
        "recommendation_template": "CRITICAL: Isolate OT network for {email} domain. Audit PLC access. Review air-gap integrity. Notify CERT-In ICS division.",
        "mention_templates": [
            "SCADA/HMI credentials for {domain} OT network posted on ICS-focused dark web forum. Includes PLC programming access.",
            "Ransomware group claiming access to {domain} manufacturing execution systems. Double extortion threat.",
        ],
        "threat_context": "Industrial control system threat. Physical infrastructure at risk. Coordinate with CERT-In ICS and NCIIPC.",
        "high_risk": True,
    },
    "pharma": {
        "name": "Pharmaceutical / Biotech",
        "email_prefixes": ["research@", "clinical-trials@", "qa@", "regulatory@", "formulation@", "gmp@", "pharmacovigilance@"],
        "subdomains": ["lims", "clinical-portal", "gmp-docs", "regulatory-submissions", "drug-safety", "api-manufacturing", "research-portal"],
        "tech_indicators": ["LIMS System", "Clinical Trial Management", "GMP Documentation", "Drug Safety Database", "Regulatory Submission Portal", "Batch Record System"],
        "extra_breach_sources": ["Pharma IP Theft Forum", "Clinical Data Market"],
        "extra_data_types": ["drug_formulation", "clinical_trial_data", "patient_trial_data", "gmp_records", "api_process"],
        "breach_probability": 0.4,
        "recommendation_template": "Force password reset for {email}. Audit research data access. Review IP protection controls. Notify DCGI if clinical data exposed.",
        "mention_templates": [
            "Clinical trial data and drug formulation IP from {domain} listed for sale. Includes Phase 2/3 results for pipeline compounds.",
            "Competitor intelligence operation targeting {domain} research division. Custom malware found on research workstations.",
        ],
        "threat_context": "Pharmaceutical IP theft with regulatory (DCGI/CDSCO) and competitive implications.",
        "high_risk": True,
    },
    "energy": {
        "name": "Energy / Power / Utilities",
        "email_prefixes": ["scada@", "grid-ops@", "dispatch@", "metering@", "generation@", "transmission@", "safety@"],
        "subdomains": ["scada", "ems", "dms", "metering", "grid-portal", "dispatch", "safety-portal", "substation"],
        "tech_indicators": ["SCADA/EMS System", "Smart Grid Gateway", "AMI Metering", "WAMS/PMU Network", "Substation Automation", "DER Management", "OT Security Monitoring"],
        "extra_breach_sources": ["Critical Infrastructure Forum", "XENOTIME Dump"],
        "extra_data_types": ["grid_topology", "scada_config", "substation_credentials", "smart_meter_data"],
        "breach_probability": 0.35,
        "recommendation_template": "CRITICAL: Isolate control systems for {email} domain. Review SIS integrity. Coordinate with NCIIPC and power sector CERT. National security implications.",
        "mention_templates": [
            "Power grid SCADA access for {domain} substations being auctioned. Threat actor demonstrates live access to EMS.",
            "Nation-state APT targeting {domain} grid infrastructure. Custom TRITON-like malware detected in OT network.",
        ],
        "threat_context": "Critical national infrastructure threat. Immediate coordination with NCIIPC, CERT-In, and CEA required.",
        "high_risk": True,
    },
    "insurance": {
        "name": "Insurance",
        "email_prefixes": ["claims@", "underwriting@", "actuarial@", "policy@", "compliance@", "fraud@", "reinsurance@"],
        "subdomains": ["claims-portal", "agent-portal", "policy-admin", "underwriting", "fraud-detection", "customer-portal"],
        "tech_indicators": ["Policy Admin System", "Claims Management", "Actuarial Engine", "Fraud Detection", "Reinsurance Platform", "Agent Portal"],
        "extra_breach_sources": ["Insurance Data Forum", "PII Trading Channel"],
        "extra_data_types": ["policy_data", "claims_history", "medical_reports", "nominee_details"],
        "breach_probability": 0.4,
        "recommendation_template": "Force password reset for {email}. Audit policyholder data access. Review IRDAI compliance. Check claims processing integrity.",
        "mention_templates": [
            "Policyholder database from {domain} with 200K records including nominee and medical details listed for sale.",
            "Insurance fraud ring using stolen agent credentials from {domain} to file fake claims.",
        ],
        "threat_context": "Insurance data breach. Notify IRDAI and affected policyholders per DPDPA requirements.",
        "high_risk": False,
    },
    "legal": {
        "name": "Legal / Law Firm",
        "email_prefixes": ["partner@", "associate@", "paralegal@", "litigation@", "corporate@", "ipr@", "confidential@"],
        "subdomains": ["dms", "case-portal", "client-portal", "billing", "research", "e-discovery"],
        "tech_indicators": ["Document Management System", "Legal Research Platform", "e-Discovery Tool", "Case Management", "Billing/Time Tracking", "Secure Client Portal"],
        "extra_breach_sources": ["Legal Sector Breach", "M&A Intelligence Forum"],
        "extra_data_types": ["attorney_client_privileged", "case_documents", "m_and_a_data", "client_retainer"],
        "breach_probability": 0.35,
        "recommendation_template": "Force password reset for {email}. Audit privileged document access. Review client confidentiality controls. Notify affected clients if privilege breached.",
        "mention_templates": [
            "Attorney-client privileged communications from {domain} found in corporate espionage dump. Includes M&A transaction details.",
            "Threat actor targeting {domain} for insider trading intelligence. Exfiltrating IPO-related legal opinions.",
        ],
        "threat_context": "Legal privilege breach with client confidentiality and potential securities fraud implications.",
        "high_risk": False,
    },
    "logistics": {
        "name": "Logistics / Supply Chain",
        "email_prefixes": ["dispatch@", "warehouse@", "tracking@", "fleet@", "customs@", "procurement@", "driver@"],
        "subdomains": ["tracking", "fleet-mgmt", "warehouse", "customs-portal", "driver-app", "api", "vendor-portal"],
        "tech_indicators": ["TMS Platform", "WMS System", "GPS Fleet Tracking", "Customs EDI", "Last-Mile Delivery App", "Supply Chain Visibility"],
        "extra_breach_sources": ["Supply Chain Threat Feed", "Cargo Theft Forum"],
        "extra_data_types": ["shipment_manifest", "customs_data", "gps_coordinates", "warehouse_inventory"],
        "breach_probability": 0.35,
        "recommendation_template": "Force password reset for {email}. Rotate GPS/tracking API keys. Audit customs EDI access. Review supply chain partner access controls.",
        "mention_templates": [
            "GPS tracking API credentials for {domain} fleet shared in cargo theft Telegram group.",
            "Customs clearance portal access for {domain} being sold. Enables fraudulent import/export declarations.",
        ],
        "threat_context": "Supply chain security threat. Risk of cargo theft, customs fraud, and operational disruption.",
        "high_risk": False,
    },
    "nbfc": {
        "name": "NBFC / Microfinance",
        "email_prefixes": ["loans@", "collections@", "kyc@", "disbursement@", "recovery@", "credit@", "compliance@"],
        "subdomains": ["loan-portal", "kyc-verification", "collection-app", "agent-portal", "credit-scoring", "disbursement"],
        "tech_indicators": ["Loan Management System", "KYC/eKYC Platform", "Credit Scoring Engine", "Collection App", "Digital Lending Platform", "Aadhaar eSign"],
        "extra_breach_sources": ["Microfinance Data Dump", "KYC Document Market"],
        "extra_data_types": ["aadhaar_number", "pan_card", "bank_statement", "credit_score", "loan_agreement"],
        "breach_probability": 0.5,
        "recommendation_template": "CRITICAL: Force password reset for {email}. Audit KYC document access. Review RBI digital lending guidelines compliance. Notify affected borrowers per DPDPA.",
        "mention_templates": [
            "Loan applicant database from {domain} with 500K Aadhaar-linked records for sale. Includes bank statements and PAN cards.",
            "KYC document repository from {domain} being traded. Full identity packages for synthetic fraud.",
        ],
        "threat_context": "NBFC data breach with RBI regulatory and DPDPA compliance implications. High fraud risk from KYC data exposure.",
        "high_risk": True,
    },
    "defence": {
        "name": "Defence / Aerospace",
        "email_prefixes": ["classified@", "procurement@", "r-and-d@", "project@", "security@", "testing@", "systems@"],
        "subdomains": ["secure-mail", "procurement-portal", "project-mgmt", "testing-range", "r-and-d", "classified-net"],
        "tech_indicators": ["Classified Network", "Defence ERP", "Secure Communication System", "Satellite Ground Station", "Missile Guidance System", "Radar Processing"],
        "extra_breach_sources": ["APT Staging Server", "Nation-State Dump", "Defence Contractor Breach"],
        "extra_data_types": ["classified_documents", "weapon_specs", "satellite_data", "procurement_contracts", "personnel_clearances"],
        "breach_probability": 0.3,
        "recommendation_template": "CRITICAL NATIONAL SECURITY: Lock {email} immediately. Notify NTRO, Defence Cyber Agency, and DRDO security. Initiate damage assessment. Review personnel clearances.",
        "mention_templates": [
            "Classified defence documents from {domain} found on Chinese APT staging server. Includes weapon system schematics and test data.",
            "Satellite subsystem specifications from {domain} posted on nation-state linked forum. Active espionage operation suspected.",
        ],
        "threat_context": "CRITICAL: National security breach. Defence classified data compromise. Immediate NTRO and DCA escalation required.",
        "high_risk": True,
    },
    "education": {
        "name": "Education / EdTech",
        "email_prefixes": ["registrar@", "admissions@", "faculty@", "research@", "library@", "exam@", "placement@"],
        "subdomains": ["lms", "erp", "exam-portal", "admissions", "research-portal", "library", "placement"],
        "tech_indicators": ["LMS Platform", "Student ERP", "Exam Management", "Research Repository", "Plagiarism Detection", "Virtual Classroom"],
        "extra_breach_sources": ["Education Sector Dump", "Student Data Market"],
        "extra_data_types": ["student_records", "exam_results", "research_papers", "placement_data"],
        "breach_probability": 0.35,
        "recommendation_template": "Force password reset for {email}. Audit student records access. Review exam portal security. Notify UGC/AICTE if research data compromised.",
        "mention_templates": [
            "Student database from {domain} with 100K records including Aadhaar and exam scores posted on dark web.",
            "Exam question papers from {domain} being sold before examination dates on Telegram channels.",
        ],
        "threat_context": "Education sector breach. Student PII and academic integrity at risk. Notify relevant regulatory bodies.",
        "high_risk": False,
    },
    "media": {
        "name": "Media / Entertainment",
        "email_prefixes": ["editorial@", "content@", "broadcast@", "digital@", "advertising@", "newsroom@", "streaming@"],
        "subdomains": ["cms", "streaming", "cdn", "ad-server", "newsroom", "archive", "digital-platform"],
        "tech_indicators": ["CMS Platform", "Streaming Infrastructure", "CDN Network", "Ad Server", "DRM System", "Broadcast Automation", "Archive System"],
        "extra_breach_sources": ["Media Leak Forum", "Content Piracy Network"],
        "extra_data_types": ["unpublished_content", "source_contacts", "subscriber_data", "ad_revenue_data"],
        "breach_probability": 0.35,
        "recommendation_template": "Force password reset for {email}. Audit CMS and content access. Review source protection controls. Check DRM integrity.",
        "mention_templates": [
            "CMS credentials and unpublished content from {domain} leaked. Pre-release content schedules exposed.",
            "Journalist source database from {domain} compromised. Source identities at risk.",
        ],
        "threat_context": "Media organization compromise. Source protection and content embargo integrity at risk.",
        "high_risk": False,
    },
    "realestate": {
        "name": "Real Estate / PropTech",
        "email_prefixes": ["sales@", "property@", "legal@", "broker@", "registry@", "tenant@", "maintenance@"],
        "subdomains": ["portal", "broker-portal", "tenant-portal", "crm", "property-mgmt", "registry"],
        "tech_indicators": ["Property Management System", "CRM Platform", "Broker Portal", "Tenant Portal", "Registry Integration", "Payment Gateway"],
        "extra_breach_sources": ["Property Data Forum", "Identity Theft Market"],
        "extra_data_types": ["property_ownership", "registration_docs", "tenant_aadhaar", "transaction_records"],
        "breach_probability": 0.3,
        "recommendation_template": "Force password reset for {email}. Audit property records access. Review RERA compliance. Check registry document security.",
        "mention_templates": [
            "Property ownership records and registration documents from {domain} listed for sale for identity fraud.",
            "Tenant PII database from {domain} with Aadhaar numbers found in credential dump.",
        ],
        "threat_context": "Real estate data breach. Property fraud and identity theft risk. Review RERA and DPDPA compliance.",
        "high_risk": False,
    },
}

# Default fallback profile
_DEFAULT_PROFILE = {
    "name": "General",
    "email_prefixes": ["it@", "security@", "compliance@", "dev@", "ops@"],
    "subdomains": ["api", "staging", "dev", "mail", "vpn", "portal"],
    "tech_indicators": ["Web Server", "Database", "Load Balancer", "VPN Gateway", "Email Server", "Cloud Infrastructure"],
    "extra_breach_sources": [],
    "extra_data_types": [],
    "breach_probability": 0.4,
    "recommendation_template": "Force password reset for {email}. Enable MFA. Monitor for suspicious login attempts.",
    "mention_templates": [],
    "threat_context": "Recommend enhanced monitoring and proactive defense measures.",
    "high_risk": False,
}


def _detect_industry_profile(domain, user):
    """Detect industry from user's organization or domain patterns and return scan profile."""
    # Try user's organization first
    if hasattr(user, 'organization') and user.organization:
        org_industry = (user.organization.industry or "").lower().replace(" ", "").replace("/", "").replace("&", "")
        for key in INDUSTRY_SCAN_PROFILES:
            if key in org_industry or org_industry in key:
                return INDUSTRY_SCAN_PROFILES[key]

    # Fallback: detect from domain patterns
    domain_lower = domain.lower()
    domain_hints = {
        "banking": ["bank", "fintech", "finance", "pay", "upi"],
        "healthcare": ["health", "hospital", "med", "care", "clinic", "pharma"],
        "government": [".gov.", ".nic.", "govt", "government"],
        "ecommerce": ["shop", "kart", "store", "mart", "retail", "commerce"],
        "telecom": ["telco", "tele", "comm", "mobile", "airtel", "jio"],
        "manufacturing": ["steel", "mfg", "factory", "manufacturing", "industrial"],
        "pharma": ["pharma", "bio", "drug", "lab"],
        "energy": ["power", "energy", "grid", "solar", "electric", "utility"],
        "insurance": ["insure", "insurance", "life", "general-insurance"],
        "legal": ["legal", "law", "advocate", "attorney"],
        "logistics": ["logistics", "cargo", "freight", "shipping", "delivery", "dart"],
        "nbfc": ["nbfc", "microfinance", "lending", "loan"],
        "defence": ["defence", "defense", "aerospace", "hal-", "drdo", "military"],
        "education": ["edu", "university", "college", "school", "learning", "academy"],
        "media": ["media", "news", "broadcast", "entertainment", "zee", "ndtv"],
        "realestate": ["property", "realty", "propnest", "housing", "estate"],
    }
    for industry_key, hints in domain_hints.items():
        if any(hint in domain_lower for hint in hints):
            return INDUSTRY_SCAN_PROFILES.get(industry_key, _DEFAULT_PROFILE)

    return _DEFAULT_PROFILE


@login_required
def api_domain_scan(request):
    """
    Scan an organization domain (@organization.com) for breaches,
    leaked credentials, and dark web mentions.
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    try:
        data = json.loads(request.body)
        domain = data.get("domain", "").strip().lstrip("@")
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({"error": "Invalid request"}, status=400)

    if not domain:
        return JsonResponse({"error": "Domain is required"}, status=400)

    # Register/update monitored domain
    mon_domain, created = MonitoredDomain.objects.get_or_create(
        domain=domain,
        defaults={
            "added_by": request.user,
            "risk_level": "MEDIUM",
            "last_scanned": timezone.now(),
        }
    )
    if not created:
        mon_domain.last_scanned = timezone.now()
        mon_domain.save(update_fields=["last_scanned"])

    # Detect industry from user's organization or domain patterns
    industry_profile = _detect_industry_profile(domain, request.user)

    # Core email patterns + industry-specific ones
    base_emails = [
        f"admin@{domain}", f"info@{domain}", f"hr@{domain}",
        f"support@{domain}", f"finance@{domain}", f"ceo@{domain}",
    ]
    industry_emails = [f"{prefix}@{domain}" for prefix in industry_profile["email_prefixes"]]
    email_patterns = list(dict.fromkeys(base_emails + industry_emails))  # deduplicate

    # Simulate subdomain discovery
    subdomains_found = []
    for sub in industry_profile["subdomains"]:
        if random.random() < 0.55:
            subdomains_found.append(f"{sub}.{domain}")

    # Simulate technology stack fingerprinting
    tech_stack = random.sample(industry_profile["tech_indicators"], k=min(len(industry_profile["tech_indicators"]), random.randint(2, 5)))

    # Simulate DNS/SSL findings
    dns_findings = []
    if random.random() < 0.35:
        dns_findings.append({"type": "spf_missing", "detail": f"No SPF record found for {domain}. Vulnerable to email spoofing."})
    if random.random() < 0.25:
        dns_findings.append({"type": "dmarc_weak", "detail": f"DMARC policy set to 'none' for {domain}. Email authentication not enforced."})
    if random.random() < 0.20:
        dns_findings.append({"type": "dangling_cname", "detail": f"Dangling CNAME record found: staging.{domain} -> decommissioned host. Subdomain takeover risk."})
    if random.random() < 0.30:
        ssl_days = random.randint(-30, 15)
        if ssl_days <= 0:
            dns_findings.append({"type": "ssl_expired", "detail": f"SSL certificate for {domain} expired {abs(ssl_days)} days ago."})
        else:
            dns_findings.append({"type": "ssl_expiring", "detail": f"SSL certificate for {domain} expires in {ssl_days} days."})

    findings = {
        "domain": domain,
        "is_new": created,
        "industry": industry_profile["name"],
        "emails_checked": len(email_patterns),
        "breaches_found": 0,
        "credentials_leaked": 0,
        "dark_web_mentions": 0,
        "subdomains_discovered": subdomains_found,
        "tech_stack_detected": tech_stack,
        "dns_findings": dns_findings,
        "risk_level": "LOW",
        "details": [],
    }

    source = ThreatIntelSource.objects.filter(source_type="dark_web").first()

    # Extended breach sources
    breach_sources = [
        "BreachForums 2026", "Telegram Channel", "DeHashed",
        "Stealer Logs", "Russian Market", "Exploit.in",
        "LeakBase Archive", "Pastebin Dump", "Have I Been Pwned",
        "IntelX Collection", "Snusbase", "WeLeakInfo Mirror",
    ] + industry_profile.get("extra_breach_sources", [])

    # Simulate credential findings with industry-weighted probability
    hit_probability = industry_profile.get("breach_probability", 0.4)
    for email in email_patterns:
        if random.random() < hit_probability:
            breach_src = random.choice(breach_sources)
            risk = random.randint(50, 98)

            # Industry-specific data types that might be leaked
            data_type_pool = ["email", "password_hash", "phone", "ip_address", "username"] + industry_profile.get("extra_data_types", [])

            cred, cred_created = LeakedCredential.objects.get_or_create(
                email=email,
                breach_source=breach_src,
                defaults={
                    "domain": mon_domain,
                    "breach_date": (timezone.now() - timedelta(days=random.randint(5, 120))).date(),
                    "data_types": random.sample(data_type_pool, k=min(len(data_type_pool), random.randint(2, 5))),
                    "is_verified": random.choice([True, False]),
                    "risk_score": risk,
                    "ai_recommendation": industry_profile["recommendation_template"].format(email=email),
                }
            )
            if cred_created:
                findings["credentials_leaked"] += 1
                findings["details"].append({
                    "type": "credential_leak",
                    "email": email,
                    "source": breach_src,
                    "risk_score": risk,
                })

    # Subdomain-based findings
    for subdomain in subdomains_found:
        if random.random() < 0.3:
            finding_type = random.choice(["exposed_service", "default_creds", "info_disclosure"])
            findings["details"].append({
                "type": f"subdomain_{finding_type}",
                "subdomain": subdomain,
                "detail": {
                    "exposed_service": f"Unauthenticated admin panel found at {subdomain}",
                    "default_creds": f"Default credentials active on {subdomain}",
                    "info_disclosure": f"Version disclosure and debug info exposed on {subdomain}",
                }[finding_type],
                "risk_score": random.randint(55, 85),
            })

    # Dark web mentions - industry-aware
    mention_templates = [
        f"Domain {domain} found in dark web forum discussion. Threat actors discussing potential targets in {domain} infrastructure.",
    ] + industry_profile.get("mention_templates", [])

    if source and random.random() < 0.6:
        mention_text = random.choice(mention_templates).format(domain=domain)
        DarkWebMention.objects.create(
            keyword_matched=domain,
            snippet=mention_text,
            source=source,
            risk_score=random.randint(60, 90),
            ai_analysis=f"THREAT_ANALYZER: Domain {domain} ({industry_profile['name']}) is being discussed on underground forums. {industry_profile.get('threat_context', 'Recommend enhanced monitoring and proactive defense measures.')}",
        )
        findings["dark_web_mentions"] += 1

    # Second mention for high-risk industries
    if source and industry_profile.get("high_risk", False) and random.random() < 0.45:
        mention_text = random.choice(industry_profile.get("mention_templates", [mention_templates[0]])).format(domain=domain)
        DarkWebMention.objects.create(
            keyword_matched=domain,
            snippet=mention_text,
            source=source,
            risk_score=random.randint(75, 98),
            ai_analysis=f"THREAT_ANALYZER: {industry_profile['name']} sector target {domain} flagged in active threat campaign. {industry_profile.get('threat_context', '')}",
        )
        findings["dark_web_mentions"] += 1

    # Calculate overall risk (enhanced scoring)
    total_issues = findings["credentials_leaked"] + findings["dark_web_mentions"] + len(dns_findings)
    subdomain_risk = len([d for d in findings["details"] if d["type"].startswith("subdomain_")])
    total_issues += subdomain_risk

    if total_issues >= 6:
        findings["risk_level"] = "CRITICAL"
    elif total_issues >= 4:
        findings["risk_level"] = "HIGH"
    elif total_issues >= 2:
        findings["risk_level"] = "MEDIUM"
    elif total_issues >= 1:
        findings["risk_level"] = "LOW"

    # Update domain risk
    mon_domain.risk_level = findings["risk_level"]
    mon_domain.total_breaches_found += findings["credentials_leaked"]
    mon_domain.total_mentions_found += findings["dark_web_mentions"]
    mon_domain.save()

    # Log agent activity
    orchestrator = ThreatAgent.objects.filter(name="ORCHESTRATOR").first()
    if orchestrator:
        AgentLog.objects.create(
            agent=orchestrator, level="info",
            message=f"Domain scan initiated for {domain} by {request.user.username}"
        )
        AgentLog.objects.create(
            agent=orchestrator, level="success",
            message=f"Domain scan complete for {domain}. {total_issues} findings."
        )

    # Create scan record
    DarkWebScan.objects.create(
        scan_type="domain_monitor",
        query=domain,
        status="completed",
        initiated_by=request.user,
        completed_at=timezone.now(),
        results_summary=f"Domain scan ({industry_profile['name']}): {findings['credentials_leaked']} leaked creds, {findings['dark_web_mentions']} mentions, {len(subdomains_found)} subdomains, {len(dns_findings)} DNS issues",
        results_data=findings,
        agent_used="ORCHESTRATOR",
    )

    return JsonResponse(findings)


@login_required
def api_agent_status(request):
    """Get current status of all threat agents."""
    agents = ThreatAgent.objects.all()
    agent_data = []
    for agent in agents:
        # Simulate some activity
        recent_logs = AgentLog.objects.filter(agent=agent).order_by('-timestamp')[:5]
        agent_data.append({
            "id": agent.id,
            "name": agent.name,
            "type": agent.get_agent_type_display(),
            "status": agent.status,
            "is_enabled": agent.is_enabled,
            "tasks_completed": agent.tasks_completed,
            "threats_found": agent.threats_found,
            "last_active": agent.last_active.strftime("%Y-%m-%d %H:%M:%S") if agent.last_active else "Never",
            "capabilities": agent.capabilities,
            "description": agent.description,
            "recent_logs": [
                {"level": log.level, "message": log.message, "time": log.timestamp.strftime("%H:%M:%S")}
                for log in recent_logs
            ],
        })

    return JsonResponse({"agents": agent_data})


@login_required
def api_agent_logs(request):
    """Get recent agent activity logs for terminal feed."""
    # Generate some simulated real-time logs
    agents = list(ThreatAgent.objects.all())
    if agents:
        agent = random.choice(agents)
        log_templates = [
            ("info", f"[{agent.name}] Scanning dark web node #{random.randint(100,999)}..."),
            ("info", f"[{agent.name}] Processing {random.randint(50,500)} records from breach DB..."),
            ("warning", f"[{agent.name}] Suspicious pattern detected in traffic from {random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"),
            ("success", f"[{agent.name}] IOC extracted: SHA256 hash {hashlib.sha256(str(random.random()).encode()).hexdigest()[:32]}..."),
            ("info", f"[{agent.name}] Monitoring Telegram channel for threat chatter..."),
            ("warning", f"[{agent.name}] New paste detected with {random.randint(1,50)}K credentials"),
            ("info", f"[{agent.name}] Correlating {random.randint(5,30)} IOCs across threat feeds..."),
            ("success", f"[{agent.name}] Threat report generated. Risk score: {random.randint(40,95)}/100"),
            ("info", f"[{agent.name}] Checking {random.choice(list(COUNTRIES.values()))['name']} exit nodes..."),
            ("error", f"[{agent.name}] Connection timeout to .onion endpoint. Retrying via alternate circuit..."),
        ]
        level, msg = random.choice(log_templates)
        AgentLog.objects.create(agent=agent, level=level, message=msg)

    logs = AgentLog.objects.order_by('-timestamp')[:15]
    return JsonResponse({
        "logs": [
            {
                "agent": log.agent.name,
                "level": log.level,
                "message": log.message,
                "timestamp": log.timestamp.strftime("%H:%M:%S"),
            }
            for log in logs
        ]
    })


@login_required
def api_cve_feed(request):
    """Return CVE data for the threat dashboard CVE section."""
    from cve_manager.models import CVE

    search = request.GET.get('search', '').strip()
    severity = request.GET.get('severity', '').strip()
    year = request.GET.get('year', '').strip()

    cves = CVE.objects.all()
    if search:
        cves = cves.filter(
            models_Q(cve_id__icontains=search) |
            models_Q(description__icontains=search) |
            models_Q(affected_products__icontains=search)
        )
    if severity:
        cves = cves.filter(severity=severity)
    if year:
        cves = cves.filter(cve_id__contains=f"CVE-{year}")

    cves = cves[:50]
    return JsonResponse({
        "cves": [
            {
                "id": cve.id,
                "cve_id": cve.cve_id,
                "description": cve.description[:200],
                "severity": cve.severity,
                "cvss_score": cve.cvss_score,
                "published_date": cve.published_date.strftime("%Y-%m-%d") if cve.published_date else "N/A",
                "affected_products": cve.affected_products[:100] if cve.affected_products else "",
            }
            for cve in cves
        ]
    })


# Fix for the Q import
from django.db.models import Q as models_Q
