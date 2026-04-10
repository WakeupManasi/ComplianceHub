from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.http import JsonResponse
from django.contrib import messages
from collections import defaultdict

from .models import AuditReview, Audit, AuditFinding, AuditTimelineEvent
from .forms import AuditForm, AuditFindingForm


# ──────────────────────────────────────────────
# Existing AuditReview views
# ──────────────────────────────────────────────

@login_required
def auditor_dashboard(request):
    """Show all pending reviews for the user's organization with stats."""
    reviews = AuditReview.objects.filter(organization=request.user.organization)

    stats = {
        'pending': reviews.filter(status='pending').count(),
        'approved': reviews.filter(status='approved').count(),
        'rejected': reviews.filter(status='rejected').count(),
        'needs_info': reviews.filter(status='needs_info').count(),
        'total': reviews.count(),
    }

    pending_reviews = reviews.filter(status='pending').select_related(
        'control', 'document', 'risk', 'reviewer'
    )

    context = {
        'reviews': pending_reviews,
        'stats': stats,
    }
    return render(request, 'auditor/dashboard.html', context)


@login_required
def review_detail(request, pk):
    """Show control, document, risk, and mitigation info for a review."""
    review = get_object_or_404(
        AuditReview.objects.select_related('control', 'document', 'risk', 'reviewer'),
        pk=pk,
        organization=request.user.organization,
    )
    return render(request, 'auditor/review_detail.html', {'review': review})


@login_required
@require_POST
def approve_review(request, pk):
    """Approve a review and mark linked risk mitigation as verified."""
    review = get_object_or_404(AuditReview, pk=pk, organization=request.user.organization)
    review.status = 'approved'
    review.reviewer = request.user
    review.reviewed_at = timezone.now()
    review.comments = request.POST.get('comments', '')
    review.save()

    # Update linked risk mitigation status to verified
    if review.risk:
        review.risk.mitigation_status = 'verified'
        review.risk.save()

    return redirect('auditor:review_detail', pk=review.pk)


@login_required
@require_POST
def reject_review(request, pk):
    """Reject a review with comments."""
    review = get_object_or_404(AuditReview, pk=pk, organization=request.user.organization)
    review.status = 'rejected'
    review.reviewer = request.user
    review.reviewed_at = timezone.now()
    review.comments = request.POST.get('comments', '')
    review.save()

    return redirect('auditor:review_detail', pk=review.pk)


# ──────────────────────────────────────────────
# New Audit Scheduling & Timeline views
# ──────────────────────────────────────────────

@login_required
def audit_list(request):
    """List all audits: upcoming, in-progress, and completed tabs."""
    org = request.user.organization
    audits = Audit.objects.filter(organization=org).select_related(
        'framework', 'lead_auditor'
    )

    status_filter = request.GET.get('status', 'all')
    if status_filter != 'all':
        audits = audits.filter(status=status_filter)

    stats = {
        'total': Audit.objects.filter(organization=org).count(),
        'scheduled': Audit.objects.filter(organization=org, status='scheduled').count(),
        'in_progress': Audit.objects.filter(organization=org, status='in_progress').count(),
        'completed': Audit.objects.filter(organization=org, status='completed').count(),
    }

    context = {'audits': audits, 'stats': stats, 'current_status': status_filter}
    return render(request, 'auditor/audit_list.html', context)


@login_required
def schedule_audit(request):
    """Schedule a new audit."""
    org = request.user.organization
    if request.method == 'POST':
        form = AuditForm(request.POST, organization=org)
        if form.is_valid():
            audit = form.save(commit=False)
            audit.organization = org
            audit.save()
            form.save_m2m()
            # Create timeline event
            AuditTimelineEvent.objects.create(
                audit=audit,
                event_type='created',
                description=f'Audit "{audit.title}" was scheduled by {request.user.username}.',
                user=request.user,
                metadata={'audit_type': audit.audit_type},
            )
            messages.success(request, f'Audit "{audit.title}" has been scheduled.')
            return redirect('auditor:audit_detail', pk=audit.pk)
    else:
        form = AuditForm(organization=org)

    return render(request, 'auditor/schedule_audit.html', {'form': form})


@login_required
def audit_detail(request, pk):
    """Show audit details with findings and timeline."""
    audit = get_object_or_404(
        Audit.objects.select_related('framework', 'lead_auditor', 'organization'),
        pk=pk,
        organization=request.user.organization,
    )
    findings = audit.findings.select_related('control', 'assigned_to').all()
    timeline_events = audit.timeline_events.select_related('user').all()

    context = {
        'audit': audit,
        'findings': findings,
        'timeline_events': timeline_events,
    }
    return render(request, 'auditor/audit_detail.html', context)


