import json
import logging
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .agents import (
    ClassifierAgent, DiffAgent, DrafterAgent, MapperAgent,
    MonitorAgent, ReporterAgent, ScraperAgent,
)
from .models import (
    AgentLog, ClauseDiff, ComplianceCategory, ImpactMapping,
    ImpactReport, RegulatoryDocument, RegulatorySource,
)

logger = logging.getLogger(__name__)


def _log_agent(agent_type, action, status='started', document=None, details=''):
    """Create an agent log entry."""
    return AgentLog.objects.create(
        agent_type=agent_type,
        action=action,
        status=status,
        document=document,
        details=details,
    )


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@login_required
def intel_dashboard(request):
    """Main regulatory intelligence dashboard."""
    recent_docs = RegulatoryDocument.objects.all()[:10]
    new_docs = RegulatoryDocument.objects.filter(is_new=True).count()
    total_docs = RegulatoryDocument.objects.count()
    pending_reports = ImpactReport.objects.filter(is_approved=False).count()
    recent_reports = ImpactReport.objects.all()[:5]
    recent_logs = AgentLog.objects.all()[:15]
    sources = RegulatorySource.objects.filter(is_active=True)

    # Category counts for heatmap
    categories = {}
    for doc in RegulatoryDocument.objects.exclude(categories=''):
        for cat in doc.categories.split(','):
            cat = cat.strip()
            if cat:
                categories[cat] = categories.get(cat, 0) + 1

    # Impact distribution
    impact_counts = {
        'critical': RegulatoryDocument.objects.filter(impact_level='critical').count(),
        'high': RegulatoryDocument.objects.filter(impact_level='high').count(),
        'medium': RegulatoryDocument.objects.filter(impact_level='medium').count(),
        'low': RegulatoryDocument.objects.filter(impact_level='low').count(),
    }

    context = {
        'recent_docs': recent_docs,
        'new_docs_count': new_docs,
        'total_docs': total_docs,
        'pending_reports': pending_reports,
        'recent_reports': recent_reports,
        'recent_logs': recent_logs,
        'sources': sources,
        'categories': categories,
        'impact_counts': impact_counts,
    }
    return render(request, 'regulatory_intel/dashboard.html', context)


# ---------------------------------------------------------------------------
# Document Views
# ---------------------------------------------------------------------------
@login_required
def document_list(request):
    """List all regulatory documents with filters."""
    docs = RegulatoryDocument.objects.all()

    # Filters
    impact = request.GET.get('impact')
    doc_type = request.GET.get('type')
    source = request.GET.get('source')
    search = request.GET.get('q', '')

    if impact:
        docs = docs.filter(impact_level=impact)
    if doc_type:
        docs = docs.filter(doc_type=doc_type)
    if source:
        docs = docs.filter(source_id=source)
    if search:
        docs = docs.filter(title__icontains=search)

    sources = RegulatorySource.objects.filter(is_active=True)
    context = {
        'documents': docs,
        'sources': sources,
        'current_impact': impact,
        'current_type': doc_type,
        'current_source': source,
        'search_query': search,
    }
    return render(request, 'regulatory_intel/document_list.html', context)


@login_required
def document_detail(request, pk):
    """View a regulatory document with its analysis."""
    doc = get_object_or_404(RegulatoryDocument, pk=pk)
    diffs = doc.diffs.all()
    reports = doc.reports.all()
    mappings = ImpactMapping.objects.filter(diff__document=doc)

    # Generate diff HTML if there's a previous version
    diff_html = ''
    if doc.previous_version and doc.raw_text and doc.previous_version.raw_text:
        diff_html = DiffAgent.generate_diff_html(
            doc.previous_version.raw_text, doc.raw_text
        )

    context = {
        'document': doc,
        'diffs': diffs,
        'reports': reports,
        'mappings': mappings,
        'diff_html': diff_html,
    }
    return render(request, 'regulatory_intel/document_detail.html', context)


