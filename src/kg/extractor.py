import os
import asyncio
from langchain_openai import ChatOpenAI
from langchain_neo4j import Neo4jGraph
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_core.documents import Document
from src.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, OLLAMA_BASE_URL, OLLAMA_EXTRACTOR_MODEL

graph = None
llm_transformer = None
_skip_notice_printed = False

# Important: allow the app to start even if Neo4j/Ollama are not running yet.
try:
    graph = Neo4jGraph(
        url=NEO4J_URI,
        username=NEO4J_USER,
        password=NEO4J_PASSWORD
    )

    # Use OpenAI client pointing to local Ollama
    llm = ChatOpenAI(
        api_key="ollama",  # placeholder
        base_url=OLLAMA_BASE_URL,
        model=OLLAMA_EXTRACTOR_MODEL,
        temperature=0
    )

    # Initialize the graph transformer
    llm_transformer = LLMGraphTransformer(llm=llm)
except Exception as e:
    print(f"[kg.extractor] Init failed: {e}")

def extract_and_store_knowledge(text: str):
    """
    Extract entities and relationships from the text and store them in Neo4j.
    """
    global _skip_notice_printed
    if not graph or not llm_transformer:
        if not _skip_notice_printed:
            print("[kg.extractor] Skipping extraction: Neo4j/LLM not initialized.")
            _skip_notice_printed = True
        return False

    try:
        documents = [Document(page_content=text)]
        graph_documents = llm_transformer.convert_to_graph_documents(documents)
        
        # Store to Neo4j
        if graph_documents:
            graph.add_graph_documents(
                graph_documents, 
                baseEntityLabel=True, 
                include_source=True
            )
            print(f"Stored {len(graph_documents[0].nodes)} nodes and {len(graph_documents[0].relationships)} relationships.")
        return True
    except Exception as e:
        print(f"Error extracting knowledge: {e}")
        return False

async def async_extract_and_store(text: str):
    """
    Async wrapper for background execution
    """
    return await asyncio.to_thread(extract_and_store_knowledge, text)
