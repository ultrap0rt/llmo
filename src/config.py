import os
from dotenv import load_dotenv

load_dotenv()

# Neo4j Settings
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

# Qdrant Settings
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")

# Ollama / LLM Settings
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "deepseek-r1:1.5b")
OLLAMA_EXTRACTOR_MODEL = os.getenv("OLLAMA_EXTRACTOR_MODEL", "qwen2.5:0.5b")

# Embedding Model
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
