from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count

from .forms import RegisterForm, OnboardingForm, LoginForm
from .models import (
    Organization, OnboardingQuestion, OnboardingResponse, ComplianceSuggestion, User,
)


def landing_page(request):
    """Public landing page with parallax scrolling."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'core/landing.html')


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully. Please complete onboarding.')
            return redirect('onboarding')
    else:
        form = RegisterForm()
    return render(request, 'core/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, 'Logged in successfully.')
            if not user.organization:
                return redirect('onboarding')
            return redirect('dashboard')
    else:
        form = LoginForm()
    return render(request, 'core/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')


# ---------------------------------------------------------------------------
# Seed onboarding questions
# ---------------------------------------------------------------------------

COMMON_QUESTIONS = [
    {
        'question_text': 'Do you handle personally identifiable information (PII)?',
        'question_type': 'boolean',
        'category': 'data',
        'order': 1,
        'help_text': 'PII includes names, addresses, emails, SSNs, etc.',
    },
    {
        'question_text': 'Do you process financial/payment data?',
        'question_type': 'boolean',
        'category': 'data',
        'order': 2,
        'help_text': 'Credit card numbers, bank accounts, transaction data.',
    },
    {
        'question_text': 'Do you handle health records or PHI?',
        'question_type': 'boolean',
        'category': 'data',
        'order': 3,
        'help_text': 'Protected Health Information including medical records.',
    },
    {
        'question_text': 'Do you have remote/distributed workers?',
        'question_type': 'boolean',
        'category': 'infrastructure',
        'order': 4,
        'help_text': 'Employees or contractors working outside your offices.',
    },
    {
        'question_text': 'Is your infrastructure cloud-hosted?',
        'question_type': 'boolean',
        'category': 'infrastructure',
        'order': 5,
        'help_text': 'AWS, Azure, GCP, or other cloud providers.',
    },
    {
        'question_text': 'How many third-party vendors do you work with?',
        'question_type': 'choice',
        'category': 'infrastructure',
        'order': 6,
        'options': ['0', '1-5', '6-20', '21-50', '50+'],
        'help_text': 'Vendors with access to your systems or data.',
    },
    {
        'question_text': 'What is your current security maturity level?',
        'question_type': 'scale',
        'category': 'security',
        'order': 7,
        'help_text': '1=None, 2=Basic, 3=Developing, 4=Advanced, 5=Optimized',
    },
    {
        'question_text': 'Do you have a dedicated security team?',
        'question_type': 'boolean',
        'category': 'security',
        'order': 8,
        'help_text': 'A team or individual focused on information security.',
    },
    {
        'question_text': 'Have you experienced a data breach in the last 2 years?',
        'question_type': 'boolean',
        'category': 'security',
        'order': 9,
        'help_text': 'Any unauthorized access to sensitive data.',
    },
    {
        'question_text': 'Do you have existing compliance certifications?',
        'question_type': 'multi',
        'category': 'security',
        'order': 10,
        'options': ['ISO 27001', 'SOC2', 'GDPR', 'PCI DSS', 'HIPAA', 'None'],
        'help_text': 'Select all that currently apply.',
    },
]

INDUSTRY_QUESTIONS = {
    'it_saas': [
        {
            'question_text': 'Do you offer SaaS to enterprise clients?',
            'question_type': 'boolean',
            'category': 'industry_it',
            'order': 101,
            'help_text': 'Enterprise B2B software-as-a-service offerings.',
        },
        {
            'question_text': 'Do you use CI/CD pipelines?',
            'question_type': 'boolean',
            'category': 'industry_it',
            'order': 102,
            'help_text': 'Continuous integration and deployment automation.',
        },
        {
            'question_text': 'Do you perform regular penetration testing?',
            'question_type': 'boolean',
            'category': 'industry_it',
            'order': 103,
            'help_text': 'Scheduled security testing of your applications.',
        },
    ],
    'banking': [
        {
            'question_text': 'Do you process card payments?',
            'question_type': 'boolean',
            'category': 'industry_banking',
            'order': 101,
            'help_text': 'Credit/debit card payment processing.',
        },
        {
            'question_text': 'Are you regulated by RBI/Central Bank?',
            'question_type': 'boolean',
            'category': 'industry_banking',
            'order': 102,
            'help_text': 'Subject to central banking authority regulations.',
        },
        {
            'question_text': 'Do you perform KYC verification?',
            'question_type': 'boolean',
            'category': 'industry_banking',
            'order': 103,
            'help_text': 'Know Your Customer identity verification.',
        },
    ],
    'healthcare': [
        {
            'question_text': 'Do you transmit ePHI electronically?',
            'question_type': 'boolean',
            'category': 'industry_healthcare',
            'order': 101,
            'help_text': 'Electronic Protected Health Information transmission.',
        },
        {
            'question_text': 'Do you use EHR/EMR systems?',
            'question_type': 'boolean',
            'category': 'industry_healthcare',
            'order': 102,
            'help_text': 'Electronic Health/Medical Record systems.',
        },
        {
            'question_text': 'Are you a covered entity or business associate?',
            'question_type': 'boolean',
            'category': 'industry_healthcare',
            'order': 103,
            'help_text': 'Under HIPAA definitions.',
        },
    ],
    'insurance': [
        {
            'question_text': 'Do you handle policyholder data?',
            'question_type': 'boolean',
            'category': 'industry_insurance',
            'order': 101,
            'help_text': 'Personal data of insurance policyholders.',
        },
        {
            'question_text': 'Are you regulated by IRDAI?',
            'question_type': 'boolean',
            'category': 'industry_insurance',
            'order': 102,
            'help_text': 'Insurance Regulatory and Development Authority.',
        },
        {
            'question_text': 'Do you process claims data?',
            'question_type': 'boolean',
            'category': 'industry_insurance',
            'order': 103,
            'help_text': 'Insurance claims processing and management.',
        },
    ],
    'government': [
        {
            'question_text': 'Do you handle classified data?',
            'question_type': 'boolean',
            'category': 'industry_government',
            'order': 101,
            'help_text': 'Government classified or restricted information.',
        },
        {
            'question_text': 'Are you subject to RTI/FOIA?',
            'question_type': 'boolean',
            'category': 'industry_government',
            'order': 102,
            'help_text': 'Right to Information or Freedom of Information Act.',
        },
        {
            'question_text': 'Do you interface with citizen data?',
            'question_type': 'boolean',
            'category': 'industry_government',
            'order': 103,
            'help_text': 'Collecting or processing citizen personal data.',
        },
    ],
}


def seed_onboarding_questions():
    """Seed all onboarding questions if they don't exist."""
    if OnboardingQuestion.objects.exists():
        return

    for q in COMMON_QUESTIONS:
        OnboardingQuestion.objects.create(**q)

    for industry, questions in INDUSTRY_QUESTIONS.items():
        for q in questions:
            OnboardingQuestion.objects.create(**q)


