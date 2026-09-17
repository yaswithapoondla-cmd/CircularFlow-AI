import os
import re
from typing import List, Dict, Any, Optional
import chromadb
from ..config import get_settings
from ..schemas.rag import RAGChunk


class RAGService:
    _client: Optional[chromadb.PersistentClient] = None
    _collection: Optional[Any] = None
    COLLECTION_NAME = "institutional_knowledge"

    @classmethod
    def get_client(cls) -> chromadb.PersistentClient:
        if cls._client is None:
            persist_dir = get_settings().CHROMA_PERSIST_DIR
            os.makedirs(persist_dir, exist_ok=True)
            cls._client = chromadb.PersistentClient(path=persist_dir)
        return cls._client

    @classmethod
    def get_collection(cls):
        if cls._collection is None:
            client = cls.get_client()
            cls._collection = client.get_or_create_collection(
                name=cls.COLLECTION_NAME,
                metadata={"description": "CircularFlow AI Institutional Policy and Circular Store"}
            )
        return cls._collection

    @staticmethod
    def chunk_text(text: str, chunk_size: int = 600, overlap: int = 80) -> List[str]:
        """Split text into overlapping clean semantic chunks."""
        clean_text = text.strip()
        if not clean_text:
            return []
        
        # Split by double newline first if structured
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n', clean_text) if p.strip()]
        chunks: List[str] = []
        current_chunk = ""

        for p in paragraphs:
            if len(current_chunk) + len(p) <= chunk_size:
                current_chunk = f"{current_chunk}\n\n{p}".strip() if current_chunk else p
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                if len(p) > chunk_size:
                    # Split very large paragraph by word boundaries
                    words = p.split()
                    temp = ""
                    for w in words:
                        if len(temp) + len(w) + 1 <= chunk_size:
                            temp = f"{temp} {w}".strip()
                        else:
                            if temp:
                                chunks.append(temp)
                            temp = w
                    if temp:
                        current_chunk = temp
                    else:
                        current_chunk = ""
                else:
                    current_chunk = p

        if current_chunk:
            chunks.append(current_chunk)

        # Fallback if no chunks produced
        if not chunks:
            chunks = [clean_text[:chunk_size]]

        return chunks

    @classmethod
    def ingest_document(cls, document_name: str, content: str) -> int:
        """Indexes an institutional document text into ChromaDB."""
        chunks = cls.chunk_text(content)
        if not chunks:
            return 0

        coll = cls.get_collection()
        
        # Clean existing chunks for this document name to avoid duplicate indexing
        try:
            existing = coll.get(where={"document": document_name})
            if existing and existing.get("ids"):
                coll.delete(ids=existing["ids"])
        except Exception:
            pass

        ids = [f"{document_name}#chunk_{i}_{hash(c) & 0xfffffff}" for i, c in enumerate(chunks)]
        metadatas = [{"document": document_name, "chunk_id": f"chunk-{i}"} for i in range(len(chunks))]

        coll.add(
            documents=chunks,
            metadatas=metadatas,
            ids=ids
        )
        return len(chunks)

    @classmethod
    def retrieve(cls, query: str, top_k: int = 5) -> List[RAGChunk]:
        """Retrieve most relevant institutional knowledge chunks for a query."""
        coll = cls.get_collection()
        count = coll.count()
        if count == 0:
            return []

        actual_k = min(top_k, count)
        try:
            results = coll.query(
                query_texts=[query],
                n_results=actual_k,
                include=["documents", "metadatas", "distances"]
            )
        except Exception as e:
            print(f"[RAGService] Query error: {e}")
            return []

        rag_chunks: List[RAGChunk] = []
        if not results or not results.get("documents") or not results["documents"][0]:
            return []

        docs = results["documents"][0]
        metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
        distances = results["distances"][0] if results.get("distances") else [1.0] * len(docs)

        for doc_text, meta, dist in zip(docs, metas, distances):
            # Convert cosine/L2 distance to normalized score (0.0 - 1.0)
            score = round(max(0.0, min(1.0, 1.0 - (float(dist) / 2.0))), 3)
            # Only include chunks that meet the relevance threshold
            if score < 0.45:
                continue
            doc_name = meta.get("document", "Institutional Document")
            chunk_id = meta.get("chunk_id", "chunk-0")
            rag_chunks.append(RAGChunk(
                content=doc_text,
                document=doc_name,
                score=score,
                chunk_id=chunk_id
            ))

        return rag_chunks

    @classmethod
    def list_documents(cls) -> List[Dict[str, Any]]:
        """List distinct documents stored in ChromaDB and their chunk counts."""
        coll = cls.get_collection()
        if coll.count() == 0:
            return []

        data = coll.get(include=["metadatas"])
        doc_counts: Dict[str, int] = {}
        for m in (data.get("metadatas") or []):
            name = m.get("document", "Unknown")
            doc_counts[name] = doc_counts.get(name, 0) + 1

        return [
            {"document": doc_name, "total_chunks": count}
            for doc_name, count in doc_counts.items()
        ]
