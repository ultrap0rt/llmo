import asyncio
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

from src.config import OLLAMA_BASE_URL, OLLAMA_MODEL
from src.memory.vector_store import vector_store
from src.rag.graph_retriever import retrieve_graph_context
from src.kg.extractor import async_extract_and_store

app = FastAPI(title="AI Knowledge Graph Memory System")

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    response: str

# Main LLM for response generation
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

def update_memory_sync(session_id: str, message: str, response: str):
    """
    Sync wrapper to update memory (since vector_store is currently sync).
    """
    vector_store.add_memory(session_id=session_id, role="user", text=message)
    vector_store.add_memory(session_id=session_id, role="assistant", text=response)

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    # 1. Retrieve episodic memory (vector search)
    # Get last 5 relevant messages
    past_messages = vector_store.search_memory(session_id=request.session_id, query=request.message, top_k=5)
    
    history_text = ""
    if past_messages:
        # Sort or format them
        for msg in reversed(past_messages):  # assuming they are ranked by relevance, just show them
            history_text += f"{msg['role'].capitalize()}: {msg['text']}\n"
            
    if not history_text:
        history_text = "No prior history found."
        
    # 2. Retrieve graph context
    graph_context = retrieve_graph_context(query=request.message)
    if not graph_context:
        graph_context = "No relevant knowledge graph entities found."
        
    # 3. Generate response
    response = chain.invoke({
        "history": history_text,
        "graph_context": graph_context,
        "message": request.message
    })
    
    answer_text = response.content
    
    # 4. Schedule background tasks
    # a. Update vector memory
    background_tasks.add_task(update_memory_sync, request.session_id, request.message, answer_text)
    
    # b. Extract and update knowledge graph with new facts from the user message
    # (Optional: also extract from assistant response if desired)
    full_interaction = f"User: {request.message}\nAssistant: {answer_text}"
    background_tasks.add_task(async_extract_and_store, full_interaction)
    
    return ChatResponse(response=answer_text)

@app.get("/health")
def health_check():
    return {"status": "ok"}
