"""
Circular Generation Service — Phase 18
Uses existing LLM client to generate structured circular content.
Falls back to a draft template if LLM is unavailable — never crashes.
"""
import json
import logging
import random
from datetime import date
from typing import Optional

from ..llm.client import get_llm_client
from ..llm.prompts import CIRCULAR_GENERATION_SYSTEM_PROMPT
from ..schemas.circular_gen import CircularGenerateRequest, GeneratedCircularContent

logger = logging.getLogger("circularflow.circular_gen")


def _generate_ref_no() -> str:
    """Auto-generate a circular reference number."""
    return f"CIRC-2026-{random.randint(100, 999)}"


def _today_str() -> str:
    return date.today().strftime("%d %B %Y")


def _make_fallback(request: CircularGenerateRequest) -> GeneratedCircularContent:
    """
    Returns a professional draft template when LLM is unavailable.
    No invented policies — uses safe placeholder text.
    """
    dept = request.department or "Office of the Registrar"
    audience = request.audience or "All Stakeholders"
    effective = request.effective_date or "To be determined"
    priority = request.priority or "High"
    category = request.category or "Policy & Compliance"

    body = (
        f"This circular is issued by the {dept} regarding: {request.topic}.\n\n"
        "All concerned stakeholders are requested to take note of the following directives and ensure "
        "strict compliance within the stipulated timelines. Departments are advised to acknowledge "
        "receipt of this circular through the institutional governance portal.\n\n"
        "Further details regarding implementation guidelines will be communicated through official "
        "channels. Queries, if any, may be directed to the contact information provided below.\n\n"
        "NOTE: This is an AI-generated DRAFT for review purposes only. The content has not been "
        "officially approved or published. Please review and modify as required before final issuance."
    )

    instructions = (
        "1. All concerned departments must acknowledge receipt of this circular within 3 working days.\n"
        "2. Department Heads are responsible for communicating the contents to all staff members.\n"
        "3. Any clarifications should be sought from the designated contact before the effective date.\n"
        "4. Records of compliance must be maintained and made available for audit purposes.\n"
        "5. This draft requires review and approval from the competent authority before issuance."
    )

    return GeneratedCircularContent(
        title=f"[DRAFT] {request.topic}",
        subject=request.topic,
        department=dept,
        audience=audience,
        reference=_generate_ref_no(),
        date=_today_str(),
        effective_date=effective,
        body=body,
        instructions=instructions,
        contact_information=(
            "Registrar's Office\n"
            "Vignan's Foundation for Science, Technology & Research\n"
            "Email: registrar@vignan.ac.in | Phone: [To be updated]"
        ),
        signatory_name="[Authorized Signatory]",
        signatory_designation="University Registrar",
        priority=priority,
        category=category,
        is_ai_generated=True,
    )


def generate_circular(request: CircularGenerateRequest) -> GeneratedCircularContent:
    """
    Generates a structured institutional circular using the LLM.
    Falls back to template draft if LLM is not configured or fails.
    """
    client = get_llm_client()

    if client is None:
        logger.info("[CircularGen] No LLM_API_KEY configured — returning template draft.")
        return _make_fallback(request)

    # Build the user prompt
    user_prompt = (
        f"Generate a formal institutional circular for the following:\n\n"
        f"Topic / Purpose: {request.topic}\n"
        f"Department: {request.department or 'Office of the Registrar'}\n"
        f"Target Audience: {request.audience or 'All Staff and Students'}\n"
        f"Effective Date: {request.effective_date or 'As specified by authority'}\n"
        f"Priority: {request.priority or 'High'}\n"
        f"Category: {request.category or 'Policy & Compliance'}\n"
    )
    if request.additional_instructions:
        user_prompt += f"\nAdditional Instructions from user:\n{request.additional_instructions}\n"

    user_prompt += (
        f"\nToday's date: {_today_str()}\n"
        "Return ONLY a JSON object with the required fields. No extra text."
    )

    try:
        from ..config import get_settings
        settings = get_settings()
        logger.info(f"[CircularGen] Calling LLM ({settings.LLM_MODEL}) for circular generation.")
        response = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": CIRCULAR_GENERATION_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=1200,
        )
        raw = response.choices[0].message.content.strip()

        # Strip markdown code fences if model added them despite instructions
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:-1]) if len(lines) > 2 else raw

        parsed = json.loads(raw)

        dept = request.department or "Office of the Registrar"
        priority = request.priority or "High"
        category = request.category or "Policy & Compliance"

        return GeneratedCircularContent(
            title=parsed.get("title", f"[DRAFT] {request.topic}"),
            subject=parsed.get("subject", request.topic),
            department=parsed.get("department", dept),
            audience=parsed.get("audience", request.audience or "All Stakeholders"),
            reference=parsed.get("reference", _generate_ref_no()),
            date=parsed.get("date", _today_str()),
            effective_date=parsed.get("effective_date", request.effective_date or _today_str()),
            body=parsed.get("body", ""),
            instructions=parsed.get("instructions", ""),
            contact_information=parsed.get("contact_information", "Registrar's Office — registrar@vignan.ac.in"),
            signatory_name=parsed.get("signatory_name", "[Authorized Signatory]"),
            signatory_designation=parsed.get("signatory_designation", "University Registrar"),
            priority=priority,
            category=category,
            is_ai_generated=True,
        )

    except json.JSONDecodeError as e:
        logger.warning(f"[CircularGen] LLM returned non-JSON response: {e}. Using fallback.")
        return _make_fallback(request)
    except Exception as e:
        logger.error(f"[CircularGen] LLM error: {e}. Using fallback.", exc_info=True)
        return _make_fallback(request)
