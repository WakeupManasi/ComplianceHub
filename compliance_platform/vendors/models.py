from django.db import models


class Vendor(models.Model):
    name = models.CharField(max_length=255)
    services = models.TextField()
    tech_stack = models.TextField(blank=True)
    risk_score = models.IntegerField(default=50)  # 0-100
    organization = models.ForeignKey('core.Organization', on_delete=models.CASCADE)
    contact_email = models.EmailField(blank=True)
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'),
        ('under_review', 'Under Review'),
        ('suspended', 'Suspended'),
    ], default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    @property
    def risk_level(self):
        if self.risk_score >= 75:
            return 'Critical'
        if self.risk_score >= 50:
            return 'High'
        if self.risk_score >= 25:
            return 'Medium'
        return 'Low'


class VendorMonitoring(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='monitoring_events')
    event_type = models.CharField(max_length=50, choices=[
        ('sla_breach', 'SLA Breach'),
        ('incident', 'Security Incident'),
        ('risk_change', 'Risk Score Change'),
        ('negative_news', 'Negative News'),
        ('legal_issue', 'Legal Issue'),
    ])
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.vendor.name} - {self.get_event_type_display()}"
