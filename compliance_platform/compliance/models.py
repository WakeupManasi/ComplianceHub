from django.db import models
from django.conf import settings


class ComplianceFramework(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    industry = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Clause(models.Model):
    framework = models.ForeignKey(ComplianceFramework, on_delete=models.CASCADE, related_name='clauses')
    number = models.CharField(max_length=20)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.framework.name} - {self.number}: {self.title}"


class Control(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    clause = models.ForeignKey(Clause, on_delete=models.CASCADE, related_name='controls')
    framework = models.ForeignKey(ComplianceFramework, on_delete=models.CASCADE, related_name='controls')
    is_mandatory = models.BooleanField(default=True)
    organization = models.ForeignKey('core.Organization', on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Document(models.Model):
    DOC_TYPES = [
        ('policy', 'Policy'),
        ('sop', 'SOP'),
        ('evidence', 'Evidence'),
    ]
    title = models.CharField(max_length=255)
    doc_type = models.CharField(max_length=20, choices=DOC_TYPES)
    file = models.FileField(upload_to='documents/')
    controls = models.ManyToManyField(Control, blank=True, related_name='documents')
    organization = models.ForeignKey('core.Organization', on_delete=models.CASCADE)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    storage_link = models.URLField(blank=True, help_text='External storage link (S3/Drive)')
    checksum_sha256 = models.CharField(max_length=64, blank=True)
    checksum_md5 = models.CharField(max_length=32, blank=True)
    file_size = models.BigIntegerField(default=0)
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_documents')
    version = models.IntegerField(default=1)
    previous_version = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='newer_versions')

    def __str__(self):
        return self.title


class Guideline(models.Model):
    industry = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=[
        ('policy', 'Required Policy'),
        ('practice', 'Best Practice'),
    ])

    def __str__(self):
        return self.title
