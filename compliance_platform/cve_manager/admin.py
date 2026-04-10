from django.contrib import admin

from .models import CVE


@admin.register(CVE)
class CVEAdmin(admin.ModelAdmin):
    list_display = ('cve_id', 'severity', 'cvss_score', 'published_date', 'created_at')
    list_filter = ('severity',)
    search_fields = ('cve_id', 'description')
    filter_horizontal = ('mapped_controls',)
