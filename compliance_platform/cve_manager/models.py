from django.db import models


class CVE(models.Model):
    cve_id = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=[
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ])
    cvss_score = models.FloatField(default=0.0)
    published_date = models.DateTimeField(null=True)
    last_modified = models.DateTimeField(null=True)
    affected_products = models.TextField(blank=True)
    mapped_controls = models.ManyToManyField(
        'compliance.Control', blank=True, related_name='cves'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-published_date']

    def __str__(self):
        return self.cve_id
