from django.urls import path
from . import views

app_name = 'ai_assist'

urlpatterns = [
    path('explain/', views.ai_explain, name='ai_explain'),
    path('chat/', views.ai_chat, name='ai_chat'),
    path('chat/message/', views.ai_chat_message, name='ai_chat_message'),
]
