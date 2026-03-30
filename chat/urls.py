from django.urls import path
from .views import SessionCreateView, SessionDetailView, ChatMessageView

urlpatterns = [
    path('sessions/', SessionCreateView.as_view(), name='session-create'),
    path('sessions/<uuid:session_id>/', SessionDetailView.as_view(), name='session-detail'),
    path('sessions/<uuid:session_id>/message/', ChatMessageView.as_view(), name='chat-message'),
]
