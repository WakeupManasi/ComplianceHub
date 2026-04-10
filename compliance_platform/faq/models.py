from django.db import models


class FAQ(models.Model):
    question = models.TextField()
    answer = models.TextField()
    category = models.CharField(max_length=50, choices=[
        ('general', 'General'),
        ('compliance', 'Compliance'),
        ('vendor', 'Vendor Management'),
        ('cve', 'CVE & Vulnerabilities'),
        ('audit', 'Audit'),
    ])
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'

    def __str__(self):
        return self.question
