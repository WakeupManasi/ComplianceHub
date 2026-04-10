import logging

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_datetime

from compliance.models import Control
from .models import CVE

logger = logging.getLogger(__name__)


@login_required
def cve_list(request):
    cves = CVE.objects.all()
    severity_filter = request.GET.get('severity')
    if severity_filter:
        cves = cves.filter(severity=severity_filter)
    return render(request, 'cve_manager/cve_list.html', {
        'cves': cves,
        'severity_filter': severity_filter,
    })


@login_required
def cve_detail(request, pk):
    cve = get_object_or_404(CVE, pk=pk)
    mapped_controls = cve.mapped_controls.all()
    available_controls = Control.objects.filter(
        organization=request.user.organization
    ).exclude(pk__in=mapped_controls.values_list('pk', flat=True))
    return render(request, 'cve_manager/cve_detail.html', {
        'cve': cve,
        'mapped_controls': mapped_controls,
        'available_controls': available_controls,
    })


@login_required
def fetch_cves(request):
    """Fetch recent CVEs from the NVD API."""
    api_url = getattr(settings, 'NVD_API_URL', 'https://services.nvd.nist.gov/rest/json/cves/2.0')
    created_count = 0
    error_message = None

    try:
        response = requests.get(api_url, params={'resultsPerPage': 20}, timeout=30)
        response.raise_for_status()
        data = response.json()

        for vuln in data.get('vulnerabilities', []):
            cve_data = vuln.get('cve', {})
            cve_id = cve_data.get('id', '')

            if not cve_id or CVE.objects.filter(cve_id=cve_id).exists():
                continue

            # Extract description (English preferred)
            description = ''
            for desc in cve_data.get('descriptions', []):
                if desc.get('lang') == 'en':
                    description = desc.get('value', '')
                    break
            if not description:
                descriptions = cve_data.get('descriptions', [])
                if descriptions:
                    description = descriptions[0].get('value', '')

            # Extract CVSS score and severity
            cvss_score = 0.0
            severity = 'LOW'
            metrics = cve_data.get('metrics', {})

            # Try CVSS v3.1 first, then v3.0, then v2.0
            cvss_metrics = (
                metrics.get('cvssMetricV31', [])
                or metrics.get('cvssMetricV30', [])
            )
            if cvss_metrics:
                cvss_data = cvss_metrics[0].get('cvssData', {})
                cvss_score = cvss_data.get('baseScore', 0.0)
                severity = cvss_data.get('baseSeverity', 'LOW').upper()
            else:
                cvss_v2 = metrics.get('cvssMetricV2', [])
                if cvss_v2:
                    cvss_data = cvss_v2[0].get('cvssData', {})
                    cvss_score = cvss_data.get('baseScore', 0.0)
                    # Map v2 score to severity
                    if cvss_score >= 9.0:
                        severity = 'CRITICAL'
                    elif cvss_score >= 7.0:
                        severity = 'HIGH'
                    elif cvss_score >= 4.0:
                        severity = 'MEDIUM'
                    else:
                        severity = 'LOW'

            # Ensure severity is valid
            if severity not in ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL'):
                severity = 'LOW'

            # Extract dates
            published_date = parse_datetime(cve_data.get('published', ''))
            last_modified = parse_datetime(cve_data.get('lastModified', ''))

            # Extract affected products from configurations
            affected_products = ''
            configurations = cve_data.get('configurations', [])
            product_list = []
            for config in configurations:
                for node in config.get('nodes', []):
                    for cpe_match in node.get('cpeMatch', []):
                        criteria = cpe_match.get('criteria', '')
                        if criteria:
                            product_list.append(criteria)
            if product_list:
                affected_products = '\n'.join(product_list[:10])

            CVE.objects.create(
                cve_id=cve_id,
                description=description,
                severity=severity,
                cvss_score=cvss_score,
                published_date=published_date,
                last_modified=last_modified,
                affected_products=affected_products,
            )
            created_count += 1

    except requests.RequestException as e:
        logger.error('Failed to fetch CVEs from NVD: %s', e)
        error_message = f'Failed to fetch CVEs: {e}'
    except (KeyError, ValueError) as e:
        logger.error('Error parsing NVD response: %s', e)
        error_message = f'Error parsing NVD response: {e}'

    if error_message:
        messages.error(request, error_message)
    else:
        messages.success(request, f'Successfully fetched {created_count} new CVE(s).')

    return redirect('cve_manager:cve_list')


@login_required
def map_cve_to_control(request, pk):
    """POST view to link a CVE to controls."""
    cve = get_object_or_404(CVE, pk=pk)
    if request.method == 'POST':
        control_ids = request.POST.getlist('control_ids')
        if control_ids:
            controls = Control.objects.filter(
                pk__in=control_ids,
                organization=request.user.organization,
            )
            cve.mapped_controls.add(*controls)
            messages.success(request, 'Controls mapped to CVE successfully.')
        else:
            messages.warning(request, 'No controls selected.')
    return redirect('cve_manager:cve_detail', pk=cve.pk)