# ---------------------------------------------------------------------------
# Compliance suggestion generation
# ---------------------------------------------------------------------------

def generate_compliance_suggestions(organization, responses):
    """Analyze onboarding responses and create ComplianceSuggestion records."""
    # Clear old suggestions
    ComplianceSuggestion.objects.filter(organization=organization).delete()

    suggestions = []
    industry = organization.industry

    # Build a lookup: question_text -> answer
    answer_map = {}
    for resp in responses:
        answer_map[resp.question.question_text] = resp.answer

    handles_pii = answer_map.get('Do you handle personally identifiable information (PII)?', False)
    handles_financial = answer_map.get('Do you process financial/payment data?', False)
    handles_health = answer_map.get('Do you handle health records or PHI?', False)
    has_remote = answer_map.get('Do you have remote/distributed workers?', False)
    cloud_hosted = answer_map.get('Is your infrastructure cloud-hosted?', False)
    vendor_count = answer_map.get('How many third-party vendors do you work with?', '0')
    maturity = answer_map.get('What is your current security maturity level?', 3)
    has_security_team = answer_map.get('Do you have a dedicated security team?', False)
    had_breach = answer_map.get('Have you experienced a data breach in the last 2 years?', False)
    existing_certs = answer_map.get('Do you have existing compliance certifications?', [])

    # Update org fields
    organization.handles_pii = bool(handles_pii)
    organization.handles_financial = bool(handles_financial)
    organization.handles_health = bool(handles_health)
    organization.has_remote_workers = bool(has_remote)
    organization.cloud_hosted = bool(cloud_hosted)

    vendor_map = {'0': 0, '1-5': 3, '6-20': 13, '21-50': 35, '50+': 60}
    organization.num_third_party_vendors = vendor_map.get(vendor_count, 0)

    # Calculate risk score (0-100)
    risk = 30  # baseline
    if handles_pii:
        risk += 10
    if handles_financial:
        risk += 15
    if handles_health:
        risk += 15
    if had_breach:
        risk += 15
    if not has_security_team:
        risk += 10
    try:
        maturity_val = int(maturity)
    except (ValueError, TypeError):
        maturity_val = 3
    risk -= (maturity_val - 1) * 5  # higher maturity reduces risk
    if vendor_count in ('21-50', '50+'):
        risk += 10
    organization.risk_score = max(0, min(100, risk))

    # Determine data sensitivity
    if handles_health or (handles_financial and handles_pii):
        organization.data_sensitivity = 'critical'
    elif handles_financial or handles_pii:
        organization.data_sensitivity = 'high'
    elif cloud_hosted:
        organization.data_sensitivity = 'medium'
    else:
        organization.data_sensitivity = 'low'

    organization.save()

    # --- Framework suggestions ---

    # ISO 27001 - recommended for most
    if industry in ('it_saas', 'banking', 'insurance', 'government'):
        priority = 'required' if organization.risk_score > 50 else 'recommended'
        if 'ISO 27001' not in existing_certs:
            suggestions.append(('ISO 27001', 'Industry-standard information security management framework essential for your industry.', priority))

    # SOC 2 - IT/SaaS
    if industry == 'it_saas':
        saas_enterprise = answer_map.get('Do you offer SaaS to enterprise clients?', False)
        if saas_enterprise:
            suggestions.append(('SOC 2', 'Enterprise SaaS clients typically require SOC 2 compliance for vendor evaluation.', 'required'))
        else:
            suggestions.append(('SOC 2', 'SOC 2 demonstrates strong security practices for technology companies.', 'recommended'))

    # GDPR / DPDP - PII handling
    if handles_pii:
        if 'GDPR' not in existing_certs:
            suggestions.append(('GDPR', 'You handle personally identifiable information which requires GDPR compliance for EU data subjects.', 'required'))
        suggestions.append(('DPDP Act 2023', 'India\'s Digital Personal Data Protection Act applies to organizations handling PII of Indian citizens.', 'recommended'))

    # PCI DSS - financial/payment data
    if handles_financial:
        card_payments = answer_map.get('Do you process card payments?', False)
        if card_payments or industry == 'banking':
            if 'PCI DSS' not in existing_certs:
                suggestions.append(('PCI DSS', 'Processing payment card data requires PCI DSS compliance.', 'required'))
        else:
            suggestions.append(('PCI DSS', 'You process financial data; PCI DSS ensures payment data security.', 'recommended'))

    # HIPAA - health data
    if handles_health or industry == 'healthcare':
        ephi = answer_map.get('Do you transmit ePHI electronically?', False)
        covered = answer_map.get('Are you a covered entity or business associate?', False)
        if ephi or covered:
            if 'HIPAA' not in existing_certs:
                suggestions.append(('HIPAA', 'Handling electronic Protected Health Information requires HIPAA compliance.', 'required'))
        else:
            suggestions.append(('HIPAA', 'Healthcare organizations should consider HIPAA for health data protection.', 'recommended'))

    # RBI Cyber Security Framework - banking
    if industry == 'banking':
        rbi_regulated = answer_map.get('Are you regulated by RBI/Central Bank?', False)
        if rbi_regulated:
            suggestions.append(('RBI Cyber Security Framework', 'RBI-regulated entities must comply with the Cyber Security Framework.', 'required'))
        else:
            suggestions.append(('RBI Cyber Security Framework', 'Banking organizations benefit from RBI Cyber Security Framework alignment.', 'optional'))

    # Additional suggestions based on context
    if cloud_hosted and industry == 'it_saas':
        suggestions.append(('CSA STAR', 'Cloud-hosted infrastructure benefits from Cloud Security Alliance STAR certification.', 'optional'))

    if industry == 'government':
        classified = answer_map.get('Do you handle classified data?', False)
        citizen_data = answer_map.get('Do you interface with citizen data?', False)
        suggestions.append(('ISO 27001', 'Government agencies need robust information security management.', 'required'))
        if citizen_data:
            suggestions.append(('DPDP Act 2023', 'Handling citizen data requires compliance with India\'s data protection law.', 'required'))
        if classified:
            suggestions.append(('NIST SP 800-53', 'Classified data handling benefits from NIST security controls framework.', 'recommended'))

    if industry == 'insurance':
        irdai = answer_map.get('Are you regulated by IRDAI?', False)
        if irdai:
            suggestions.append(('IRDAI Cyber Security Guidelines', 'IRDAI-regulated insurers must follow IRDAI cyber security guidelines.', 'required'))
        policyholder = answer_map.get('Do you handle policyholder data?', False)
        if policyholder:
            suggestions.append(('DPDP Act 2023', 'Policyholder data handling requires compliance with data protection regulations.', 'recommended'))

    if had_breach:
        suggestions.append(('NIST Cybersecurity Framework', 'Post-breach organizations benefit significantly from the NIST CSF to strengthen security posture.', 'recommended'))

    # Deduplicate by framework_name (keep highest priority)
    priority_rank = {'required': 0, 'recommended': 1, 'optional': 2}
    seen = {}
    for name, reason, priority in suggestions:
        if name not in seen or priority_rank[priority] < priority_rank[seen[name][1]]:
            seen[name] = (reason, priority)

    for name, (reason, priority) in seen.items():
        ComplianceSuggestion.objects.create(
            organization=organization,
            framework_name=name,
            reason=reason,
            priority=priority,
        )

    return ComplianceSuggestion.objects.filter(organization=organization)


