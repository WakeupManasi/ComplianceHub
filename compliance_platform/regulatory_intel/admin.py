from django.contrib import admin
from .models import (
    RegulatorySource, RegulatoryDocument, ClauseDiff,
    ImpactMapping, ImpactReport, ComplianceCategory, AgentLog,
)


@admin.register(RegulatorySource)
class RegulatorySourceAdmin(admin.ModelAdmin):
    list_display = ['name', 'source_type', 'is_active', 'last_checked']
    list_filter = ['source_type', 'is_active']


@admin.register(RegulatoryDocument)
class RegulatoryDocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'doc_type', 'source', 'impact_level', 'published_date', 'is_processed', 'is_new']
    list_filter = ['doc_type', 'impact_level', 'is_processed', 'is_new', 'source']
    search_fields = ['title', 'reference_number', 'raw_text']
    date_hierarchy = 'created_at'


@admin.register(ClauseDiff)
class ClauseDiffAdmin(admin.ModelAdmin):
    list_display = ['clause_reference', 'change_type', 'impact_score', 'document']
    list_filter = ['change_type']


@admin.register(ImpactMapping)
class ImpactMappingAdmin(admin.ModelAdmin):
    list_display = ['area_name', 'area_type', 'risk_score', 'status', 'responsible_team']
    list_filter = ['area_type', 'status']


@admin.register(ImpactReport)
class ImpactReportAdmin(admin.ModelAdmin):
    list_display = ['title', 'overall_risk_score', 'is_approved', 'created_at']
    list_filter = ['is_approved']


@admin.register(ComplianceCategory)
class ComplianceCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(AgentLog)
class AgentLogAdmin(admin.ModelAdmin):
    list_display = ['agent_type', 'action', 'status', 'created_at']
    list_filter = ['agent_type', 'status']
    readonly_fields = ['created_at']
