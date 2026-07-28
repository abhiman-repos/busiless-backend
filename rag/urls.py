from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_file, name='upload_file'),
    path('query/', views.ask_question, name='ask_question'),
    # Optional: list files, delete, etc.
]