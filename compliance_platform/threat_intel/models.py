from django.db import models
from django.conf import settings


class ThreatIntelSource(models.Model):
    SOURCE_TYPES = (
        ('dark_web', 'Dark Web Forum / Marketplace'),
        ('telegram', 'Telegram Channels'),
        ('osint', 'OSINT Feeds'),
        ('hactivist', 'Hacktivist Groups'),
        ('paste_site', 'Paste Sites'),
        ('breach_db', 'Breach Databases'),
    )
    name = models.CharField(max_length=255)
    source_type = models.CharField(max_length=50, choices=SOURCE_TYPES)
    url = models.CharField(max_length=500, blank=True)
    is_active = models.BooleanField(default=True)
    last_scanned = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.get_source_type_display()})"


class LiveThreat(models.Model):
    SEVERITY_LEVELS = (
        ('CRITICAL', 'Critical'),
        ('HIGH', 'High'),
        ('MEDIUM', 'Medium'),
        ('LOW', 'Low'),
    )
    title = models.CharField(max_length=300)
    description = models.TextField()
    source = models.ForeignKey(ThreatIntelSource, on_delete=models.CASCADE)
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS)
    timestamp = models.DateTimeField(auto_now_add=True)
    target_region = models.CharField(max_length=100, default='Global')
    target_industry = models.CharField(max_length=100, default='Financial')
    actor = models.CharField(max_length=100, blank=True, null=True, help_text="Known threat actor or APT group")
    indicators_of_compromise = models.JSONField(default=list, blank=True, help_text="IPs, Domains, Hashes")
    is_resolved = models.BooleanField(default=False)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"[{self.severity}] {self.title}"


class DarkWebMention(models.Model):
    keyword_matched = models.CharField(max_length=100)
    snippet = models.TextField()
    source = models.ForeignKey(ThreatIntelSource, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    risk_score = models.IntegerField(default=50, help_text="0-100 score formulated by AI Agent")
    ai_analysis = models.TextField(blank=True, help_text="Agentic explanation of the threat context")

    def __str__(self):
        return f"Mention: {self.keyword_matched} (Risk {self.risk_score})"


# ============ NEW: Dark Web Monitoring Models ============

class MonitoredDomain(models.Model):
    """Domains being actively monitored on dark web for breaches/mentions"""
    domain = models.CharField(max_length=255, unique=True)
    organization = models.ForeignKey(
        'core.Organization', on_delete=models.CASCADE, null=True, blank=True
    )
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    added_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    last_scanned = models.DateTimeField(null=True, blank=True)
    total_breaches_found = models.IntegerField(default=0)
    total_mentions_found = models.IntegerField(default=0)
    risk_level = models.CharField(max_length=20, choices=(
        ('CRITICAL', 'Critical'), ('HIGH', 'High'),
        ('MEDIUM', 'Medium'), ('LOW', 'Low'), ('CLEAN', 'Clean'),
    ), default='LOW')

    def __str__(self):
        return f"{self.domain} [{self.risk_level}]"


class LeakedCredential(models.Model):
    """Leaked emails/credentials found on dark web"""
    email = models.EmailField()
    domain = models.ForeignKey(MonitoredDomain, on_delete=models.CASCADE, related_name='leaked_creds')
    breach_source = models.CharField(max_length=255, help_text="Where the leak was found")
    breach_date = models.DateField(null=True, blank=True)
    discovered_at = models.DateTimeField(auto_now_add=True)
    data_types = models.JSONField(default=list, help_text="Types of data leaked: password, hash, phone, etc.")
    password_hash = models.CharField(max_length=255, blank=True, help_text="Partial hash if found")
    is_verified = models.BooleanField(default=False)
    risk_score = models.IntegerField(default=50)
    ai_recommendation = models.TextField(blank=True)

    class Meta:
        unique_together = ('email', 'breach_source')

    def __str__(self):
        return f"{self.email} via {self.breach_source}"


class DarkWebScan(models.Model):
    """Records of dark web scans performed by agents"""
    STATUS_CHOICES = (
        ('queued', 'Queued'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    scan_type = models.CharField(max_length=50, choices=(
        ('org_search', 'Organization Search'),
        ('email_search', 'Email Search'),
        ('domain_monitor', 'Domain Monitor'),
        ('full_recon', 'Full Reconnaissance'),
    ))
    query = models.CharField(max_length=500)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    initiated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    results_summary = models.TextField(blank=True)
    results_data = models.JSONField(default=dict, blank=True)
    agent_used = models.CharField(max_length=100, default='RECON_AGENT')

    def __str__(self):
        return f"[{self.status}] {self.scan_type}: {self.query}"


# ============ NEW: Agentic AI Models ============

class ThreatAgent(models.Model):
    """Autonomous AI agents for threat intelligence"""
    AGENT_TYPES = (
        ('recon', 'Reconnaissance Agent'),
        ('darkweb_crawler', 'Dark Web Crawler'),
        ('email_hunter', 'Email Leak Hunter'),
        ('threat_analyzer', 'Threat Analyzer'),
        ('ioc_extractor', 'IOC Extractor'),
        ('report_generator', 'Report Generator'),
        ('orchestrator', 'Orchestrator Agent'),
    )
    STATUS_CHOICES = (
        ('idle', 'Idle'),
        ('active', 'Active'),
        ('scanning', 'Scanning'),
        ('analyzing', 'Analyzing'),
        ('error', 'Error'),
        ('cooldown', 'Cooldown'),
    )
    name = models.CharField(max_length=100, unique=True)
    agent_type = models.CharField(max_length=50, choices=AGENT_TYPES)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='idle')
    is_enabled = models.BooleanField(default=True)
    tasks_completed = models.IntegerField(default=0)
    threats_found = models.IntegerField(default=0)
    last_active = models.DateTimeField(null=True, blank=True)
    capabilities = models.JSONField(default=list, help_text="List of agent capabilities")
    config = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.name} [{self.get_status_display()}]"


class AgentTask(models.Model):
    """Tasks assigned to or created by agents"""
    PRIORITY_CHOICES = (
        ('critical', 'Critical'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    )
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    agent = models.ForeignKey(ThreatAgent, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    result = models.JSONField(default=dict, blank=True)
    parent_task = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subtasks')

    def __str__(self):
        return f"[{self.agent.name}] {self.title}"


class AgentLog(models.Model):
    """Real-time logs from agent activities"""
    LOG_LEVELS = (
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('success', 'Success'),
        ('critical', 'Critical'),
    )
    agent = models.ForeignKey(ThreatAgent, on_delete=models.CASCADE, related_name='logs')
    timestamp = models.DateTimeField(auto_now_add=True)
    level = models.CharField(max_length=20, choices=LOG_LEVELS, default='info')
    message = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.level}] {self.agent.name}: {self.message[:80]}"
