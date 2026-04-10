from django.contrib.auth.models import AbstractUser
from django.db import models


class Organization(models.Model):
    name = models.CharField(max_length=255)
    industry = models.CharField(max_length=50, choices=[
        ('it_saas', 'IT / SaaS'),
        ('banking', 'Banking / Fintech'),
        ('healthcare', 'Healthcare'),
        ('insurance', 'Insurance'),
        ('government', 'Government'),
        ('ecommerce', 'E-Commerce / Retail'),
        ('telecom', 'Telecommunications'),
        ('education', 'Education / EdTech'),
        ('manufacturing', 'Manufacturing / Industrial'),
        ('pharma', 'Pharmaceutical / Biotech'),
        ('energy', 'Energy / Power / Utilities'),
        ('legal', 'Legal / Law Firm'),
        ('logistics', 'Logistics / Supply Chain'),
        ('media', 'Media / Entertainment'),
        ('nbfc', 'NBFC / Microfinance'),
        ('realestate', 'Real Estate / PropTech'),
        ('defence', 'Defence / Aerospace'),
    ])
    country = models.CharField(max_length=100)
    company_size = models.CharField(max_length=50, choices=[
        ('1-50', '1-50'),
        ('51-200', '51-200'),
        ('201-500', '201-500'),
        ('501-1000', '501-1000'),
        ('1000+', '1000+'),
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    onboarding_completed = models.BooleanField(default=False)
    risk_score = models.IntegerField(default=0)
    data_sensitivity = models.CharField(max_length=20, default='medium', choices=[
        ('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical'),
    ])
    handles_pii = models.BooleanField(default=False)
    handles_financial = models.BooleanField(default=False)
    handles_health = models.BooleanField(default=False)
    has_remote_workers = models.BooleanField(default=False)
    cloud_hosted = models.BooleanField(default=False)
    num_third_party_vendors = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class User(AbstractUser):
    ROLE_CHOICES = [
        ('super_admin', 'Super Admin'),
        ('client_admin', 'Client Admin'),
        ('compliance_manager', 'Compliance Manager'),
        ('auditor', 'Auditor'),
        ('vendor_user', 'Vendor User'),
    ]
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default='client_admin')
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, null=True, blank=True
    )

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class OnboardingQuestion(models.Model):
    QUESTION_TYPES = [
        ('boolean', 'Yes/No'),
        ('choice', 'Single Choice'),
        ('multi', 'Multiple Choice'),
        ('text', 'Free Text'),
        ('scale', 'Scale 1-5'),
    ]
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    options = models.JSONField(default=list, blank=True)
    category = models.CharField(max_length=30, choices=[
        ('basic', 'Basic'),
        ('security', 'Security Posture'),
        ('data', 'Data Handling'),
        ('infrastructure', 'Infrastructure'),
        ('industry_it', 'IT/SaaS Specific'),
        ('industry_banking', 'Banking Specific'),
        ('industry_healthcare', 'Healthcare Specific'),
        ('industry_insurance', 'Insurance Specific'),
        ('industry_government', 'Government Specific'),
        ('industry_ecommerce', 'E-Commerce Specific'),
        ('industry_telecom', 'Telecom Specific'),
        ('industry_pharma', 'Pharma Specific'),
        ('industry_energy', 'Energy Specific'),
        ('industry_manufacturing', 'Manufacturing Specific'),
        ('industry_nbfc', 'NBFC Specific'),
        ('industry_defence', 'Defence Specific'),
    ])
    is_required = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    help_text = models.TextField(blank=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.question_text[:80]


class OnboardingResponse(models.Model):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name='onboarding_responses'
    )
    question = models.ForeignKey(OnboardingQuestion, on_delete=models.CASCADE)
    answer = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['organization', 'question']


class ComplianceSuggestion(models.Model):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name='suggestions'
    )
    framework_name = models.CharField(max_length=255)
    reason = models.TextField()
    priority = models.CharField(max_length=20, choices=[
        ('required', 'Required'),
        ('recommended', 'Recommended'),
        ('optional', 'Optional'),
    ])
    is_accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
