from django.urls import path
from . import views

app_name = 'alerts'

urlpatterns = [
    path('', views.alert_list, name='alert_list'),
    path('<int:pk>/', views.alert_detail, name='alert_detail'),
    path('<int:pk>/dismiss/', views.dismiss_alert, name='dismiss_alert'),
    path('generate/', views.generate_alerts_view, name='generate_alerts'),
]
