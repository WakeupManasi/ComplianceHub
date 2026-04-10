from django.conf import settings
from django.db import models


class Risk(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ])
    linked_control = models.ForeignKey(
        'compliance.Control', on_delete=models.SET_NULL, null=True, blank=True
    )
    linked_cve = models.ForeignKey(
        'cve_manager.CVE', on_delete=models.SET_NULL, null=True, blank=True
    )
    linked_vendor = models.ForeignKey(
        'vendors.Vendor', on_delete=models.SET_NULL, null=True, blank=True
    )
    organization = models.ForeignKey('core.Organization', on_delete=models.CASCADE)
    mitigation_status = models.CharField(max_length=30, choices=[
        ('identified', 'Identified'),
        ('in_progress', 'In Progress'),
        ('mitigated', 'Mitigated'),
        ('verified', 'Verified by Auditor'),
        ('accepted', 'Risk Accepted'),
    ], default='identified')
    mitigation_plan = models.TextField(blank=True)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
