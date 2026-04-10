"""
URL configuration for compliance_platform project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('compliance/', include('compliance.urls')),
    path('vendors/', include('vendors.urls')),
    path('cve/', include('cve_manager.urls')),
    path('risks/', include('risks.urls')),
    path('alerts/', include('alerts.urls')),
    path('auditor/', include('auditor.urls')),
    path('ai/', include('ai_assist.urls')),
    path('faq/', include('faq.urls')),
    path('threat/', include('threat_intel.urls')),
    path('intel/', include('regulatory_intel.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