@login_required
def audit_timeline(request):
    """Show full audit timeline across all audits for the org."""
    org = request.user.organization
    events = AuditTimelineEvent.objects.filter(
        audit__organization=org
    ).select_related('audit', 'user').order_by('-created_at')

    audit_filter = request.GET.get('audit')
    if audit_filter:
        events = events.filter(audit_id=audit_filter)

    # Group events by month
    grouped = defaultdict(list)
    for event in events:
        key = event.created_at.strftime('%B %Y')
        grouped[key].append(event)

    # Completed audits summary
    completed_audits = Audit.objects.filter(
        organization=org, status='completed'
    ).select_related('framework', 'lead_auditor').order_by('-actual_end')[:6]

    all_audits = Audit.objects.filter(organization=org).order_by('-scheduled_start')

    context = {
        'grouped_events': dict(grouped),
        'completed_audits': completed_audits,
        'all_audits': all_audits,
        'current_audit_filter': audit_filter,
    }
    return render(request, 'auditor/audit_timeline.html', context)


@login_required
def add_finding(request, audit_pk):
    """Add a finding to an audit."""
    org = request.user.organization
    audit = get_object_or_404(Audit, pk=audit_pk, organization=org)

    if request.method == 'POST':
        form = AuditFindingForm(request.POST, organization=org)
        if form.is_valid():
            finding = form.save(commit=False)
            finding.audit = audit
            finding.save()
            # Create timeline event
            AuditTimelineEvent.objects.create(
                audit=audit,
                event_type='finding',
                description=f'Finding "{finding.title}" ({finding.get_severity_display()}) added by {request.user.username}.',
                user=request.user,
                metadata={'finding_id': finding.pk, 'severity': finding.severity},
            )
            messages.success(request, f'Finding "{finding.title}" has been added.')
            return redirect('auditor:audit_detail', pk=audit.pk)
    else:
        form = AuditFindingForm(organization=org)

    return render(request, 'auditor/add_finding.html', {'form': form, 'audit': audit})


@login_required
@require_POST
def update_audit_status(request, pk):
    """Update audit status (start, complete, cancel)."""
    audit = get_object_or_404(Audit, pk=pk, organization=request.user.organization)
    new_status = request.POST.get('status')
    valid_transitions = {
        'scheduled': ['in_progress', 'cancelled'],
        'in_progress': ['under_review', 'completed', 'cancelled'],
        'under_review': ['completed', 'in_progress'],
        'completed': [],
        'cancelled': ['scheduled'],
    }

    allowed = valid_transitions.get(audit.status, [])
    if new_status not in allowed:
        messages.error(request, f'Cannot transition from {audit.get_status_display()} to {new_status}.')
        return redirect('auditor:audit_detail', pk=audit.pk)

    old_status = audit.get_status_display()
    audit.status = new_status

    if new_status == 'in_progress' and not audit.actual_start:
        audit.actual_start = timezone.now().date()
    elif new_status == 'completed':
        audit.actual_end = timezone.now().date()

    audit.save()

    # Determine event type
    event_type_map = {
        'in_progress': 'started',
        'completed': 'completed',
    }
    event_type = event_type_map.get(new_status, 'status_change')

    AuditTimelineEvent.objects.create(
        audit=audit,
        event_type=event_type,
        description=f'Status changed from {old_status} to {audit.get_status_display()} by {request.user.username}.',
        user=request.user,
        metadata={'old_status': old_status, 'new_status': new_status},
    )
    messages.success(request, f'Audit status updated to {audit.get_status_display()}.')
    return redirect('auditor:audit_detail', pk=audit.pk)


@login_required
def audit_calendar(request):
    """Calendar view of scheduled audits - returns JSON for calendar widget."""
    org = request.user.organization
    audits = Audit.objects.filter(organization=org).select_related('framework', 'lead_auditor')

    status_colors = {
        'scheduled': '#6366f1',
        'in_progress': '#f59e0b',
        'under_review': '#8b5cf6',
        'completed': '#10b981',
        'cancelled': '#ef4444',
    }

    events = []
    for audit in audits:
        events.append({
            'id': audit.pk,
            'title': audit.title,
            'start': audit.scheduled_start.isoformat(),
            'end': audit.scheduled_end.isoformat(),
            'color': status_colors.get(audit.status, '#6366f1'),
            'status': audit.status,
            'status_display': audit.get_status_display(),
            'audit_type': audit.get_audit_type_display(),
            'url': f'/auditor/audits/{audit.pk}/',
        })

    return JsonResponse(events, safe=False)