# ---------------------------------------------------------------------------
# Analysis Pipeline
# ---------------------------------------------------------------------------
@login_required
@require_POST
def run_scan(request):
    """Trigger a scan of all active regulatory sources."""
    log = _log_agent('monitor', 'Manual scan triggered')
    monitor = MonitorAgent()
    results = []

    try:
        # Scan RBI
        rbi_items = monitor.check_rbi_notifications()
        results.extend(rbi_items)

        # Scan SEBI
        sebi_items = monitor.check_sebi_circulars()
        results.extend(sebi_items)

        new_count = 0
        for item in results:
            # Check if document already exists
            exists = RegulatoryDocument.objects.filter(
                title=item.get('title', ''),
                source_url=item.get('url', ''),
            ).exists()

            if not exists and item.get('title'):
                source, _ = RegulatorySource.objects.get_or_create(
                    source_type=item.get('source', 'rbi'),
                    defaults={
                        'name': item.get('source', 'RBI').upper(),
                        'base_url': f"https://www.{item.get('source', 'rbi')}.org.in",
                        'scrape_url': f"https://www.{item.get('source', 'rbi')}.org.in",
                    }
                )
                RegulatoryDocument.objects.create(
                    title=item.get('title', ''),
                    doc_type='notification',
                    source=source,
                    reference_number=item.get('reference', ''),
                    source_url=item.get('url', ''),
                    is_new=True,
                )
                new_count += 1

        log.status = 'completed'
        log.details = f"Found {len(results)} items, {new_count} new documents added."
        log.save()
        messages.success(request, f'Scan complete! Found {new_count} new regulatory documents.')

    except Exception as e:
        log.status = 'failed'
        log.error_message = str(e)
        log.save()
        messages.error(request, f'Scan failed: {e}')

    return redirect('regulatory_intel:dashboard')


@login_required
@require_POST
def analyze_document(request, pk):
    """Run full analysis pipeline on a document."""
    doc = get_object_or_404(RegulatoryDocument, pk=pk)

    # Step 1: Extract text if needed
    if not doc.raw_text and doc.source_url:
        log = _log_agent('scraper', f'Extracting text from {doc.title}', document=doc)
        scraper = ScraperAgent()
        doc.raw_text = scraper.download_and_extract(doc.source_url)
        doc.save()
        log.status = 'completed'
        log.save()

    if not doc.raw_text:
        messages.warning(request, 'No text content available for analysis.')
        return redirect('regulatory_intel:document_detail', pk=pk)

    # Step 2: Classify
    log = _log_agent('classifier', f'Classifying {doc.title}', document=doc)
    categories = ClassifierAgent.classify_document(doc.raw_text, doc.title)
    entities = ClassifierAgent.classify_entities(doc.raw_text, doc.title)
    impact = ClassifierAgent.assess_impact(doc.raw_text, doc.title)

    doc.categories = ', '.join(categories)
    doc.affected_entities = ', '.join(entities)
    doc.impact_level = impact
    doc.save()
    log.status = 'completed'
    log.details = f"Categories: {doc.categories}, Entities: {doc.affected_entities}, Impact: {impact}"
    log.save()

    # Step 3: Diff (if previous version exists)
    diffs_data = []
    if doc.previous_version and doc.previous_version.raw_text:
        log = _log_agent('diff', f'Computing diff for {doc.title}', document=doc)
        diffs_data = DiffAgent.extract_clause_changes(
            doc.previous_version.raw_text, doc.raw_text
        )
        for diff in diffs_data:
            ClauseDiff.objects.create(
                document=doc,
                previous_document=doc.previous_version,
                clause_reference=diff.get('clause', ''),
                change_type=diff.get('type', 'modified'),
                old_text=diff.get('old_text', ''),
                new_text=diff.get('new_text', ''),
                change_summary=diff.get('summary', ''),
                impact_score=5 if diff.get('type') in ['added', 'removed'] else 3,
            )
        log.status = 'completed'
        log.details = f"Found {len(diffs_data)} clause-level changes"
        log.save()

    # Step 4: Map to business areas
    log = _log_agent('mapper', f'Mapping {doc.title}', document=doc)
    mappings_data = MapperAgent.map_to_business(categories, doc.raw_text)

    # Create mappings for the first diff or a placeholder
    clause_diffs = doc.diffs.all()
    if clause_diffs.exists():
        for diff_obj in clause_diffs:
            for mapping in mappings_data:
                ImpactMapping.objects.get_or_create(
                    diff=diff_obj,
                    area_type=mapping['area_type'],
                    area_name=mapping['area_name'],
                    defaults={
                        'description': f"Affected due to changes in {diff_obj.clause_reference}",
                        'risk_score': diff_obj.impact_score,
                    }
                )
    else:
        # Create a placeholder diff for document-level mappings
        placeholder_diff = ClauseDiff.objects.create(
            document=doc,
            clause_reference='Full Document',
            change_type='added',
            new_text=doc.raw_text[:1000],
            change_summary=f'New regulatory document: {doc.title}',
            impact_score=5,
        )
        for mapping in mappings_data:
            ImpactMapping.objects.create(
                diff=placeholder_diff,
                area_type=mapping['area_type'],
                area_name=mapping['area_name'],
                description=f"Review required for {mapping['area_name']}",
                risk_score=5,
            )

    log.status = 'completed'
    log.details = f"Generated {len(mappings_data)} business mappings"
    log.save()

    # Step 5: Generate report
    log = _log_agent('reporter', f'Generating report for {doc.title}', document=doc)
    report_data = ReporterAgent.generate_report(
        {
            'title': doc.title,
            'source': doc.source.name if doc.source else 'Unknown',
            'published_date': str(doc.published_date or ''),
            'effective_date': str(doc.effective_date or ''),
            'compliance_deadline': str(doc.compliance_deadline or ''),
        },
        diffs_data,
        mappings_data,
    )

    ImpactReport.objects.create(
        document=doc,
        title=report_data['title'],
        executive_summary=report_data['executive_summary'],
        detailed_analysis=report_data['detailed_analysis'],
        policy_amendments=report_data.get('policy_amendments', ''),
        sop_changes=report_data.get('action_items', ''),
        filing_checklist=report_data.get('compliance_timeline', ''),
        overall_risk_score=report_data.get('overall_risk_score', 5),
    )

    doc.is_processed = True
    doc.is_new = False
    doc.save()
    log.status = 'completed'
    log.save()

    messages.success(request, f'Analysis complete for "{doc.title}"! Impact report generated.')
    return redirect('regulatory_intel:document_detail', pk=pk)