# ---------------------------------------------------------------------------
# Multi-step onboarding views
# ---------------------------------------------------------------------------

@login_required
def onboarding_view(request):
    """Redirect to current onboarding step."""
    if request.user.organization and request.user.organization.onboarding_completed:
        return redirect('dashboard')
    step = request.session.get('onboarding_step', 1)
    return redirect(f'onboarding_step{step}')


@login_required
def onboarding_step1(request):
    """Step 1: Basic organization info."""
    if request.user.organization and request.user.organization.onboarding_completed:
        return redirect('dashboard')

    if request.method == 'POST':
        form = OnboardingForm(request.POST)
        if form.is_valid():
            org = form.save()
            request.user.organization = org
            request.user.save()
            request.session['onboarding_step'] = 2
            return redirect('onboarding_step2')
    else:
        # Pre-fill if org already exists (going back)
        org = request.user.organization
        if org:
            form = OnboardingForm(instance=org)
        else:
            form = OnboardingForm()

    return render(request, 'core/onboarding_step1.html', {'form': form})


@login_required
def onboarding_step2(request):
    """Step 2: Common questions for all industries."""
    org = request.user.organization
    if not org:
        return redirect('onboarding_step1')
    if org.onboarding_completed:
        return redirect('dashboard')

    # Seed questions on first access
    seed_onboarding_questions()

    common_categories = ['data', 'infrastructure', 'security']
    questions = OnboardingQuestion.objects.filter(category__in=common_categories)

    if request.method == 'POST':
        for q in questions:
            field_name = f'question_{q.id}'
            if q.question_type == 'boolean':
                answer = request.POST.get(field_name) == 'yes'
            elif q.question_type == 'choice':
                answer = request.POST.get(field_name, '')
            elif q.question_type == 'multi':
                answer = request.POST.getlist(field_name)
            elif q.question_type == 'scale':
                try:
                    answer = int(request.POST.get(field_name, 3))
                except ValueError:
                    answer = 3
            else:
                answer = request.POST.get(field_name, '')

            OnboardingResponse.objects.update_or_create(
                organization=org,
                question=q,
                defaults={'answer': answer},
            )

        request.session['onboarding_step'] = 3
        return redirect('onboarding_step3')

    # Load existing answers for back navigation
    existing = {
        r.question_id: r.answer
        for r in OnboardingResponse.objects.filter(organization=org, question__in=questions)
    }

    return render(request, 'core/onboarding_step2.html', {
        'questions': questions,
        'existing': existing,
    })


