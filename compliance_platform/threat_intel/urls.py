from django.urls import path
from . import views

app_name = 'threat_intel'

urlpatterns = [
    path('', views.threat_dashboard, name='dashboard'),
    path('api/live/', views.api_live_threats, name='api_live_threats'),
    path('api/scan/', views.api_trigger_agent_scan, name='api_trigger_scan'),
    path('api/search/', views.api_dark_web_search, name='api_dark_web_search'),
    path('api/leakosint/', views.api_leakosint_search, name='api_leakosint_search'),
    path('api/domain-scan/', views.api_domain_scan, name='api_domain_scan'),
    path('api/stats/', views.api_threat_stats, name='api_threat_stats'),
    path('api/agents/', views.api_agent_status, name='api_agent_status'),
    path('api/logs/', views.api_agent_logs, name='api_agent_logs'),
    path('api/cves/', views.api_cve_feed, name='api_cve_feed'),
]
