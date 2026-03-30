import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
from qdrant_client.http.models import Filter, FieldCondition, MatchValue

from src.config import QDRANT_URL, EMBEDDING_MODEL_NAME

class VectorStore:
    def __init__(self, collection_name: str = "episodic_memory"):
        self.collection_name = collection_name
        self.client = None
        self.embedder = None
        self.vector_size = None
        self.is_available = False

        # Important: allow the app to start even if Qdrant is not running yet.
        # Connection/model initialization can fail on fresh setups.
        try:
            self.client = QdrantClient(url=QDRANT_URL)
            self.embedder = SentenceTransformer(EMBEDDING_MODEL_NAME)
            self.vector_size = self.embedder.get_sentence_embedding_dimension()
            self._init_collection()
            self.is_available = True
        except Exception as e:
            print(f"[vector_store] Qdrant/embeddings init failed: {e}")

    def _disable(self, reason: Exception):
        """
        Disable vector operations after connection failures to avoid noisy logs
        on every request while Qdrant is down.
        """
        if self.is_available:
            print(f"[vector_store] Disabling vector store after failure: {reason}")
        self.is_available = False

    def _init_collection(self):
        if not self.client or self.vector_size is None:
            return
        # Проверяем существует ли коллекция
        collections = self.client.get_collections()
        collection_names = [col.name for col in collections.collections]
        
        if self.collection_name not in collection_names:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
            )

    def add_memory(self, session_id: str, role: str, text: str):
        """
        Сохраняем сообщение в векторную базу
        role: "user" или "assistant"
        """
        if not self.client or not self.embedder or not self.is_available:
            return False

        try:
            vector = self.embedder.encode(text).tolist()
            point_id = str(uuid.uuid4())

            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    PointStruct(
                        id=point_id,
                        vector=vector,
                        payload={
                            "session_id": session_id,
                            "role": role,
                            "text": text
                        }
                    )
                ]
            )
            return True
        except Exception as e:
            self._disable(e)
            return False

    def search_memory(self, session_id: str, query: str, top_k: int = 5) -> list[dict]:
        """
        Ищем релевантные сообщения из прошлого для данного сеанса
        """
        if not self.client or not self.embedder or not self.is_available:
            return []

        vector = self.embedder.encode(query).tolist()

        try:
            result = self.client.query_points(
                collection_name=self.collection_name,
                query=vector,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="session_id",
                            match=MatchValue(value=session_id),
                        )
                    ]
                ),
                limit=top_k,
                with_payload=True,
                with_vectors=False,
            )
            # `points` is the list of scored points in qdrant-client
            return [p.payload for p in (result.points or [])]
        except Exception as e:
            self._disable(e)
            return []

# Глобальный экземпляр для переиспользования
vector_store = VectorStore()