@login_required
def onboarding_step3(request):
    """Step 3: Industry-specific questions."""
    org = request.user.organization
    if not org:
        return redirect('onboarding_step1')
    if org.onboarding_completed:
        return redirect('dashboard')

    industry = org.industry
    category_map = {
        'it_saas': 'industry_it',
        'banking': 'industry_banking',
        'healthcare': 'industry_healthcare',
        'insurance': 'industry_insurance',
        'government': 'industry_government',
    }
    category = category_map.get(industry, 'industry_it')
    questions = OnboardingQuestion.objects.filter(category=category)

    if request.method == 'POST':
        for q in questions:
            field_name = f'question_{q.id}'
            if q.question_type == 'boolean':
                answer = request.POST.get(field_name) == 'yes'
            elif q.question_type == 'choice':
                answer = request.POST.get(field_name, '')
            elif q.question_type == 'multi':
                answer = request.POST.getlist(field_name)
            elif q.question_type == 'scale':
                try:
                    answer = int(request.POST.get(field_name, 3))
                except ValueError:
                    answer = 3
            else:
                answer = request.POST.get(field_name, '')

            OnboardingResponse.objects.update_or_create(
                organization=org,
                question=q,
                defaults={'answer': answer},
            )

        # Generate suggestions
        all_responses = OnboardingResponse.objects.filter(
            organization=org
        ).select_related('question')
        generate_compliance_suggestions(org, all_responses)

        request.session['onboarding_step'] = 4
        return redirect('onboarding_step4')

    existing = {
        r.question_id: r.answer
        for r in OnboardingResponse.objects.filter(organization=org, question__in=questions)
    }

    industry_display = org.get_industry_display()

    return render(request, 'core/onboarding_step3.html', {
        'questions': questions,
        'existing': existing,
        'industry_display': industry_display,
    })