# ---------------------------------------------------------------------------
# Impact Reports
# ---------------------------------------------------------------------------
@login_required
def report_list(request):
    """List all impact reports."""
    reports = ImpactReport.objects.select_related('document').all()
    context = {'reports': reports}
    return render(request, 'regulatory_intel/report_list.html', context)


@login_required
def report_detail(request, pk):
    """View a single impact report."""
    report = get_object_or_404(ImpactReport, pk=pk)
    mappings = ImpactMapping.objects.filter(diff__document=report.document)
    context = {
        'report': report,
        'mappings': mappings,
        'document': report.document,
    }
    return render(request, 'regulatory_intel/report_detail.html', context)


@login_required
@require_POST
def approve_report(request, pk):
    """Approve an impact report."""
    report = get_object_or_404(ImpactReport, pk=pk)
    report.is_approved = True
    report.reviewed_by = request.user
    report.save()
    messages.success(request, 'Report approved successfully.')
    return redirect('regulatory_intel:report_detail', pk=pk)


# ---------------------------------------------------------------------------
# Agent Logs
# ---------------------------------------------------------------------------
@login_required
def agent_logs(request):
    """View agent activity logs."""
    logs = AgentLog.objects.all()[:50]
    context = {'logs': logs}
    return render(request, 'regulatory_intel/agent_logs.html', context)


# ---------------------------------------------------------------------------
# Risk Heatmap (API)
# ---------------------------------------------------------------------------
@login_required
def risk_heatmap_data(request):
    """Return heatmap data as JSON for the dashboard."""
    categories = {}
    for doc in RegulatoryDocument.objects.exclude(categories=''):
        impact = doc.impact_level
        for cat in doc.categories.split(','):
            cat = cat.strip()
            if cat:
                if cat not in categories:
                    categories[cat] = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
                categories[cat][impact] = categories[cat].get(impact, 0) + 1

    return JsonResponse({'categories': categories})


# ---------------------------------------------------------------------------
# Manual Document Upload
# ---------------------------------------------------------------------------
@login_required
def upload_document(request):
    """Upload a regulatory document manually."""
    if request.method == 'POST':
        title = request.POST.get('title', '')
        doc_type = request.POST.get('doc_type', 'circular')
        source_type = request.POST.get('source_type', 'rbi')
        raw_text = request.POST.get('raw_text', '')
        source_url = request.POST.get('source_url', '')

        source, _ = RegulatorySource.objects.get_or_create(
            source_type=source_type,
            defaults={
                'name': source_type.upper(),
                'base_url': f'https://www.{source_type}.org.in',
                'scrape_url': f'https://www.{source_type}.org.in',
            }
        )

        doc = RegulatoryDocument.objects.create(
            title=title,
            doc_type=doc_type,
            source=source,
            raw_text=raw_text,
            source_url=source_url,
            is_new=True,
        )

        # Handle file upload
        if request.FILES.get('pdf_file'):
            doc.pdf_file = request.FILES['pdf_file']
            # Extract text from uploaded PDF
            scraper = ScraperAgent()
            pdf_bytes = request.FILES['pdf_file'].read()
            doc.raw_text = scraper._extract_from_pdf(pdf_bytes)
            doc.save()

        messages.success(request, f'Document "{title}" uploaded successfully.')
        return redirect('regulatory_intel:document_detail', pk=doc.pk)

    sources = RegulatorySource.SOURCE_TYPES
    doc_types = RegulatoryDocument.DOC_TYPES
    context = {'source_types': sources, 'doc_types': doc_types}
    return render(request, 'regulatory_intel/upload_document.html', context)
