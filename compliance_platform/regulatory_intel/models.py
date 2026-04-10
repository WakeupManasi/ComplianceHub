from django.db import models
from django.conf import settings


class RegulatorySource(models.Model):
    """Tracks a regulatory body/source being monitored."""
    SOURCE_TYPES = [
        ('rbi', 'Reserve Bank of India'),
        ('sebi', 'Securities and Exchange Board of India'),
        ('mca', 'Ministry of Corporate Affairs'),
        ('gazette', 'eGazette of India'),
        ('fiu', 'Financial Intelligence Unit'),
    ]
    name = models.CharField(max_length=255)
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPES)
    base_url = models.URLField()
    scrape_url = models.URLField(help_text='URL to scrape for new notifications')
    is_active = models.BooleanField(default=True)
    last_checked = models.DateTimeField(null=True, blank=True)
    check_interval_minutes = models.IntegerField(default=60)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_source_type_display()} - {self.name}"


class RegulatoryDocument(models.Model):
    """Stores a fetched regulatory document (circular, notification, act)."""
    DOC_TYPES = [
        ('circular', 'Circular'),
        ('notification', 'Notification'),
        ('master_direction', 'Master Direction'),
        ('act', 'Act/Statute'),
        ('amendment', 'Amendment'),
        ('guideline', 'Guideline'),
    ]
    IMPACT_LEVELS = [
        ('critical', 'Critical'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]
    title = models.CharField(max_length=500)
    doc_type = models.CharField(max_length=30, choices=DOC_TYPES)
    source = models.ForeignKey(RegulatorySource, on_delete=models.CASCADE, related_name='documents')
    reference_number = models.CharField(max_length=200, blank=True)
    published_date = models.DateField(null=True, blank=True)
    effective_date = models.DateField(null=True, blank=True)
    compliance_deadline = models.DateField(null=True, blank=True)
    source_url = models.URLField(blank=True)
    pdf_file = models.FileField(upload_to='regulatory_docs/', blank=True)
    raw_text = models.TextField(blank=True, help_text='Extracted text content')
    summary = models.TextField(blank=True, help_text='AI-generated summary')
    impact_level = models.CharField(max_length=20, choices=IMPACT_LEVELS, default='medium')
    affected_entities = models.TextField(blank=True, help_text='Comma-separated list: banks, NBFCs, fintechs, etc.')
    categories = models.TextField(blank=True, help_text='Comma-separated: KYC, prudential, cyber, etc.')
    is_processed = models.BooleanField(default=False)
    is_new = models.BooleanField(default=True)
    previous_version = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='newer_versions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-published_date', '-created_at']

    def __str__(self):
        return f"[{self.get_doc_type_display()}] {self.title}"


class ClauseDiff(models.Model):
    """Stores clause-level differences between old and new regulation versions."""
    CHANGE_TYPES = [
        ('added', 'Added'),
        ('removed', 'Removed'),
        ('modified', 'Modified'),
    ]
    document = models.ForeignKey(RegulatoryDocument, on_delete=models.CASCADE, related_name='diffs')
    previous_document = models.ForeignKey(
        RegulatoryDocument, on_delete=models.SET_NULL, null=True, blank=True, related_name='forward_diffs'
    )
    clause_reference = models.CharField(max_length=100, blank=True, help_text='e.g. Section 5(a), Clause 3.2')
    change_type = models.CharField(max_length=20, choices=CHANGE_TYPES)
    old_text = models.TextField(blank=True)
    new_text = models.TextField(blank=True)
    change_summary = models.TextField(blank=True, help_text='AI-generated summary of the change')
    impact_score = models.IntegerField(default=0, help_text='1-10 impact severity score')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-impact_score']

    def __str__(self):
        return f"{self.clause_reference} - {self.get_change_type_display()}"


class ImpactMapping(models.Model):
    """Maps a regulatory change to affected products/departments/policies."""
    AREA_TYPES = [
        ('product', 'Product/Service'),
        ('department', 'Department'),
        ('policy', 'Internal Policy'),
        ('process', 'Business Process'),
        ('system', 'IT System'),
        ('contract', 'Contract/Agreement'),
    ]
    diff = models.ForeignKey(ClauseDiff, on_delete=models.CASCADE, related_name='mappings')
    area_type = models.CharField(max_length=20, choices=AREA_TYPES)
    area_name = models.CharField(max_length=255, help_text='e.g. Home Loans, KYC Team, AML Policy')
    description = models.TextField(blank=True, help_text='How this change affects the area')
    risk_score = models.IntegerField(default=0, help_text='1-10 risk score')
    action_required = models.TextField(blank=True, help_text='Specific action to take')
    responsible_team = models.CharField(max_length=255, blank=True)
    deadline = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending Review'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('not_applicable', 'Not Applicable'),
    ], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-risk_score']

    def __str__(self):
        return f"{self.area_name} - {self.get_area_type_display()}"


class ImpactReport(models.Model):
    """Generated impact report for a regulatory change."""
    document = models.ForeignKey(RegulatoryDocument, on_delete=models.CASCADE, related_name='reports')
    title = models.CharField(max_length=500)
    executive_summary = models.TextField(blank=True)
    detailed_analysis = models.TextField(blank=True)
    policy_amendments = models.TextField(blank=True, help_text='Drafted policy amendment text')
    sop_changes = models.TextField(blank=True, help_text='SOP update recommendations')
    filing_checklist = models.TextField(blank=True, help_text='Required regulatory filings')
    training_requirements = models.TextField(blank=True)
    overall_risk_score = models.IntegerField(default=0)
    generated_by = models.CharField(max_length=50, default='ai_agent')
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class ComplianceCategory(models.Model):
    """Categories for organizing compliance requirements."""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    keywords = models.TextField(blank=True, help_text='Comma-separated keywords for auto-classification')
    icon = models.CharField(max_length=50, blank=True, default='shield')

    class Meta:
        verbose_name_plural = 'Compliance Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class AgentLog(models.Model):
    """Logs actions taken by AI agents for audit trail."""
    AGENT_TYPES = [
        ('monitor', 'Monitor Agent'),
        ('scraper', 'Scraper Agent'),
        ('diff', 'Diff Agent'),
        ('classifier', 'Classifier Agent'),
        ('mapper', 'Mapping Agent'),
        ('drafter', 'Policy Drafting Agent'),
        ('reporter', 'Report Generation Agent'),
    ]
    agent_type = models.CharField(max_length=20, choices=AGENT_TYPES)
    action = models.CharField(max_length=255)
    details = models.TextField(blank=True)
    document = models.ForeignKey(
        RegulatoryDocument, on_delete=models.SET_NULL, null=True, blank=True
    )
    status = models.CharField(max_length=20, choices=[
        ('started', 'Started'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ], default='started')
    error_message = models.TextField(blank=True)
    duration_seconds = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_agent_type_display()}] {self.action}"