@login_required
def onboarding_step4(request):
    """Step 4: Review and accept compliance suggestions."""
    org = request.user.organization
    if not org:
        return redirect('onboarding_step1')
    if org.onboarding_completed:
        return redirect('dashboard')

    suggestions = ComplianceSuggestion.objects.filter(organization=org)

    if request.method == 'POST':
        accepted_ids = request.POST.getlist('accepted_suggestions')
        suggestions.update(is_accepted=False)
        if accepted_ids:
            suggestions.filter(id__in=accepted_ids).update(is_accepted=True)

        org.onboarding_completed = True
        org.save()

        # Load accepted frameworks
        try:
            from compliance.views import load_frameworks_for_org
            load_frameworks_for_org(org)
        except (ImportError, AttributeError, Exception):
            pass

        # Clean up session
        if 'onboarding_step' in request.session:
            del request.session['onboarding_step']

        messages.success(request, 'Onboarding complete! Your compliance dashboard is ready.')
        return redirect('dashboard')

    return render(request, 'core/onboarding_step4.html', {
        'suggestions': suggestions,
        'organization': org,
    })


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@login_required
def dashboard_view(request):
    user = request.user
    org = user.organization

    context = {
        'compliance_percentage': 0,
        'total_controls': 0,
        'covered_controls': 0,
        'missing_controls': 0,
        'active_risks': 0,
        'cve_count': 0,
        'vendor_count': 0,
        'unread_alerts': 0,
        'risks_by_severity': {'critical': 0, 'high': 0, 'medium': 0, 'low': 0},
        'recent_alerts': [],
        'recent_cves': [],
        'organization': org,
    }

    if not org:
        return render(request, 'core/dashboard.html', context)

    # Compliance percentage
    try:
        from compliance.models import Control, Document
        total = Control.objects.filter(organization=org).count()
        if total > 0:
            covered = Control.objects.filter(
                organization=org, documents__isnull=False
            ).distinct().count()
            context['total_controls'] = total
            context['covered_controls'] = covered
            context['missing_controls'] = total - covered
            context['compliance_percentage'] = int((covered / total) * 100)
    except Exception:
        pass

    # Active risks
    try:
        from risks.models import Risk
        risks = Risk.objects.filter(organization=org)
        context['active_risks'] = risks.exclude(
            mitigation_status__in=['mitigated', 'verified']
        ).count()
        severity_counts = risks.values('severity').annotate(count=Count('id'))
        for item in severity_counts:
            context['risks_by_severity'][item['severity']] = item['count']
    except Exception:
        pass

    # CVE count
    try:
        from cve_manager.models import CVE
        context['cve_count'] = CVE.objects.count()
        context['recent_cves'] = CVE.objects.all()[:5]
    except Exception:
        pass

    # Vendor count
    try:
        from vendors.models import Vendor
        context['vendor_count'] = Vendor.objects.filter(organization=org).count()
    except Exception:
        pass

    # Alerts
    try:
        from alerts.models import Alert
        alerts = Alert.objects.filter(organization=org)
        context['unread_alerts'] = alerts.filter(is_read=False).count()
        context['recent_alerts'] = alerts[:5]
    except Exception:
        pass

    return render(request, 'core/dashboard.html', context)


