from typing import List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, status
from ...schemas.rag import (
    RAGSearchRequest,
    RAGSearchResponse,
    RAGUploadResponse,
    RAGDocumentListResponse,
    RAGDocument,
)
from ...services.rag_service import RAGService

router = APIRouter(prefix="/rag", tags=["Vector Retrieval & Knowledge Index"])


@router.post(
    "/upload",
    response_model=RAGUploadResponse,
    summary="Index Institutional Document into ChromaDB",
    description="Upload text or file content (.txt, .md, .pdf) to chunk and store in ChromaDB vector repository."
)
async def upload_document(
    file: Optional[UploadFile] = File(None, description="Uploaded document file"),
    document_name: Optional[str] = Form(None, description="Explicit name for document (optional if file provided)"),
    raw_text: Optional[str] = Form(None, description="Direct text content to index"),
) -> RAGUploadResponse:
    target_name = ""
    content = ""

    if file:
        target_name = document_name or file.filename or "Uploaded Document"
        try:
            byte_content = await file.read()
            content = byte_content.decode("utf-8", errors="ignore")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to read uploaded file: {str(e)}"
            )
    elif raw_text:
        target_name = document_name or "Institutional Policy Directive.txt"
        content = raw_text
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either a file or raw_text must be provided for indexing."
        )

    if not content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document content cannot be empty."
        )

    try:
        indexed_chunks = RAGService.ingest_document(document_name=target_name, content=content)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to index into ChromaDB: {str(exc)}"
        )

    return RAGUploadResponse(
        status="success",
        document=target_name,
        chunks_indexed=indexed_chunks,
        message=f"Successfully indexed {indexed_chunks} semantic chunks into ChromaDB."
    )


@router.post(
    "/search",
    response_model=RAGSearchResponse,
    summary="Semantic Retrieval Search",
    description="Query ChromaDB vector store for the most relevant context chunks."
)
async def search_knowledge(request: RAGSearchRequest) -> RAGSearchResponse:
    try:
        chunks = RAGService.retrieve(query=request.query, top_k=request.top_k)
        return RAGSearchResponse(
            query=request.query,
            results=chunks,
            total=len(chunks)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ChromaDB retrieval error: {str(exc)}"
        )


@router.get(
    "/documents",
    response_model=RAGDocumentListResponse,
    summary="List Indexed Documents",
    description="Retrieve all distinct documents currently indexed in ChromaDB."
)
async def list_indexed_documents() -> RAGDocumentListResponse:
    try:
        raw_docs = RAGService.list_documents()
        docs = [RAGDocument(document=d["document"], total_chunks=d["total_chunks"]) for d in raw_docs]
        return RAGDocumentListResponse(
            documents=docs,
            total_documents=len(docs)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(exc)}"
        )
