import uuid
from django.db import models

class UserProfile(models.Model):
    """
    Анонимный профиль пользователя (можно расширить для авторизации).
    """
    id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.id)


class ChatSession(models.Model):
    """
    Сессия чата со скрытой ссылкой (session_id).
    По этой ссылке можно получить доступ ко всей истории.
    """
    session_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, primary_key=True)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, null=True, blank=True, related_name='sessions')
    title = models.CharField(max_length=255, default="New Chat")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.session_id})"


class Message(models.Model):
    """
    Сообщение с точным временем и сохранением контекста.
    """
    ROLE_CHOICES = (
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System')
    )
    id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, primary_key=True)
    session = models.ForeignKey(ChatSession, related_name='messages', on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Дополнительные данные, которые мы извлекли из графа или векторной БД в этот момент
    graph_context = models.TextField(null=True, blank=True)
    
    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"[{self.timestamp}] {self.role}: {self.content[:50]}..."
