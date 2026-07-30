# rag/models.py
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()

class TrainingFile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='training_files')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='training/')
    size = models.IntegerField()
    type = models.CharField(max_length=50)  # e.g., 'pdf', 'csv', 'txt'
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # enforce per-user unique filenames if desired
        unique_together = ('user', 'name')
        
class ChatSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    intent = models.CharField(max_length=50)

    state = models.CharField(max_length=50)

    data = models.JSONField(default=dict)

    updated_at = models.DateTimeField(auto_now=True)