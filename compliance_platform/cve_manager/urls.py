from django.urls import path

from . import views

app_name = 'cve_manager'

urlpatterns = [
    path('', views.cve_list, name='cve_list'),
    path('fetch/', views.fetch_cves, name='fetch_cves'),
    path('<int:pk>/', views.cve_detail, name='cve_detail'),
    path('<int:pk>/map/', views.map_cve_to_control, name='map_cve_to_control'),
]
