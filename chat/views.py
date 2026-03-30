import threading
from rest_framework import views, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import ChatSession, Message
from .serializers import ChatSessionSerializer, MessageSerializer

from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

from src.config import OLLAMA_BASE_URL, OLLAMA_MODEL
from src.memory.vector_store import vector_store
from src.rag.graph_retriever import retrieve_graph_context
from src.kg.extractor import extract_and_store_knowledge

main_llm = ChatOpenAI(
    api_key="ollama", 
    base_url=OLLAMA_BASE_URL,
    model=OLLAMA_MODEL,
    temperature=0.7
)

prompt_template = PromptTemplate(
    input_variables=["history", "graph_context", "message"],
    template="""You are a highly intelligent AI assistant with a perfect long-term memory.
You have access to the user's past episodic memory and an extracted knowledge graph.

### Past Dialogue Context (Episodic Memory):
{history}

### Knowledge Graph Context (Structured Facts):
{graph_context}

### Current User Message:
{message}

Using all the provided context, generate a helpful, accurate, and natural response.
If the contexts are empty, just respond normally.
Answer:
"""
)

chain = prompt_template | main_llm

def background_extraction_task(session_id_str, user_msg, assistant_msg):
    """
    Выполняется в фоне: обновляет векторную память и граф знаний.
    """
    try:
        # Update vector store
        vector_store.add_memory(session_id=session_id_str, role="user", text=user_msg)
        vector_store.add_memory(session_id=session_id_str, role="assistant", text=assistant_msg)
        
        # Extract to Graph DB
        full_interaction = f"User: {user_msg}\nAssistant: {assistant_msg}"
        extract_and_store_knowledge(full_interaction)
    except Exception as e:
        print(f"Error in background extraction task: {e}")

class SessionCreateView(views.APIView):
    def post(self, request):
        session = ChatSession.objects.create(title=request.data.get('title', 'New Chat'))
        serializer = ChatSessionSerializer(session)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class SessionDetailView(views.APIView):
    def get(self, request, session_id):
        session = get_object_or_404(ChatSession, session_id=session_id)
        serializer = ChatSessionSerializer(session)
        return Response(serializer.data)

class ChatMessageView(views.APIView):
    def post(self, request, session_id):
        session = get_object_or_404(ChatSession, session_id=session_id)
        user_message_text = request.data.get('message')
        if not user_message_text:
            return Response({"error": "Message is required"}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Retrieve episodic memory
        session_id_str = str(session.session_id)
        past_messages = vector_store.search_memory(session_id=session_id_str, query=user_message_text, top_k=5)
        
        history_text = ""
        if past_messages:
            for msg in reversed(past_messages):
                history_text += f"{msg['role'].capitalize()}: {msg['text']}\n"
                
        if not history_text:
            history_text = "No prior history found."
            
        # 2. Retrieve graph context
        graph_context_text = retrieve_graph_context(query=user_message_text)
        if not graph_context_text:
            graph_context_text = "No relevant knowledge graph entities found."
            
        # 3. Сохраняем сообщение пользователя в SQL с точностью до миллисекунды
        Message.objects.create(
            session=session,
            role='user',
            content=user_message_text,
            graph_context=graph_context_text
        )

        # 4. Генерируем ответ
        try:
            response_llm = chain.invoke({
                "history": history_text,
                "graph_context": graph_context_text,
                "message": user_message_text
            })
            answer_text = response_llm.content
        except Exception as e:
            # If Ollama/LLM is not available, keep the API responsive.
            print(f"[chat] LLM invocation failed: {e}")
            answer_text = "LLM unavailable right now (Ollama/LLM service not reachable). Please try again later."

        # 5. Сохраняем ответ ассистента в SQL
        assistant_msg_obj = Message.objects.create(
            session=session,
            role='assistant',
            content=answer_text,
            graph_context=graph_context_text
        )

        # 6. Запускаем фоновую задачу для векторной и графовой БД
        threading.Thread(
            target=background_extraction_task, 
            args=(session_id_str, user_message_text, answer_text)
        ).start()

        return Response({
            "response": answer_text,
            "message_id": assistant_msg_obj.id,
            "timestamp": assistant_msg_obj.timestamp
        }, status=status.HTTP_200_OK)
