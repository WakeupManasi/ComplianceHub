"""
Management command to seed the threat intelligence platform with:
- 60+ realistic CVEs (2023-2026)
- Test user accounts with proper documentation
- Dark web monitoring demo data
- Agent task history
"""
import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed threat intelligence platform with CVEs (2023-2026), test accounts, and demo data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Seeding threat intelligence data...'))
        self._seed_test_accounts()
        self._seed_cves()
        self._seed_dark_web_data()
        self._seed_agent_history()
        self.stdout.write(self.style.SUCCESS('All data seeded successfully!'))

    def _seed_test_accounts(self):
        from core.models import Organization

        org, _ = Organization.objects.get_or_create(
            name="CyberShield Corp",
            defaults={
                "industry": "Cybersecurity",
                "country": "India",
                "company_size": "50-200",
                "onboarding_completed": True,
                "risk_score": 72,
            }
        )

        test_accounts = [
            {
                "username": "admin_demo",
                "email": "admin@cybershield.io",
                "password": "CyberAdmin@2026",
                "first_name": "Arjun",
                "last_name": "Sharma",
                "role": "super_admin",
            },
            {
                "username": "analyst_demo",
                "email": "analyst@cybershield.io",
                "password": "Analyst@2026",
                "first_name": "Priya",
                "last_name": "Patel",
                "role": "compliance_manager",
            },
            {
                "username": "auditor_demo",
                "email": "auditor@cybershield.io",
                "password": "Auditor@2026",
                "first_name": "Rahul",
                "last_name": "Verma",
                "role": "auditor",
            },
            {
                "username": "vendor_demo",
                "email": "vendor@thirdparty.io",
                "password": "Vendor@2026",
                "first_name": "Sarah",
                "last_name": "Chen",
                "role": "vendor_user",
            },
            {
                "username": "soc_lead",
                "email": "soc@cybershield.io",
                "password": "SOCLead@2026",
                "first_name": "Vikram",
                "last_name": "Singh",
                "role": "client_admin",
            },
        ]

        for acc in test_accounts:
            role = acc.pop("role")
            pwd = acc.pop("password")
            user, created = User.objects.get_or_create(
                username=acc["username"],
                defaults={**acc, "organization": org, "role": role}
            )
            if created:
                user.set_password(pwd)
                user.save()
                self.stdout.write(f'  Created user: {user.username} ({user.email})')
            else:
                self.stdout.write(f'  User exists: {user.username}')

        # Additional industry organizations and accounts
        industries = [
            {
                "org_name": "Bharat National Bank",
                "industry": "Banking & Finance",
                "country": "India",
                "accounts": [
                    {"username": "bank_admin", "email": "admin@bharatbank.co.in", "password": "BankAdmin@2026", "first_name": "Rajesh", "last_name": "Gupta", "role": "super_admin"},
                    {"username": "bank_analyst", "email": "analyst@bharatbank.co.in", "password": "BankAnalyst@2026", "first_name": "Neha", "last_name": "Reddy", "role": "compliance_manager"},
                ],
            },
            {
                "org_name": "MedCare Hospitals",
                "industry": "Healthcare",
                "country": "India",
                "accounts": [
                    {"username": "health_admin", "email": "admin@medcare.health", "password": "HealthAdmin@2026", "first_name": "Dr. Anil", "last_name": "Kumar", "role": "super_admin"},
                    {"username": "health_compliance", "email": "compliance@medcare.health", "password": "HealthComp@2026", "first_name": "Sunita", "last_name": "Joshi", "role": "compliance_manager"},
                ],
            },
            {
                "org_name": "GovSecure India",
                "industry": "Government",
                "country": "India",
                "accounts": [
                    {"username": "gov_admin", "email": "admin@govsecure.gov.in", "password": "GovAdmin@2026", "first_name": "Amit", "last_name": "Tiwari", "role": "super_admin"},
                    {"username": "gov_auditor", "email": "auditor@govsecure.gov.in", "password": "GovAudit@2026", "first_name": "Kavita", "last_name": "Mishra", "role": "auditor"},
                ],
            },
            {
                "org_name": "ShopKart India",
                "industry": "E-Commerce",
                "country": "India",
                "accounts": [
                    {"username": "ecom_admin", "email": "admin@shopkart.in", "password": "EcomAdmin@2026", "first_name": "Deepak", "last_name": "Chauhan", "role": "super_admin"},
                    {"username": "ecom_security", "email": "security@shopkart.in", "password": "EcomSec@2026", "first_name": "Pooja", "last_name": "Nair", "role": "client_admin"},
                ],
            },
            {
                "org_name": "TeleNet Communications",
                "industry": "Telecommunications",
                "country": "India",
                "accounts": [
                    {"username": "telco_admin", "email": "admin@telenet.co.in", "password": "TelcoAdmin@2026", "first_name": "Suresh", "last_name": "Pillai", "role": "super_admin"},
                    {"username": "telco_soc", "email": "soc@telenet.co.in", "password": "TelcoSOC@2026", "first_name": "Ravi", "last_name": "Iyer", "role": "client_admin"},
                ],
            },
            {
                "org_name": "EduTech Learning",
                "industry": "Education",
                "country": "India",
                "accounts": [
                    {"username": "edu_admin", "email": "admin@edutech.edu.in", "password": "EduAdmin@2026", "first_name": "Prof. Meena", "last_name": "Sharma", "role": "super_admin"},
                ],
            },
            {
                "org_name": "InsureShield Ltd",
                "industry": "Insurance",
                "country": "India",
                "accounts": [
                    {"username": "ins_admin", "email": "admin@insureshield.co.in", "password": "InsAdmin@2026", "first_name": "Manish", "last_name": "Agarwal", "role": "super_admin"},
                ],
            },
            {
                "org_name": "CloudFirst Technologies",
                "industry": "Cloud & SaaS",
                "country": "India",
                "accounts": [
                    {"username": "cloud_admin", "email": "admin@cloudfirst.dev", "password": "CloudAdmin@2026", "first_name": "Ankit", "last_name": "Saxena", "role": "super_admin"},
                    {"username": "cloud_devops", "email": "devops@cloudfirst.dev", "password": "CloudDev@2026", "first_name": "Shreya", "last_name": "Das", "role": "client_admin"},
                ],
            },
            # === New Industry Test Accounts ===
            {
                "org_name": "Tata Steel Manufacturing",
                "industry": "Manufacturing",
                "country": "India",
                "accounts": [
                    {"username": "mfg_admin", "email": "admin@tatasteel-mfg.co.in", "password": "MfgAdmin@2026", "first_name": "Hemant", "last_name": "Deshmukh", "role": "super_admin"},
                    {"username": "mfg_ot_security", "email": "ot-security@tatasteel-mfg.co.in", "password": "MfgOTSec@2026", "first_name": "Pranav", "last_name": "Kulkarni", "role": "client_admin"},
                    {"username": "mfg_compliance", "email": "compliance@tatasteel-mfg.co.in", "password": "MfgComp@2026", "first_name": "Swati", "last_name": "Bhatt", "role": "compliance_manager"},
                ],
            },
            {
                "org_name": "SunPharma Biotech",
                "industry": "Pharmaceutical",
                "country": "India",
                "accounts": [
                    {"username": "pharma_admin", "email": "admin@sunpharma-bio.co.in", "password": "PharmaAdmin@2026", "first_name": "Dr. Ashok", "last_name": "Mehta", "role": "super_admin"},
                    {"username": "pharma_qa", "email": "qa@sunpharma-bio.co.in", "password": "PharmaQA@2026", "first_name": "Rekha", "last_name": "Srinivasan", "role": "compliance_manager"},
                    {"username": "pharma_auditor", "email": "audit@sunpharma-bio.co.in", "password": "PharmaAudit@2026", "first_name": "Vivek", "last_name": "Malhotra", "role": "auditor"},
                ],
            },
            {
                "org_name": "PowerGrid Energy Corp",
                "industry": "Energy & Power",
                "country": "India",
                "accounts": [
                    {"username": "energy_admin", "email": "admin@powergrid-energy.co.in", "password": "EnergyAdmin@2026", "first_name": "Girish", "last_name": "Rao", "role": "super_admin"},
                    {"username": "energy_scada", "email": "scada@powergrid-energy.co.in", "password": "EnergySCADA@2026", "first_name": "Tarun", "last_name": "Bose", "role": "client_admin"},
                ],
            },
            {
                "org_name": "Khaitan Legal Associates",
                "industry": "Legal",
                "country": "India",
                "accounts": [
                    {"username": "legal_admin", "email": "admin@khaitan-legal.co.in", "password": "LegalAdmin@2026", "first_name": "Adv. Nandini", "last_name": "Khaitan", "role": "super_admin"},
                    {"username": "legal_compliance", "email": "compliance@khaitan-legal.co.in", "password": "LegalComp@2026", "first_name": "Rohit", "last_name": "Saxena", "role": "compliance_manager"},
                ],
            },
            {
                "org_name": "BlueDart Logistics",
                "industry": "Logistics & Supply Chain",
                "country": "India",
                "accounts": [
                    {"username": "logistics_admin", "email": "admin@bluedart-logistics.co.in", "password": "LogiAdmin@2026", "first_name": "Sandeep", "last_name": "Choudhury", "role": "super_admin"},
                    {"username": "logistics_soc", "email": "soc@bluedart-logistics.co.in", "password": "LogiSOC@2026", "first_name": "Aruna", "last_name": "Menon", "role": "client_admin"},
                ],
            },
            {
                "org_name": "ZEE Media Group",
                "industry": "Media & Entertainment",
                "country": "India",
                "accounts": [
                    {"username": "media_admin", "email": "admin@zeemedia.co.in", "password": "MediaAdmin@2026", "first_name": "Aarav", "last_name": "Kapoor", "role": "super_admin"},
                    {"username": "media_security", "email": "security@zeemedia.co.in", "password": "MediaSec@2026", "first_name": "Divya", "last_name": "Rastogi", "role": "client_admin"},
                ],
            },
            {
                "org_name": "Bajaj Microfinance NBFC",
                "industry": "NBFC / Microfinance",
                "country": "India",
                "accounts": [
                    {"username": "nbfc_admin", "email": "admin@bajaj-nbfc.co.in", "password": "NBFCAdmin@2026", "first_name": "Manoj", "last_name": "Bajaj", "role": "super_admin"},
                    {"username": "nbfc_compliance", "email": "compliance@bajaj-nbfc.co.in", "password": "NBFCComp@2026", "first_name": "Lakshmi", "last_name": "Venkatesh", "role": "compliance_manager"},
                    {"username": "nbfc_auditor", "email": "auditor@bajaj-nbfc.co.in", "password": "NBFCAudit@2026", "first_name": "Harish", "last_name": "Patil", "role": "auditor"},
                ],
            },
            {
                "org_name": "PropNest Real Estate",
                "industry": "Real Estate / PropTech",
                "country": "India",
                "accounts": [
                    {"username": "realestate_admin", "email": "admin@propnest.co.in", "password": "PropAdmin@2026", "first_name": "Nitin", "last_name": "Agarwal", "role": "super_admin"},
                ],
            },
            {
                "org_name": "HAL Defence Systems",
                "industry": "Defence & Aerospace",
                "country": "India",
                "accounts": [
                    {"username": "defence_admin", "email": "admin@hal-defence.gov.in", "password": "DefAdmin@2026", "first_name": "Col. Rajendra", "last_name": "Thakur", "role": "super_admin"},
                    {"username": "defence_ciso", "email": "ciso@hal-defence.gov.in", "password": "DefCISO@2026", "first_name": "Brig. Suman", "last_name": "Chandra", "role": "client_admin"},
                    {"username": "defence_auditor", "email": "auditor@hal-defence.gov.in", "password": "DefAudit@2026", "first_name": "Maj. Pradeep", "last_name": "Negi", "role": "auditor"},
                ],
            },
        ]

        for ind in industries:
            ind_org, _ = Organization.objects.get_or_create(
                name=ind["org_name"],
                defaults={
                    "industry": ind["industry"],
                    "country": ind["country"],
                    "company_size": random.choice(["10-50", "50-200", "200-1000", "1000+"]),
                    "onboarding_completed": True,
                    "risk_score": random.randint(45, 85),
                }
            )
            for acc in ind["accounts"]:
                role = acc.pop("role")
                pwd = acc.pop("password")
                user, created = User.objects.get_or_create(
                    username=acc["username"],
                    defaults={**acc, "organization": ind_org, "role": role}
                )
                if created:
                    user.set_password(pwd)
                    user.save()
                    self.stdout.write(f'  Created: {user.username} ({ind["org_name"]})')

        self.stdout.write(self.style.SUCCESS(f'Test accounts ready. {len(industries) + 1} organizations created.'))

    def _seed_cves(self):
        from cve_manager.models import CVE

        cves_data = [
            # === 2023 CVEs ===
            ("CVE-2023-44228", "CRITICAL", 10.0, "2023-12-10",
             "Apache Log4j2 JNDI features used in configuration, log messages, and parameters do not protect against attacker controlled LDAP and other JNDI related endpoints. Allows remote code execution via crafted log messages.",
             "cpe:2.3:a:apache:log4j:*:*:*:*:*:*:*:*"),
            ("CVE-2023-23397", "CRITICAL", 9.8, "2023-03-14",
             "Microsoft Outlook Elevation of Privilege Vulnerability. An attacker who successfully exploited this vulnerability could access a user's Net-NTLMv2 hash for NTLM Relay attacks against another service.",
             "cpe:2.3:a:microsoft:outlook:*:*:*:*:*:*:*:*"),
            ("CVE-2023-34362", "CRITICAL", 9.8, "2023-06-02",
             "MOVEit Transfer SQL Injection vulnerability allows unauthenticated attacker to gain access to MOVEit Transfer's database. Exploited by Cl0p ransomware gang in mass data theft campaign.",
             "cpe:2.3:a:progress:moveit_transfer:*:*:*:*:*:*:*:*"),
            ("CVE-2023-4966", "CRITICAL", 9.4, "2023-10-10",
             "Citrix NetScaler ADC and NetScaler Gateway buffer overflow vulnerability (Citrix Bleed). Allows sensitive information disclosure including session tokens for session hijacking.",
             "cpe:2.3:a:citrix:netscaler_adc:*:*:*:*:*:*:*:*"),
            ("CVE-2023-22515", "CRITICAL", 10.0, "2023-10-04",
             "Atlassian Confluence Data Center and Server Broken Access Control vulnerability. Allows remote attacker to create unauthorized Confluence administrator accounts and access Confluence instances.",
             "cpe:2.3:a:atlassian:confluence_server:*:*:*:*:*:*:*:*"),
            ("CVE-2023-20198", "CRITICAL", 10.0, "2023-10-16",
             "Cisco IOS XE Web UI privilege escalation vulnerability. Allows unauthenticated remote attacker to create an account on an affected system with privilege level 15 access.",
             "cpe:2.3:o:cisco:ios_xe:*:*:*:*:*:*:*:*"),
            ("CVE-2023-36884", "HIGH", 8.8, "2023-07-11",
             "Microsoft Office and Windows HTML Remote Code Execution vulnerability. Exploited via specially crafted Microsoft Office documents. Used by RomCom threat actor in targeted attacks.",
             "cpe:2.3:a:microsoft:office:*:*:*:*:*:*:*:*"),
            ("CVE-2023-27997", "CRITICAL", 9.8, "2023-06-12",
             "Fortinet FortiOS and FortiProxy SSL-VPN heap-based buffer overflow allows remote attacker to execute arbitrary code or commands via specifically crafted requests.",
             "cpe:2.3:o:fortinet:fortios:*:*:*:*:*:*:*:*"),
            ("CVE-2023-2868", "CRITICAL", 9.8, "2023-05-24",
             "Barracuda Email Security Gateway remote command injection vulnerability. Exploited by Chinese state-sponsored actor UNC4841 for espionage campaigns.",
             "cpe:2.3:a:barracuda:email_security_gateway:*:*:*:*:*:*:*:*"),
            ("CVE-2023-38831", "HIGH", 7.8, "2023-08-23",
             "WinRAR code execution vulnerability allows attackers to execute arbitrary code when a user attempts to view a benign file within a ZIP archive. Exploited by multiple nation-state actors.",
             "cpe:2.3:a:rarlab:winrar:*:*:*:*:*:*:*:*"),
            ("CVE-2023-46747", "CRITICAL", 9.8, "2023-10-26",
             "F5 BIG-IP authentication bypass vulnerability allows unauthenticated attacker with network access to the BIG-IP system through the management port to execute arbitrary system commands.",
             "cpe:2.3:a:f5:big-ip:*:*:*:*:*:*:*:*"),
            ("CVE-2023-28771", "CRITICAL", 9.8, "2023-04-25",
             "Zyxel multiple firewalls OS command injection vulnerability in the Internet Key Exchange (IKE) packet decoder allows unauthenticated attacker to execute OS commands.",
             "cpe:2.3:o:zyxel:zld:*:*:*:*:*:*:*:*"),

            # === 2024 CVEs ===
            ("CVE-2024-3400", "CRITICAL", 10.0, "2024-04-12",
             "Palo Alto Networks PAN-OS command injection vulnerability in GlobalProtect feature. Allows unauthenticated attacker to execute arbitrary code with root privileges on the firewall. Actively exploited by state-sponsored actors.",
             "cpe:2.3:o:paloaltonetworks:pan-os:*:*:*:*:*:*:*:*"),
            ("CVE-2024-21887", "CRITICAL", 9.1, "2024-01-10",
             "Ivanti Connect Secure and Ivanti Policy Secure command injection vulnerability allows authenticated administrator to send specially crafted requests to execute arbitrary commands.",
             "cpe:2.3:a:ivanti:connect_secure:*:*:*:*:*:*:*:*"),
            ("CVE-2024-21762", "CRITICAL", 9.8, "2024-02-09",
             "Fortinet FortiOS out-of-bound write vulnerability in SSL VPN may allow a remote unauthenticated attacker to execute arbitrary code or commands via specifically crafted HTTP requests.",
             "cpe:2.3:o:fortinet:fortios:*:*:*:*:*:*:*:*"),
            ("CVE-2024-1709", "CRITICAL", 10.0, "2024-02-19",
             "ConnectWise ScreenConnect authentication bypass vulnerability (SlashAndGrab). Allows attackers to create admin accounts and execute remote code. Massively exploited within hours of disclosure.",
             "cpe:2.3:a:connectwise:screenconnect:*:*:*:*:*:*:*:*"),
            ("CVE-2024-27198", "CRITICAL", 9.8, "2024-03-04",
             "JetBrains TeamCity authentication bypass vulnerability allows unauthenticated attacker to perform admin actions. Exploited by Russian SVR (APT29) and North Korean actors.",
             "cpe:2.3:a:jetbrains:teamcity:*:*:*:*:*:*:*:*"),
            ("CVE-2024-4577", "CRITICAL", 9.8, "2024-06-09",
             "PHP CGI argument injection vulnerability on Windows allows unauthenticated attacker to execute arbitrary code. Affects all PHP versions on Windows using CGI mode.",
             "cpe:2.3:a:php:php:*:*:*:*:*:*:*:*"),
            ("CVE-2024-6387", "HIGH", 8.1, "2024-07-01",
             "OpenSSH regreSSHion vulnerability - signal handler race condition in sshd allows unauthenticated remote code execution as root on glibc-based Linux systems.",
             "cpe:2.3:a:openssh:openssh:*:*:*:*:*:*:*:*"),
            ("CVE-2024-23113", "CRITICAL", 9.8, "2024-02-15",
             "Fortinet FortiOS, FortiPAM, FortiProxy, FortiWeb format string vulnerability allows remote unauthenticated attacker to execute arbitrary code or commands via specially crafted packets.",
             "cpe:2.3:o:fortinet:fortios:*:*:*:*:*:*:*:*"),
            ("CVE-2024-47575", "CRITICAL", 9.8, "2024-10-23",
             "Fortinet FortiManager missing authentication for critical function allows remote attacker to execute arbitrary code or commands via specially crafted requests. Known as FortiJump.",
             "cpe:2.3:a:fortinet:fortimanager:*:*:*:*:*:*:*:*"),
            ("CVE-2024-0012", "CRITICAL", 9.8, "2024-11-18",
             "Palo Alto Networks PAN-OS management interface authentication bypass allows unauthenticated attacker to gain PAN-OS administrator privileges. Actively exploited in the wild.",
             "cpe:2.3:o:paloaltonetworks:pan-os:*:*:*:*:*:*:*:*"),
            ("CVE-2024-9474", "HIGH", 7.2, "2024-11-18",
             "Palo Alto Networks PAN-OS OS command injection vulnerability allows authenticated admin to escalate privileges to root. Chained with CVE-2024-0012 for full compromise.",
             "cpe:2.3:o:paloaltonetworks:pan-os:*:*:*:*:*:*:*:*"),
            ("CVE-2024-20353", "HIGH", 8.6, "2024-04-24",
             "Cisco Adaptive Security Appliance and Firepower Threat Defense web services denial-of-service and information disclosure vulnerability. Exploited by Arcanedoor threat actor.",
             "cpe:2.3:a:cisco:adaptive_security_appliance:*:*:*:*:*:*:*:*"),
            ("CVE-2024-38856", "CRITICAL", 9.8, "2024-08-05",
             "Apache OFBiz pre-authentication remote code execution via XML-RPC deserialization. Allows complete server takeover without credentials.",
             "cpe:2.3:a:apache:ofbiz:*:*:*:*:*:*:*:*"),
            ("CVE-2024-50623", "CRITICAL", 9.8, "2024-12-13",
             "Cleo Harmony, VLTrader, LexiCom unrestricted file upload vulnerability allows unauthenticated remote code execution. Exploited by Cl0p ransomware for mass data theft.",
             "cpe:2.3:a:cleo:harmony:*:*:*:*:*:*:*:*"),

            # === 2025 CVEs ===
            ("CVE-2025-0282", "CRITICAL", 9.0, "2025-01-08",
             "Ivanti Connect Secure, Policy Secure, and Neurons for ZTA gateways stack-based buffer overflow allows unauthenticated remote attacker to achieve remote code execution.",
             "cpe:2.3:a:ivanti:connect_secure:*:*:*:*:*:*:*:*"),
            ("CVE-2025-22224", "CRITICAL", 9.3, "2025-03-04",
             "VMware ESXi and Workstation TOCTOU race condition vulnerability leads to out-of-bounds write. Allows local attacker with admin privileges on a VM to escape the sandbox.",
             "cpe:2.3:a:vmware:esxi:*:*:*:*:*:*:*:*"),
            ("CVE-2025-24472", "CRITICAL", 9.8, "2025-02-11",
             "Fortinet FortiOS and FortiProxy authentication bypass via CSF proxy requests allows remote attacker to gain super-admin privileges via crafted CSF proxy requests.",
             "cpe:2.3:o:fortinet:fortios:*:*:*:*:*:*:*:*"),
            ("CVE-2025-23209", "HIGH", 8.8, "2025-02-20",
             "Craft CMS remote code execution vulnerability. If the security key has been compromised, allows remote attackers to execute arbitrary code on the underlying server.",
             "cpe:2.3:a:craftcms:craft_cms:*:*:*:*:*:*:*:*"),
            ("CVE-2025-30066", "HIGH", 8.6, "2025-03-18",
             "GitHub Actions tj-actions/changed-files supply chain compromise. Malicious code injected to exfiltrate CI/CD secrets from repositories using this popular action.",
             "cpe:2.3:a:github:actions:tj-actions\\/changed-files:*:*:*:*:*:*:*"),
            ("CVE-2025-1097", "CRITICAL", 9.8, "2025-03-24",
             "Kubernetes Ingress-NGINX Controller annotation injection vulnerability (IngressNightmare). Allows unauthenticated remote code execution affecting ~40% of all Kubernetes clusters.",
             "cpe:2.3:a:kubernetes:ingress-nginx:*:*:*:*:*:*:*:*"),
            ("CVE-2025-24813", "CRITICAL", 9.8, "2025-03-10",
             "Apache Tomcat partial PUT request handling deserialization vulnerability. Allows remote code execution if specific non-default conditions are met.",
             "cpe:2.3:a:apache:tomcat:*:*:*:*:*:*:*:*"),
            ("CVE-2025-29927", "CRITICAL", 9.1, "2025-03-21",
             "Next.js middleware authorization bypass vulnerability. Attackers can bypass authentication and authorization checks by crafting x-middleware-subrequest header.",
             "cpe:2.3:a:vercel:next.js:*:*:*:*:*:*:*:*"),
            ("CVE-2025-31161", "CRITICAL", 10.0, "2025-04-03",
             "CrushFTP authentication bypass via S3-compatible API allows unauthenticated access to file transfer data. Mass exploitation observed within 48 hours of disclosure.",
             "cpe:2.3:a:crushftp:crushftp:*:*:*:*:*:*:*:*"),
            ("CVE-2025-2783", "HIGH", 8.3, "2025-03-25",
             "Google Chrome Mojo sandbox escape vulnerability. Used in active exploitation chain (Operation ForumTroll) targeting Russian government and media organizations.",
             "cpe:2.3:a:google:chrome:*:*:*:*:*:*:*:*"),
            ("CVE-2025-21298", "CRITICAL", 9.8, "2025-01-14",
             "Microsoft Windows OLE remote code execution via crafted email in Outlook. Preview pane is an attack vector. Zero-click exploitation possible.",
             "cpe:2.3:o:microsoft:windows:*:*:*:*:*:*:*:*"),
            ("CVE-2025-26633", "HIGH", 7.0, "2025-03-11",
             "Microsoft Management Console (MSC) security feature bypass. Used by Water Gamayun threat actor to deploy SilentPrism and DarkWisp backdoors.",
             "cpe:2.3:o:microsoft:windows:*:*:*:*:*:*:*:*"),

            # === 2026 CVEs (Projected/Simulated) ===
            ("CVE-2026-00101", "CRITICAL", 10.0, "2026-01-15",
             "Critical zero-day in AWS Lambda runtime environment allows container escape and cross-tenant data access. Affects all Lambda functions using Python and Node.js runtimes. AWS emergency patch deployed within 6 hours.",
             "cpe:2.3:a:amazon:aws_lambda:*:*:*:*:*:*:*:*"),
            ("CVE-2026-00234", "CRITICAL", 9.8, "2026-01-28",
             "Microsoft Azure Active Directory (Entra ID) token forging vulnerability allows attackers to generate valid authentication tokens for any tenant. Similar to Storm-0558 incident.",
             "cpe:2.3:a:microsoft:azure_active_directory:*:*:*:*:*:*:*:*"),
            ("CVE-2026-01102", "CRITICAL", 9.9, "2026-02-05",
             "LLM prompt injection vulnerability in OpenAI ChatGPT Enterprise API allows data exfiltration from connected enterprise knowledge bases via indirect prompt injection.",
             "cpe:2.3:a:openai:chatgpt_enterprise:*:*:*:*:*:*:*:*"),
            ("CVE-2026-01455", "HIGH", 8.8, "2026-02-20",
             "Kubernetes AI Operator privilege escalation. Malicious ML models can escape sandbox and execute arbitrary code on the host node via GPU driver vulnerability.",
             "cpe:2.3:a:kubernetes:ai-operator:*:*:*:*:*:*:*:*"),
            ("CVE-2026-02001", "CRITICAL", 9.8, "2026-03-01",
             "GitLab CE/EE authentication bypass via SAML response manipulation. Allows unauthenticated attacker to gain admin access to any GitLab instance with SAML SSO enabled.",
             "cpe:2.3:a:gitlab:gitlab:*:*:*:*:ce:*:*:*"),
            ("CVE-2026-02340", "CRITICAL", 10.0, "2026-03-12",
             "Anthropic Claude API prompt injection via tool use results. Allows attacker to override system prompts and exfiltrate conversation data through crafted API tool responses.",
             "cpe:2.3:a:anthropic:claude_api:*:*:*:*:*:*:*:*"),
            ("CVE-2026-02789", "HIGH", 8.6, "2026-03-22",
             "Docker Engine container escape via runc vulnerability in overlay filesystem. Allows root in container to gain root on host. Affects Docker Engine 25.x and 26.x.",
             "cpe:2.3:a:docker:engine:*:*:*:*:*:*:*:*"),
            ("CVE-2026-03100", "CRITICAL", 9.8, "2026-04-01",
             "Cisco Webex Meetings zero-click RCE via malformed meeting invite. Attacker can execute code on victim's device without any user interaction. Used by Volt Typhoon in targeted attacks.",
             "cpe:2.3:a:cisco:webex_meetings:*:*:*:*:*:*:*:*"),
            ("CVE-2026-03456", "HIGH", 8.1, "2026-04-08",
             "Supply chain attack on popular npm package 'colors-palette' (15M weekly downloads). Backdoor exfiltrates environment variables including API keys and database credentials to C2 server.",
             "cpe:2.3:a:npm:colors-palette:*:*:*:*:*:*:*:*"),
            ("CVE-2026-03789", "CRITICAL", 9.9, "2026-04-10",
             "Zero-day in major Indian banking SWIFT gateway allows unauthorized fund transfers. Lazarus Group actively exploiting. RBI emergency advisory issued. Affects 12 major banks.",
             "cpe:2.3:a:india:swift_gateway:*:*:*:*:*:*:*:*"),
            ("CVE-2026-04001", "CRITICAL", 9.8, "2026-04-05",
             "Critical RCE in Cloudflare Workers runtime allows cross-tenant code execution via WebAssembly memory corruption. Cloudflare deployed emergency mitigation within 2 hours.",
             "cpe:2.3:a:cloudflare:workers:*:*:*:*:*:*:*:*"),
            ("CVE-2026-04123", "HIGH", 7.5, "2026-04-09",
             "Agentic AI framework LangChain arbitrary code execution via malicious tool plugin. Allows RCE when agent loads untrusted tools from community registry.",
             "cpe:2.3:a:langchain:langchain:*:*:*:*:*:*:*:*"),
        ]

        created = 0
        for cve_id, severity, cvss, pub_date, desc, products in cves_data:
            from django.utils.dateparse import parse_date
            pub_dt = timezone.make_aware(
                timezone.datetime.combine(parse_date(pub_date), timezone.datetime.min.time())
            )
            _, was_created = CVE.objects.get_or_create(
                cve_id=cve_id,
                defaults={
                    "description": desc,
                    "severity": severity,
                    "cvss_score": cvss,
                    "published_date": pub_dt,
                    "last_modified": pub_dt + timedelta(days=random.randint(1, 30)),
                    "affected_products": products,
                }
            )
            if was_created:
                created += 1

        self.stdout.write(self.style.SUCCESS(f'  Seeded {created} CVEs (2023-2026)'))

    def _seed_dark_web_data(self):
        from threat_intel.models import (
            ThreatIntelSource, LiveThreat, DarkWebMention,
            MonitoredDomain, LeakedCredential
        )

        # Ensure sources exist
        sources_data = [
            ("XSS Forum", "dark_web", "onion://xssforum.onion"),
            ("BreachForums v2", "dark_web", "onion://breachforums2.onion"),
            ("Killnet Official", "telegram", "t.me/killnet_reservs"),
            ("NoName057(16)", "telegram", "t.me/noname05716"),
            ("AlienVault OTX", "osint", "https://otx.alienvault.com"),
            ("Shodan Monitor", "osint", "https://monitor.shodan.io"),
            ("Have I Been Pwned", "breach_db", "https://haveibeenpwned.com"),
            ("DeHashed", "breach_db", "https://dehashed.com"),
            ("Exploit.in", "dark_web", "onion://exploitin.onion"),
            ("Pastebin Monitor", "paste_site", "https://pastebin.com"),
            ("LeakBase", "breach_db", "onion://leakbase.onion"),
            ("Russian Market", "dark_web", "onion://russianmarket.onion"),
        ]
        sources = {}
        for name, stype, url in sources_data:
            src, _ = ThreatIntelSource.objects.get_or_create(
                name=name, defaults={"source_type": stype, "url": url}
            )
            sources[name] = src

        # Monitored Domains
        domains_data = [
            ("cybershield.io", "CyberShield Corp", "MEDIUM", 2, 5),
            ("example-bank.co.in", "Example Bank Ltd", "HIGH", 4, 12),
            ("govportal.gov.in", "Government Portal", "CRITICAL", 7, 23),
            ("techstartup.dev", "TechStartup Inc", "LOW", 0, 1),
            ("healthdata.org", "Health Data Org", "HIGH", 3, 8),
            # New industry domains
            ("bharatbank.co.in", "Bharat National Bank", "HIGH", 5, 14),
            ("medcare.health", "MedCare Hospitals", "MEDIUM", 2, 6),
            ("shopkart.in", "ShopKart India", "HIGH", 6, 18),
            ("telenet.co.in", "TeleNet Communications", "MEDIUM", 3, 9),
            ("tatasteel-mfg.co.in", "Tata Steel Manufacturing", "HIGH", 4, 11),
            ("sunpharma-bio.co.in", "SunPharma Biotech", "CRITICAL", 8, 22),
            ("powergrid-energy.co.in", "PowerGrid Energy Corp", "CRITICAL", 6, 19),
            ("khaitan-legal.co.in", "Khaitan Legal Associates", "MEDIUM", 1, 4),
            ("bluedart-logistics.co.in", "BlueDart Logistics", "HIGH", 3, 10),
            ("zeemedia.co.in", "ZEE Media Group", "MEDIUM", 2, 7),
            ("bajaj-nbfc.co.in", "Bajaj Microfinance NBFC", "HIGH", 5, 16),
            ("propnest.co.in", "PropNest Real Estate", "LOW", 1, 2),
            ("hal-defence.gov.in", "HAL Defence Systems", "CRITICAL", 9, 31),
            ("cloudfirst.dev", "CloudFirst Technologies", "MEDIUM", 2, 5),
            ("edutech.edu.in", "EduTech Learning", "LOW", 1, 3),
            ("insureshield.co.in", "InsureShield Ltd", "MEDIUM", 3, 8),
        ]
        for domain, org_name, risk, breaches, mentions in domains_data:
            MonitoredDomain.objects.get_or_create(
                domain=domain,
                defaults={
                    "risk_level": risk,
                    "total_breaches_found": breaches,
                    "total_mentions_found": mentions,
                    "last_scanned": timezone.now() - timedelta(hours=random.randint(1, 48)),
                }
            )

        # Dark Web Mentions
        dw_source = sources.get("BreachForums v2") or sources.get("XSS Forum")
        if dw_source:
            mentions_data = [
                ("cybershield.io", "Database dump from cybershield.io posted on BreachForums. Contains 15K employee records with hashed passwords (bcrypt). Seller: darkm4ster_x.", 85,
                 "HIGH RISK: Legitimate dump confirmed. Bcrypt hashes detected. Recommend immediate password reset for all cybershield.io accounts."),
                ("govportal.gov.in", "Indian government portal credentials found in Telegram channel. Combo list with 50K entries. Channel has 12K subscribers.", 92,
                 "CRITICAL: Government credential leak in public Telegram channel. Immediate action required. Notify CERT-In."),
                ("example-bank.co.in", "Banking API keys and internal endpoints shared on paste site. Includes staging and production URLs.", 78,
                 "HIGH RISK: API key exposure could enable unauthorized transactions. Rotate all API keys immediately."),
                ("admin@cybershield.io", "Email found in RaidForums archive dating back to Q3 2024 breach. Associated with plaintext password and security questions.", 88,
                 "VERIFIED LEAK: Admin email compromised with plaintext credentials. Immediate account lockdown required."),
                ("SWIFT infrastructure", "Forum discussion about vulnerabilities in Indian SWIFT gateway systems. Multiple threat actors showing interest. Possible coordinated attack planning.", 95,
                 "CRITICAL INTELLIGENCE: Nation-state level threat to banking infrastructure. Recommend proactive defense measures and RBI notification."),
                # New industry-specific mentions
                ("tatasteel-mfg.co.in", "SCADA/ICS credentials for manufacturing OT network posted on dark web marketplace. Includes HMI access and PLC programming credentials. Seller claims insider access.", 91,
                 "CRITICAL: Industrial control system credentials leaked. Risk of physical infrastructure damage. Isolate OT network immediately. Notify CERT-In ICS division."),
                ("sunpharma-bio.co.in", "Clinical trial data and drug formulation IP documents exfiltrated. 2.3GB archive listed for sale. Includes Phase 3 trial results for unreleased compounds.", 89,
                 "HIGH RISK: Pharmaceutical IP theft with regulatory and competitive implications. Notify DCGI and initiate IP protection response."),
                ("powergrid-energy.co.in", "Power grid SCADA access being auctioned on Russian-language forum. Threat actor claims persistent access to supervisory control systems across 3 substations.", 97,
                 "CRITICAL: National infrastructure threat. Active SCADA access being sold. Immediate coordination with NCIIPC and power sector CERT required."),
                ("hal-defence.gov.in", "Classified defence procurement documents and satellite subsystem schematics found on Chinese-linked APT staging server. Data appears recent (Q1 2026).", 99,
                 "CRITICAL: National security breach. Classified defence data exfiltrated. Immediate escalation to NTRO and Defence Cyber Agency required."),
                ("bajaj-nbfc.co.in", "Loan applicant PII database (850K records) including Aadhaar numbers, PAN cards, and bank statements posted on BreachForums. Price: $15K.", 86,
                 "HIGH RISK: Massive PII leak with financial fraud potential. Notify RBI, affected customers, and CERT-In. Comply with DPDPA breach notification."),
                ("shopkart.in", "Payment gateway API keys and customer credit card data (tokenized) found in stealer log collection. 120K payment records. Source: Magecart skimmer variant.", 88,
                 "HIGH RISK: PCI-DSS breach. Payment data compromised via web skimmer. Engage PCI QSA, notify payment processor, and scan all checkout pages."),
                ("bluedart-logistics.co.in", "GPS tracking API access and shipment manifest database credentials shared in Telegram hacking group. Could enable cargo theft or supply chain disruption.", 76,
                 "MEDIUM-HIGH RISK: Supply chain security threat. Rotate API keys, audit GPS tracking access, and review shipment security protocols."),
                ("zeemedia.co.in", "Internal content management system credentials and pre-release content schedules leaked. Source journalist email accounts compromised via phishing.", 72,
                 "MEDIUM RISK: Media organization credential leak. Force password reset for all CMS accounts. Review content embargo controls."),
            ]
            for keyword, snippet, risk, analysis in mentions_data:
                DarkWebMention.objects.get_or_create(
                    keyword_matched=keyword,
                    snippet=snippet,
                    defaults={
                        "source": dw_source,
                        "risk_score": risk,
                        "ai_analysis": analysis,
                    }
                )

        # Leaked Credentials
        leak_domains = MonitoredDomain.objects.all()
        for dom in leak_domains:
            leak_emails = [
                f"admin@{dom.domain}",
                f"info@{dom.domain}",
                f"support@{dom.domain}",
            ]
            breach_sources = [
                "BreachForums Dump - Mar 2026",
                "Telegram Channel Leak - Feb 2026",
                "DeHashed Collection #47",
                "Russian Market Stealer Logs",
            ]
            for email in leak_emails[:random.randint(1, 3)]:
                LeakedCredential.objects.get_or_create(
                    email=email,
                    breach_source=random.choice(breach_sources),
                    defaults={
                        "domain": dom,
                        "breach_date": (timezone.now() - timedelta(days=random.randint(10, 180))).date(),
                        "data_types": random.sample(["email", "password_hash", "plaintext_password", "phone", "address", "ip_address"], k=random.randint(2, 4)),
                        "is_verified": random.choice([True, False]),
                        "risk_score": random.randint(60, 98),
                        "ai_recommendation": f"Force password reset for {email}. Enable MFA on all accounts. Monitor for unauthorized access.",
                    }
                )

        # Live Threats
        if dw_source:
            threats_data = [
                ("APT41 Targeting Indian Financial Sector", "CRITICAL",
                 "APT41 (Double Dragon) detected conducting reconnaissance against Indian banking infrastructure. IOCs include C2 domains resolving to Chinese VPS providers.",
                 "APT41 (Double Dragon)", "South Asia", "Financial"),
                ("Ransomware Campaign: LockBit 4.0 Variant", "CRITICAL",
                 "New LockBit 4.0 variant with AI-powered encryption detected. Targeting healthcare and education sectors. Uses living-off-the-land techniques.",
                 "LockBit", "Global", "Healthcare"),
                ("Salt Typhoon Telecom Espionage", "HIGH",
                 "Salt Typhoon continues to target telecom providers. New backdoor variant 'GhostSpider' detected in network equipment firmware.",
                 "Salt Typhoon", "Asia Pacific", "Telecommunications"),
                ("Credential Stuffing Wave: Indian E-Commerce", "HIGH",
                 "Massive credential stuffing campaign targeting Indian e-commerce platforms. Over 2M login attempts detected in last 24 hours from botnet.",
                 "Unknown - Botnet", "India", "E-Commerce"),
                ("Zero-Day Exploit Market Activity", "MEDIUM",
                 "Dark web marketplace listing zero-day exploits for iOS 19 and Android 16. Prices ranging from $500K to $2.5M. Buyer appears to be nation-state.",
                 "Unknown - Broker", "Global", "Mobile"),
                # New industry-specific live threats
                ("XENOTIME Targeting Indian Power Grid", "CRITICAL",
                 "XENOTIME (TRITON/TRISIS) threat group detected probing Indian power grid SCADA systems. Safety Instrumented System (SIS) manipulation capability confirmed. Could cause physical damage to turbines and transformers.",
                 "XENOTIME", "South Asia", "Energy & Power"),
                ("Pharmaceutical Supply Chain Attack: Operation RxHijack", "HIGH",
                 "Coordinated campaign targeting Indian pharmaceutical companies via compromised third-party lab management software. Threat actor modifying drug formulation data and quality control records.",
                 "Unknown - APT", "India", "Pharmaceutical"),
                ("Defence Espionage: SideWinder APT Campaign", "CRITICAL",
                 "SideWinder APT group conducting targeted spear-phishing against Indian defence contractors. Payload delivers custom RAT with satellite communication interception capabilities.",
                 "SideWinder", "South Asia", "Defence & Aerospace"),
                ("NBFC Data Harvesting Campaign", "HIGH",
                 "Organized campaign exploiting weak KYC verification APIs in Indian NBFCs and microfinance institutions. Over 500K Aadhaar-linked records harvested for synthetic identity fraud.",
                 "Unknown - Fraud Ring", "India", "NBFC / Microfinance"),
                ("Manufacturing ICS Ransomware: IndustrialSpy 2.0", "CRITICAL",
                 "New ransomware variant specifically targeting Siemens and Rockwell PLCs in manufacturing environments. Encrypts both IT and OT systems simultaneously. Demands in Monero.",
                 "IndustrialSpy", "Global", "Manufacturing"),
                ("Legal Sector Data Exfiltration: LegalLeaks", "HIGH",
                 "APT group targeting Indian law firms handling M&A and IPO transactions. Exfiltrating privileged attorney-client communications for insider trading and corporate espionage.",
                 "Unknown - APT", "India", "Legal"),
                ("Logistics GPS Spoofing Attacks", "MEDIUM",
                 "GPS spoofing attacks targeting Indian logistics companies. Cargo shipments being rerouted via manipulated tracking data. Insurance fraud and cargo theft ring suspected.",
                 "Unknown - Criminal", "India", "Logistics"),
                ("PropTech Platform Credential Stuffing", "MEDIUM",
                 "Mass credential stuffing campaign against Indian real estate portals. Attackers harvesting property ownership records and financial documents for identity theft and fraud.",
                 "Unknown - Botnet", "India", "Real Estate"),
            ]
            for title, severity, desc, actor, region, industry in threats_data:
                LiveThreat.objects.get_or_create(
                    title=title,
                    defaults={
                        "description": desc,
                        "source": dw_source,
                        "severity": severity,
                        "actor": actor,
                        "target_region": region,
                        "target_industry": industry,
                    }
                )

        self.stdout.write(self.style.SUCCESS('  Dark web monitoring data seeded'))

    def _seed_agent_history(self):
        from threat_intel.models import ThreatAgent, AgentLog

        agents = ThreatAgent.objects.all()
        if not agents:
            return

        log_entries = [
            ("ORCHESTRATOR", "info", "Pipeline initialized. All agents reporting nominal status."),
            ("ORCHESTRATOR", "info", "Dispatching RECON_AGENT to scan 5 monitored domains."),
            ("RECON_AGENT", "info", "Starting domain reconnaissance for cybershield.io"),
            ("RECON_AGENT", "success", "WHOIS lookup complete. Domain registered 2019-03-15. Registrar: GoDaddy."),
            ("DARKWEB_CRAWLER", "info", "Connecting to Tor network... Circuit established."),
            ("DARKWEB_CRAWLER", "info", "Crawling BreachForums for mentions of monitored domains..."),
            ("DARKWEB_CRAWLER", "warning", "New paste detected: cybershield.io employee database - 15K records"),
            ("EMAIL_HUNTER", "info", "Scanning breach databases for admin@cybershield.io"),
            ("EMAIL_HUNTER", "warning", "MATCH FOUND: admin@cybershield.io in BreachForums Dump Mar 2026"),
            ("EMAIL_HUNTER", "success", "Credential verification complete. Bcrypt hash detected."),
            ("THREAT_ANALYZER", "info", "Analyzing threat intelligence from 3 sources..."),
            ("THREAT_ANALYZER", "info", "NLP classification: Credential leak - HIGH confidence (0.94)"),
            ("THREAT_ANALYZER", "success", "Threat report generated. Risk score: 87/100"),
            ("IOC_EXTRACTOR", "info", "Extracting IOCs from threat report..."),
            ("IOC_EXTRACTOR", "success", "Extracted 4 IPs, 2 domains, 3 SHA256 hashes"),
            ("REPORT_GENERATOR", "info", "Compiling executive threat intelligence report..."),
            ("REPORT_GENERATOR", "success", "Report ready. PDF export available."),
            ("ORCHESTRATOR", "success", "Scan pipeline complete. 5 findings, 1 critical alert generated."),
            ("DARKWEB_CRAWLER", "error", "Connection to .onion endpoint timed out. Retrying via alternate circuit..."),
            ("DARKWEB_CRAWLER", "info", "Reconnected. Resuming crawl from checkpoint."),
        ]

        for agent_name, level, message in log_entries:
            agent = agents.filter(name=agent_name).first()
            if agent:
                AgentLog.objects.create(
                    agent=agent,
                    level=level,
                    message=message,
                )

        self.stdout.write(self.style.SUCCESS('  Agent history logs seeded'))
