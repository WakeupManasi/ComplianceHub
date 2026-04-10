from django.urls import path
from . import views

app_name = 'regulatory_intel'

urlpatterns = [
    path('', views.intel_dashboard, name='dashboard'),
    path('documents/', views.document_list, name='document_list'),
    path('documents/<int:pk>/', views.document_detail, name='document_detail'),
    path('documents/upload/', views.upload_document, name='upload_document'),
    path('documents/<int:pk>/analyze/', views.analyze_document, name='analyze_document'),
    path('scan/', views.run_scan, name='run_scan'),
    path('reports/', views.report_list, name='report_list'),
    path('reports/<int:pk>/', views.report_detail, name='report_detail'),
    path('reports/<int:pk>/approve/', views.approve_report, name='approve_report'),
    path('logs/', views.agent_logs, name='agent_logs'),
    path('api/heatmap/', views.risk_heatmap_data, name='risk_heatmap_data'),
]
