from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages as django_messages
from django.views.decorators.http import require_POST

from .models import Alert


@login_required
def alert_list(request):
    alerts = Alert.objects.filter(organization=request.user.organization)

    alert_type = request.GET.get('type')
    if alert_type:
        alerts = alerts.filter(alert_type=alert_type)

    severity = request.GET.get('severity')
    if severity:
        alerts = alerts.filter(severity=severity)

    unread_count = alerts.filter(is_read=False).count()

    context = {
        'alerts': alerts,
        'unread_count': unread_count,
        'alert_types': Alert.ALERT_TYPES,
        'current_type': alert_type,
        'current_severity': severity,
    }
    return render(request, 'alerts/alert_list.html', context)


@login_required
def alert_detail(request, pk):
    alert = get_object_or_404(Alert, pk=pk, organization=request.user.organization)
    if not alert.is_read:
        alert.is_read = True
        alert.save()
    return render(request, 'alerts/alert_detail.html', {'alert': alert})


@login_required
@require_POST
def dismiss_alert(request, pk):
    alert = get_object_or_404(Alert, pk=pk, organization=request.user.organization)
    alert.is_read = True
    alert.save()
    return redirect('alerts:alert_list')


@login_required
def generate_alerts_view(request):
    org = request.user.organization
    if org:
        count = generate_alerts(org)
        django_messages.success(request, f'{count} new alert(s) generated.')
    return redirect('alerts:alert_list')


def generate_alerts(organization):
    from cve_manager.models import CVE
    from compliance.models import Control
    from vendors.models import Vendor

    created = 0

    # Critical CVEs
    critical_cves = CVE.objects.filter(severity='CRITICAL')
    for cve in critical_cves:
        _, was_created = Alert.objects.get_or_create(
            alert_type='critical_cve',
            linked_cve=cve,
            organization=organization,
            defaults={
                'title': f'Critical CVE: {cve.cve_id}',
                'description': f'Critical vulnerability {cve.cve_id} detected (CVSS: {cve.cvss_score}). {cve.description[:200]}',
                'severity': 'critical',
            },
        )
        if was_created:
            created += 1

    # Controls without any documents (missing evidence)
    missing_controls = Control.objects.filter(
        organization=organization, documents__isnull=True
    ).distinct()
    for control in missing_controls[:10]:  # Limit to avoid alert flood
        _, was_created = Alert.objects.get_or_create(
            alert_type='missing_control',
            linked_control=control,
            organization=organization,
            defaults={
                'title': f'Missing Evidence: {control.title}',
                'description': f'Control "{control.title}" has no linked documents. Upload evidence to improve compliance.',
                'severity': 'high',
            },
        )
        if was_created:
            created += 1

    # High-risk vendors (risk_score >= 75)
    high_risk_vendors = Vendor.objects.filter(
        organization=organization, risk_score__gte=75
    )
    for vendor in high_risk_vendors:
        _, was_created = Alert.objects.get_or_create(
            alert_type='vendor_risk',
            linked_vendor=vendor,
            organization=organization,
            defaults={
                'title': f'High Risk Vendor: {vendor.name}',
                'description': f'Vendor "{vendor.name}" has a risk score of {vendor.risk_score}/100. Review assessment.',
                'severity': 'high',
            },
        )
        if was_created:
            created += 1

    return created
