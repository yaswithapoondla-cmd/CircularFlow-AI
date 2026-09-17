import logging
from typing import List, Dict, Any
from ..config import get_settings
from ..schemas.rag import RAGChunk
from ..schemas.ai import AISource, AIChatResponse
from .client import get_llm_client
from .prompts import CIRA_SYSTEM_PROMPT, build_user_prompt

logger = logging.getLogger("circularflow.llm")


class LLMService:
    @classmethod
    def generate_answer(cls, query: str, chunks: List[RAGChunk]) -> AIChatResponse:
        """
        Generates an authoritative, grounded response to an institutional inquiry
        using retrieved RAG context chunks.
        """
        settings = get_settings()
        client = get_llm_client()

        # Build structured sources list
        sources: List[AISource] = [
            AISource(document=c.document, score=c.score, chunk_id=c.chunk_id)
            for c in chunks
        ]

        # Case 1: No LLM API Key configured -> Graceful institutional fallback
        if client is None:
            logger.info("[LLMService] No LLM_API_KEY configured. Providing deterministic grounded response.")
            if not chunks:
                answer = (
                    "The current institutional knowledge base does not contain verified policy records "
                    "covering this inquiry. Please configure `LLM_API_KEY` in `backend/.env` for generative AI answering."
                )
                return AIChatResponse(answer=answer, sources=[], is_grounded=False)

            top_chunk = chunks[0]
            answer = (
                f"**Verified Record:** Based on verified document `{top_chunk.document}` (Confidence: {int(top_chunk.score * 100)}%):\n\n"
                f"> {top_chunk.content}\n\n"
                f"*Note: Direct generative LLM synthesis is unconfigured (`LLM_API_KEY` not set). Showing verified raw policy citation.*"
            )
            return AIChatResponse(answer=answer, sources=sources, is_grounded=True)

        # Case 2: LLM API Key is configured -> Generative grounded completion
        user_prompt = build_user_prompt(query, chunks)
        try:
            logger.info(f"[LLMService] Calling LLM ({settings.LLM_MODEL}) with {len(chunks)} context chunks.")
            response = client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {"role": "system", "content": CIRA_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                max_tokens=600,
            )
            llm_text = response.choices[0].message.content.strip()
            return AIChatResponse(answer=llm_text, sources=sources, is_grounded=len(chunks) > 0)

        except Exception as exc:
            logger.error(f"[LLMService] Error during LLM completion: {exc}", exc_info=True)
            if chunks:
                fallback_answer = (
                    f"**Verified Policy Reference:**\n\n"
                    f"{chunks[0].content}\n\n"
                    f"*(Source: {chunks[0].document}. LLM service encountered a connection issue: {str(exc)})*"
                )
                return AIChatResponse(answer=fallback_answer, sources=sources, is_grounded=True)
            return AIChatResponse(
                answer=f"AI service temporarily unavailable: {str(exc)}",
                sources=[],
                is_grounded=False
            )
