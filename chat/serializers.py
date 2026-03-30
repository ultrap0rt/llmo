from rest_framework import serializers
from .models import UserProfile, ChatSession, Message

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'role', 'content', 'timestamp', 'graph_context']
        read_only_fields = ['id', 'timestamp']

class ChatSessionSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    
    class Meta:
        model = ChatSession
        fields = ['session_id', 'title', 'created_at', 'updated_at', 'messages']
        read_only_fields = ['session_id', 'created_at', 'updated_at']
