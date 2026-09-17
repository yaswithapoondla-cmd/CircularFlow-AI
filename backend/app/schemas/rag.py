from typing import List, Optional
from pydantic import BaseModel, Field


class RAGChunk(BaseModel):
    content: str = Field(..., description="Text content of the retrieved chunk")
    document: str = Field(..., description="Source document filename")
    score: float = Field(..., description="Relevance / similarity score (0.0 to 1.0)")
    chunk_id: str = Field(..., description="Unique chunk identifier")


class RAGSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Semantic search query")
    top_k: int = Field(5, ge=1, le=20, description="Number of top relevant chunks to retrieve")


class RAGSearchResponse(BaseModel):
    query: str
    results: List[RAGChunk]
    total: int


class RAGUploadResponse(BaseModel):
    status: str
    document: str
    chunks_indexed: int
    message: str


class RAGDocument(BaseModel):
    document: str
    total_chunks: int


class RAGDocumentListResponse(BaseModel):
    documents: List[RAGDocument]
    total_documents: int
