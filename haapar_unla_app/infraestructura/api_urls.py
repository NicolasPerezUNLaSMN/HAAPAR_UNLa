from django.urls import path
from haapar_unla_app import views

urlpatterns = [
    path('chatgpt/', views.chatgpt_api, name='chatgpt_api'),
]
