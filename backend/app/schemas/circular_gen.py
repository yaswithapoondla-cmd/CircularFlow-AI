"""
Pydantic schemas for AI-powered circular generation and PDF export.
Phase 18 — CircularFlow AI
"""
from typing import Optional
from pydantic import BaseModel, Field


class CircularGenerateRequest(BaseModel):
    """Request body for POST /api/v1/circulars/generate"""
    topic: str = Field(..., min_length=3, description="Topic or purpose of the circular")
    department: Optional[str] = Field(None, description="Issuing department")
    audience: Optional[str] = Field(None, description="Target audience or recipients")
    effective_date: Optional[str] = Field(None, description="Effective date (YYYY-MM-DD or human readable)")
    priority: Optional[str] = Field("High", description="Priority: Critical, High, Medium, Low")
    additional_instructions: Optional[str] = Field(None, description="Extra guidance for the AI")
    category: Optional[str] = Field("Policy & Compliance", description="Governance category")


class GeneratedCircularContent(BaseModel):
    """Structured circular content — output of AI generation OR manual form."""
    title: str = Field(..., description="Official circular title")
    subject: str = Field(..., description="Subject line")
    department: str = Field(..., description="Issuing department")
    audience: str = Field(..., description="Target audience / To field")
    reference: str = Field(..., description="Circular reference number")
    date: str = Field(..., description="Date of issue")
    effective_date: str = Field(..., description="Effective from date")
    body: str = Field(..., description="Main body / matter of the circular")
    instructions: str = Field(..., description="Compliance instructions")
    contact_information: str = Field(..., description="Contact details for queries")
    signatory_name: str = Field(..., description="Signatory full name")
    signatory_designation: str = Field(..., description="Signatory designation")
    priority: str = Field("High", description="Priority level")
    category: str = Field("Policy & Compliance", description="Governance category")
    is_ai_generated: bool = Field(True, description="Whether the content was AI-generated")


class CircularPDFRequest(BaseModel):
    """Request body for POST /api/v1/circulars/generate-pdf — accepts final circular content."""
    content: GeneratedCircularContent
    institution_name: str = Field(
        "Vignan's Foundation for Science, Technology & Research",
        description="Institution name for PDF header"
    )
