from django.urls import path

from . import views

app_name = 'vendors'

urlpatterns = [
    path('', views.vendor_list, name='vendor_list'),
    path('add/', views.vendor_add, name='vendor_add'),
    path('<int:pk>/', views.vendor_detail, name='vendor_detail'),
    path('<int:pk>/edit/', views.vendor_edit, name='vendor_edit'),
]
