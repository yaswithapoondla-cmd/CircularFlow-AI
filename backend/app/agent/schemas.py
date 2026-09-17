from typing import List, Optional
from pydantic import BaseModel, Field


class AgentChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Natural language institutional query")
    user_role: Optional[str] = Field(None, description="Optional authenticated user role (Registrar, Faculty, Student)")
    user_id: Optional[str] = Field(None, description="Optional authenticated user ID")


class AgentSource(BaseModel):
    source_type: str = Field(..., description="Type of source: 'circular', 'policy_doc', 'action_record', 'recipient_record'")
    title: str = Field(..., description="Document or record title")
    reference: str = Field(..., description="Reference ID or filename")
    score: Optional[float] = Field(None, description="Similarity or relevance score (if applicable)")


class AgentChatResponse(BaseModel):
    answer: str = Field(..., description="Grounded agent answer synthesized from verified data")
    intent: str = Field(..., description="Classified query intent")
    tools_used: List[str] = Field(default_factory=list, description="List of safe backend tools invoked")
    sources: List[AgentSource] = Field(default_factory=list, description="Verified institutional source references")
    grounded: bool = Field(True, description="Whether answer is grounded in actual database/RAG records")
    activity_steps: List[str] = Field(default_factory=list, description="Safe user-facing activity step names")