# ---------------------------------------------------------------------------
# Organization User Management
# ---------------------------------------------------------------------------

@login_required
def org_users(request):
    """List all users in the organization."""
    if request.user.role not in ('super_admin', 'client_admin'):
        messages.error(request, 'You do not have permission to manage users.')
        return redirect('dashboard')
    org = request.user.organization
    users = User.objects.filter(organization=org).order_by('-date_joined')
    context = {'org_users': users, 'organization': org}
    return render(request, 'core/org_users.html', context)


@login_required
def invite_user(request):
    """Invite/create a new user for the organization."""
    if request.user.role not in ('super_admin', 'client_admin'):
        messages.error(request, 'You do not have permission.')
        return redirect('dashboard')
    if request.method == 'POST':
        # Get form data
        username = request.POST.get('username')
        email = request.POST.get('email')
        role = request.POST.get('role')
        password = request.POST.get('password')
        # Create user
        from django.contrib.auth import get_user_model
        UserModel = get_user_model()
        if UserModel.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
        else:
            user = UserModel.objects.create_user(
                username=username, email=email, password=password,
                role=role, organization=request.user.organization
            )
            messages.success(request, f'User {username} created successfully.')
            return redirect('org_users')
    roles = [r for r in User.ROLE_CHOICES if r[0] != 'super_admin']
    return render(request, 'core/invite_user.html', {'roles': roles})


@login_required
def edit_user(request, pk):
    """Edit a user's role."""
    if request.user.role not in ('super_admin', 'client_admin'):
        messages.error(request, 'You do not have permission.')
        return redirect('dashboard')
    from django.shortcuts import get_object_or_404
    target_user = get_object_or_404(User, pk=pk, organization=request.user.organization)
    if request.method == 'POST':
        new_role = request.POST.get('role')
        if new_role:
            target_user.role = new_role
            target_user.save()
            messages.success(request, f'Updated role for {target_user.username}.')
        return redirect('org_users')
    roles = [r for r in User.ROLE_CHOICES if r[0] != 'super_admin']
    return render(request, 'core/edit_user.html', {'target_user': target_user, 'roles': roles})


@login_required
def remove_user(request, pk):
    """Remove a user from the organization."""
    if request.user.role not in ('super_admin', 'client_admin'):
        messages.error(request, 'You do not have permission.')
        return redirect('dashboard')
    from django.shortcuts import get_object_or_404
    target_user = get_object_or_404(User, pk=pk, organization=request.user.organization)
    if request.method == 'POST' and target_user != request.user:
        target_user.organization = None
        target_user.is_active = False
        target_user.save()
        messages.success(request, f'User {target_user.username} removed.')
    return redirect('org_users')


@login_required
def org_settings(request):
    """Organization settings page."""
    if request.user.role not in ('super_admin', 'client_admin'):
        messages.error(request, 'You do not have permission.')
        return redirect('dashboard')
    org = request.user.organization
    if request.method == 'POST':
        org.name = request.POST.get('name', org.name)
        org.country = request.POST.get('country', org.country)
        org.save()
        messages.success(request, 'Organization settings updated.')
        return redirect('org_settings')
    return render(request, 'core/org_settings.html', {'organization': org})
