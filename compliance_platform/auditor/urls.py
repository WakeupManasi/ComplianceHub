from django.urls import path
from . import views

app_name = 'auditor'

urlpatterns = [
    path('', views.auditor_dashboard, name='dashboard'),
    path('<int:pk>/', views.review_detail, name='review_detail'),
    path('<int:pk>/approve/', views.approve_review, name='approve_review'),
    path('<int:pk>/reject/', views.reject_review, name='reject_review'),
    path('audits/', views.audit_list, name='audit_list'),
    path('audits/schedule/', views.schedule_audit, name='schedule_audit'),
    path('audits/<int:pk>/', views.audit_detail, name='audit_detail'),
    path('audits/<int:pk>/status/', views.update_audit_status, name='update_audit_status'),
    path('audits/<int:pk>/finding/', views.add_finding, name='add_finding'),
    path('timeline/', views.audit_timeline, name='audit_timeline'),
    path('calendar/', views.audit_calendar, name='audit_calendar'),
]
