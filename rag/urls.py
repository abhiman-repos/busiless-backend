from django.urls import path
from rag import views 

urlpatterns = [
    path('files/', views.list_files, name='list_files'),        # GET /api/training/files/
    path('upload/', views.upload_file, name='upload_file'),     # POST /api/training/upload/
    path('files/<int:file_id>/', views.delete_file, name='delete_file'),  # DELETE /api/training/files/<id>/
    path('query/', views.ask_question, name='ask_question'),    # POST /api/training/query/
    path('train/', views.trigger_training, name='trigger_training'),  # POST /api/training/train/
    path('status/', views.training_status, name='training_status'),    # GET /api/training/status/
]