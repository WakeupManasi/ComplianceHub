from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('onboarding/', views.onboarding_view, name='onboarding'),
    path('onboarding/step1/', views.onboarding_step1, name='onboarding_step1'),
    path('onboarding/step2/', views.onboarding_step2, name='onboarding_step2'),
    path('onboarding/step3/', views.onboarding_step3, name='onboarding_step3'),
    path('onboarding/step4/', views.onboarding_step4, name='onboarding_step4'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('organization/users/', views.org_users, name='org_users'),
    path('organization/users/invite/', views.invite_user, name='invite_user'),
    path('organization/users/<int:pk>/edit/', views.edit_user, name='edit_user'),
    path('organization/users/<int:pk>/remove/', views.remove_user, name='remove_user'),
    path('organization/settings/', views.org_settings, name='org_settings'),
]
