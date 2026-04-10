from django.contrib import admin
from .models import ComplianceFramework, Clause, Control, Document, Guideline


@admin.register(ComplianceFramework)
class ComplianceFrameworkAdmin(admin.ModelAdmin):
    list_display = ('name', 'industry', 'created_at')
    list_filter = ('industry',)
    search_fields = ('name',)


@admin.register(Clause)
class ClauseAdmin(admin.ModelAdmin):
    list_display = ('number', 'title', 'framework')
    list_filter = ('framework',)
    search_fields = ('number', 'title')


@admin.register(Control)
class ControlAdmin(admin.ModelAdmin):
    list_display = ('title', 'clause', 'framework', 'is_mandatory', 'organization')
    list_filter = ('framework', 'is_mandatory', 'organization')
    search_fields = ('title',)


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'doc_type', 'organization', 'uploaded_by', 'uploaded_at')
    list_filter = ('doc_type', 'organization')
    search_fields = ('title',)


@admin.register(Guideline)
class GuidelineAdmin(admin.ModelAdmin):
    list_display = ('title', 'industry', 'category')
    list_filter = ('industry', 'category')
    search_fields = ('title',)
