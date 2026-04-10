from django.contrib import admin

from .models import Risk


@admin.register(Risk)
class RiskAdmin(admin.ModelAdmin):
    list_display = ('title', 'severity', 'mitigation_status', 'assigned_to', 'organization', 'created_at')
    list_filter = ('severity', 'mitigation_status', 'organization')
    search_fields = ('title', 'description')
