from django.contrib import admin

from .models import Vendor, VendorMonitoring


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'risk_score', 'risk_level', 'organization', 'created_at')
    list_filter = ('status', 'organization')
    search_fields = ('name', 'services')


@admin.register(VendorMonitoring)
class VendorMonitoringAdmin(admin.ModelAdmin):
    list_display = ('vendor', 'event_type', 'severity', 'created_at')
    list_filter = ('event_type', 'severity')
    search_fields = ('vendor__name', 'description')
