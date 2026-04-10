from django.db import models


class Alert(models.Model):
    ALERT_TYPES = [
        ('critical_cve', 'Critical CVE'),
        ('missing_control', 'Missing Control'),
        ('vendor_risk', 'Vendor Risk Spike'),
        ('compliance_gap', 'Compliance Gap'),
        ('sla_breach', 'SLA Breach'),
    ]
    title = models.CharField(max_length=255)
    alert_type = models.CharField(max_length=30, choices=ALERT_TYPES)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=[
        ('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')
    ])
    organization = models.ForeignKey('core.Organization', on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)
    linked_cve = models.ForeignKey('cve_manager.CVE', on_delete=models.SET_NULL, null=True, blank=True)
    linked_vendor = models.ForeignKey('vendors.Vendor', on_delete=models.SET_NULL, null=True, blank=True)
    linked_control = models.ForeignKey('compliance.Control', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
