from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Organization, User


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'industry', 'country', 'company_size', 'created_at']
    list_filter = ['industry', 'company_size']
    search_fields = ['name', 'country']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'role', 'organization', 'is_staff']
    list_filter = ['role', 'is_staff', 'is_active']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Platform Info', {'fields': ('role', 'organization')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Platform Info', {'fields': ('role', 'organization')}),
    )
