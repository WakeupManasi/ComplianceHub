from django.urls import path
from . import views

app_name = 'compliance'

urlpatterns = [
    path('controls/', views.control_list, name='control_list'),
    path('controls/<int:pk>/', views.control_detail, name='control_detail'),
    path('documents/', views.document_list, name='document_list'),
    path('documents/upload/', views.document_upload, name='document_upload'),
    path('documents/<int:pk>/', views.document_detail, name='document_detail'),
    path('documents/<int:pk>/verify/', views.verify_document, name='verify_document'),
    path('guidelines/', views.guideline_list, name='guideline_list'),
]
