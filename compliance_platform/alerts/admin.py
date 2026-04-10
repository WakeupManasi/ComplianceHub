from django.contrib import admin
from .models import Alert


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('title', 'alert_type', 'severity', 'organization', 'is_read', 'created_at')
    list_filter = ('alert_type', 'severity', 'is_read', 'created_at')
    search_fields = ('title', 'description')
    raw_id_fields = ('organization', 'linked_cve', 'linked_vendor', 'linked_control')
