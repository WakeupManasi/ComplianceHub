from django.contrib import admin
from .models import AuditReview, Audit, AuditFinding, AuditTimelineEvent


@admin.register(AuditReview)
class AuditReviewAdmin(admin.ModelAdmin):
    list_display = ('control', 'status', 'reviewer', 'organization', 'reviewed_at', 'created_at')
    list_filter = ('status', 'created_at', 'reviewed_at')
    search_fields = ('control__title', 'comments')
    raw_id_fields = ('control', 'document', 'risk', 'organization', 'reviewer')


@admin.register(Audit)
class AuditAdmin(admin.ModelAdmin):
    list_display = ('title', 'audit_type', 'status', 'organization', 'lead_auditor', 'scheduled_start', 'scheduled_end', 'score')
    list_filter = ('status', 'audit_type', 'organization')
    search_fields = ('title', 'scope', 'objectives')
    raw_id_fields = ('organization', 'framework', 'lead_auditor')
    filter_horizontal = ('auditors',)
    date_hierarchy = 'scheduled_start'


@admin.register(AuditFinding)
class AuditFindingAdmin(admin.ModelAdmin):
    list_display = ('title', 'audit', 'severity', 'status', 'assigned_to', 'due_date', 'created_at')
    list_filter = ('severity', 'status')
    search_fields = ('title', 'description')
    raw_id_fields = ('audit', 'control', 'assigned_to')


@admin.register(AuditTimelineEvent)
class AuditTimelineEventAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'audit', 'user', 'created_at')
    list_filter = ('event_type', 'created_at')
    search_fields = ('description',)
    raw_id_fields = ('audit', 'user')
