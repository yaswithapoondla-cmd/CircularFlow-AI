import re
from typing import Tuple, Dict, Any, Optional
from ..llm.client import get_llm_client

INTENT_LATEST = "LATEST_CIRCULAR"
INTENT_LINEAGE = "LINEAGE_QUERY"
INTENT_ACK = "ACKNOWLEDGEMENT_QUERY"
INTENT_ACTION = "ACTION_STATUS"
INTENT_SEARCH = "CIRCULAR_SEARCH"
INTENT_POLICY = "POLICY_SEARCH"
INTENT_GENERAL = "GENERAL_KNOWLEDGE"


def route_intent_deterministic(query: str) -> Tuple[str, Dict[str, Any]]:
    """
    Classifies user intent using deterministic keyword & semantic pattern matching.
    Returns (intent, extracted_parameters).
    """
    q = query.lower().strip()
    params: Dict[str, Any] = {}

    # 1. Lineage & Supersession checks (highest priority when replacement/supersedes is mentioned)
    if any(k in q for k in ["replace", "supersede", "lineage", "version tree", "predecessor", "successor", "previous attendance policy", "previous policy"]):
        # Extract potential circular reference like CIR-2026-052 or CF-2026-001
        ref_match = re.search(r'\b(cir[c]?-[0-9]{4}-[0-9]{3,4}|cf-[0-9]{4}-[0-9]{3,4}|circ-[0-9]{3})\b', q, re.I)
        if ref_match:
            params["target_ref"] = ref_match.group(0).upper()
        elif "attendance" in q:
            params["target_ref"] = "CIR-2026-052"
        elif "ai" in q or "compute" in q:
            params["target_ref"] = "CIRC-2026-089"
        elif "exam" in q:
            params["target_ref"] = "CIRC-2026-092"
        return INTENT_LINEAGE, params

    # 2. Acknowledgement compliance & recipient status checks
    if any(k in q for k in ["acknowledg", "who signed", "who has not", "pending recipient", "compliance rate", "signed by students"]):
        ref_match = re.search(r'\b(cir[c]?-[0-9]{4}-[0-9]{3,4}|cf-[0-9]{4}-[0-9]{3,4}|circ-[0-9]{3})\b', q, re.I)
        if ref_match:
            params["circular_ref"] = ref_match.group(0).upper()
        elif "attendance" in q:
            params["circular_ref"] = "CIR-2026-052"

        if "student" in q:
            params["role_filter"] = "Student"
        elif "faculty" in q:
            params["role_filter"] = "Faculty"
        elif "hod" in q:
            params["role_filter"] = "HOD"

        if any(w in q for k in ["not", "pending", "haven't", "unacknowledged"] for w in [k]):
            params["pending_only"] = True

        return INTENT_ACK, params

    # 3. Action Items & Pending Tasks
    if any(k in q for k in ["action", "task", "deadline", "pending action", "overdue"]):
        ref_match = re.search(r'\b(cir[c]?-[0-9]{4}-[0-9]{3,4}|cf-[0-9]{4}-[0-9]{3,4}|circ-[0-9]{3})\b', q, re.I)
        if ref_match:
            params["circular_ref"] = ref_match.group(0).upper()
        return INTENT_ACTION, params

    # 4. Latest Circular Queries
    if any(k in q for k in ["latest", "recent", "newest", "last circular", "current circular"]):
        # Extract topic
        topic = q
        for remove_word in ["show me", "tell me", "what is", "the", "latest", "circular", "recent", "about", "on", "directive", "please"]:
            topic = re.sub(rf'\b{remove_word}\b', '', topic, flags=re.I)
        topic = re.sub(r'[^\w\s-]', ' ', topic).strip()
        params["topic"] = topic
        return INTENT_LATEST, params

    # 5. Institutional Policy / Document / RAG Search
    if any(k in q for k in ["policy document", "handbook", "code of conduct", "guideline", "rule regarding", "university policy"]):
        params["search_query"] = q
        return INTENT_POLICY, params

    # 6. General Circular Search
    if any(k in q for k in ["search", "find", "list", "show circulars", "circular"]):
        params["search_query"] = q
        return INTENT_SEARCH, params

    # 7. Default to Policy / Knowledge Base search
    params["search_query"] = q
    return INTENT_POLICY, params


def route_intent(query: str) -> Tuple[str, Dict[str, Any]]:
    """
    Public entry point for intent routing.
    Evaluates query deterministically, allowing rapid zero-dependency execution.
    """
    intent, params = route_intent_deterministic(query)
    return intent, params
