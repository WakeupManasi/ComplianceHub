from django.db import models
from django.conf import settings


class Audit(models.Model):
    AUDIT_TYPES = [
        ('internal', 'Internal Audit'),
        ('external', 'External Audit'),
        ('regulatory', 'Regulatory Audit'),
        ('surveillance', 'Surveillance Audit'),
        ('certification', 'Certification Audit'),
    ]
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('under_review', 'Under Review'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    title = models.CharField(max_length=255)
    audit_type = models.CharField(max_length=20, choices=AUDIT_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    organization = models.ForeignKey('core.Organization', on_delete=models.CASCADE, related_name='audits')
    framework = models.ForeignKey('compliance.ComplianceFramework', on_delete=models.SET_NULL, null=True, blank=True)
    lead_auditor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='led_audits')
    auditors = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='assigned_audits')
    scope = models.TextField(blank=True, help_text='What areas/controls will be audited')
    objectives = models.TextField(blank=True)
    scheduled_start = models.DateField()
    scheduled_end = models.DateField()
    actual_start = models.DateField(null=True, blank=True)
    actual_end = models.DateField(null=True, blank=True)
    findings_summary = models.TextField(blank=True)
    score = models.IntegerField(null=True, blank=True, help_text='Audit score 0-100')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-scheduled_start']

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    @property
    def duration_days(self):
        return (self.scheduled_end - self.scheduled_start).days

    @property
    def is_overdue(self):
        from django.utils import timezone
        if self.status in ('scheduled', 'in_progress') and self.scheduled_end < timezone.now().date():
            return True
        return False


class AuditFinding(models.Model):
    SEVERITY_CHOICES = [
        ('observation', 'Observation'),
        ('minor', 'Minor Non-Conformity'),
        ('major', 'Major Non-Conformity'),
        ('critical', 'Critical Non-Conformity'),
        ('opportunity', 'Opportunity for Improvement'),
    ]
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('verified', 'Verified'),
        ('closed', 'Closed'),
    ]
    audit = models.ForeignKey(Audit, on_delete=models.CASCADE, related_name='findings')
    title = models.CharField(max_length=255)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    control = models.ForeignKey('compliance.Control', on_delete=models.SET_NULL, null=True, blank=True)
    evidence = models.TextField(blank=True)
    corrective_action = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_severity_display()})"


class AuditTimelineEvent(models.Model):
    EVENT_TYPES = [
        ('created', 'Audit Created'),
        ('started', 'Audit Started'),
        ('finding', 'Finding Added'),
        ('status_change', 'Status Changed'),
        ('comment', 'Comment Added'),
        ('completed', 'Audit Completed'),
        ('review_approved', 'Review Approved'),
        ('review_rejected', 'Review Rejected'),
    ]
    audit = models.ForeignKey(Audit, on_delete=models.CASCADE, related_name='timeline_events')
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    description = models.TextField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_event_type_display()} - {self.audit.title}"


class AuditReview(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('needs_info', 'Needs More Info'),
    ]
    control = models.ForeignKey('compliance.Control', on_delete=models.CASCADE)
    document = models.ForeignKey('compliance.Document', on_delete=models.SET_NULL, null=True, blank=True)
    risk = models.ForeignKey('risks.Risk', on_delete=models.SET_NULL, null=True, blank=True)
    organization = models.ForeignKey('core.Organization', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    comments = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review: {self.control.title} - {self.get_status_display()}"
