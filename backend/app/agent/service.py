import logging
from typing import List
from sqlalchemy.orm import Session
from .schemas import AgentChatResponse, AgentSource
from .router import (
    route_intent,
    INTENT_LATEST,
    INTENT_LINEAGE,
    INTENT_ACK,
    INTENT_ACTION,
    INTENT_SEARCH,
    INTENT_POLICY,
)
from .tools import (
    search_circulars,
    get_latest_circular,
    get_circular_lineage,
    get_acknowledgement_status,
    get_pending_actions,
    search_knowledge_base,
)
from .prompts import (
    format_latest_circular_answer,
    format_lineage_answer,
    format_acknowledgement_answer,
    format_pending_actions_answer,
)

logger = logging.getLogger("circularflow.agent")


class AgentService:
    @classmethod
    def process_query(cls, db: Session, message: str) -> AgentChatResponse:
        """
        Main agent orchestration loop:
        1. Classifies user intent and extracts target parameters.
        2. Dispatches to safe institutional backend tools.
        3. Aggregates data, verifies evidence, and produces a grounded response.
        """
        intent, params = route_intent(message)
        logger.info(f"[AgentService] Query: '{message}' | Resolved Intent: {intent} | Params: {params}")

        tools_used: List[str] = []
        sources: List[AgentSource] = []
        activity_steps: List[str] = ["Understanding request..."]
        grounded = False
        answer = ""

        try:
            # ── Case 1: Latest Circular Query ─────────────────────────────────────
            if intent == INTENT_LATEST:
                tools_used.append("get_latest_circular")
                activity_steps.append("Searching circular records in PostgreSQL...")
                topic = params.get("topic")
                circ = get_latest_circular(db, topic_or_dept=topic)

                if circ:
                    answer = format_latest_circular_answer(circ)
                    sources.append(AgentSource(
                        source_type="circular",
                        title=circ["title"],
                        reference=circ["ref_no"],
                        score=1.0
                    ))
                    grounded = True
                else:
                    # Fallback to search_circulars if specific title
                    tools_used.append("search_circulars")
                    alt_circs = search_circulars(db, query=topic or message, limit=1)
                    if alt_circs:
                        answer = format_latest_circular_answer(alt_circs[0])
                        sources.append(AgentSource(
                            source_type="circular",
                            title=alt_circs[0]["title"],
                            reference=alt_circs[0]["ref_no"],
                            score=0.9
                        ))
                        grounded = True
                    else:
                        answer = f"The institutional registry does not contain any published circulars regarding '{message}'."
                        grounded = False

            # ── Case 2: Lineage & Supersession Query ──────────────────────────────
            elif intent == INTENT_LINEAGE:
                tools_used.append("get_circular_lineage")
                activity_steps.append("Tracing circular lineage tree & supersession records...")
                target = params.get("target_ref", message)
                lineage = get_circular_lineage(db, identifier=target)
                answer = format_lineage_answer(lineage, target)

                if lineage.get("found"):
                    circ = lineage["circular"]
                    sources.append(AgentSource(
                        source_type="circular",
                        title=circ["title"],
                        reference=circ["ref_no"],
                        score=1.0
                    ))
                    if lineage.get("superseded_rule") and lineage["superseded_rule"].get("ref_no"):
                        sources.append(AgentSource(
                            source_type="circular",
                            title=lineage["superseded_rule"].get("title", "Superseded Rule"),
                            reference=lineage["superseded_rule"]["ref_no"],
                            score=0.95
                        ))
                    if lineage.get("superseding_replacement") and lineage["superseding_replacement"].get("ref_no"):
                        sources.append(AgentSource(
                            source_type="circular",
                            title=lineage["superseding_replacement"].get("title", "Successor Replacement"),
                            reference=lineage["superseding_replacement"]["ref_no"],
                            score=0.95
                        ))
                    grounded = True
                else:
                    grounded = False

            # ── Case 3: Acknowledgement & Compliance Status Query ─────────────────
            elif intent == INTENT_ACK:
                tools_used.append("get_acknowledgement_status")
                activity_steps.append("Checking recipient acknowledgement records in PostgreSQL...")
                target_ref = params.get("circular_ref")
                role_filter = params.get("role_filter")
                pending_only = params.get("pending_only", False)

                ack_data = get_acknowledgement_status(
                    db,
                    circular_ref_or_id=target_ref,
                    role_filter=role_filter,
                    pending_only=pending_only
                )
                answer = format_acknowledgement_answer(ack_data)

                if ack_data.get("found"):
                    circ = ack_data["circular"]
                    sources.append(AgentSource(
                        source_type="circular",
                        title=circ["title"],
                        reference=circ["ref_no"],
                        score=1.0
                    ))
                    grounded = True
                else:
                    grounded = False

            # ── Case 4: Pending Action Items Query ────────────────────────────────
            elif intent == INTENT_ACTION:
                tools_used.append("get_pending_actions")
                activity_steps.append("Retrieving action item status and deadlines from database...")
                target_ref = params.get("circular_ref")
                actions = get_pending_actions(db, circular_ref=target_ref)
                answer = format_pending_actions_answer(actions)

                if actions:
                    for a in actions[:4]:
                        sources.append(AgentSource(
                            source_type="action_record",
                            title=a["title"],
                            reference=a["action_id"],
                            score=1.0
                        ))
                    grounded = True
                else:
                    grounded = False

            # ── Case 5: Policy & Document Semantic Knowledge Search ───────────────
            elif intent == INTENT_POLICY:
                tools_used.append("search_knowledge_base")
                activity_steps.append("Querying ChromaDB vector store for policy documents...")
                query_str = params.get("search_query", message)
                chunks = search_knowledge_base(query=query_str, top_k=3)

                if chunks:
                    top_chunk = chunks[0]
                    answer = (
                        f"### Verified Institutional Policy Record\n"
                        f"**Source Document:** `{top_chunk['document']}` (Match Confidence: {int(top_chunk['score'] * 100)}%)\n\n"
                        f"> {top_chunk['content']}\n\n"
                        f"*Grounded from verified policy repository.*"
                    )
                    for c in chunks:
                        sources.append(AgentSource(
                            source_type="policy_doc",
                            title=c["document"],
                            reference=c["document"],
                            score=c["score"]
                        ))
                    grounded = True
                else:
                    # Also cross-check database circulars before declaring absence
                    tools_used.append("search_circulars")
                    activity_steps.append("Cross-checking circular database...")
                    circs = search_circulars(db, query=query_str, limit=3)
                    if circs:
                        c = circs[0]
                        answer = (
                            f"### Verified Governance Directive: {c['ref_no']}\n"
                            f"**Title:** {c['title']} (Status: `{c['status']}`)\n\n"
                            f"**Official Summary:**\n{c['summary']}\n\n"
                            f"• **Effective Date:** {c['effective_date']} | **Department:** {c['department']}"
                        )
                        sources.append(AgentSource(
                            source_type="circular",
                            title=c["title"],
                            reference=c["ref_no"],
                            score=0.88
                        ))
                        grounded = True
                    else:
                        answer = "The current institutional knowledge base and circular registry do not contain verified policy records covering this inquiry."
                        grounded = False

            # ── Case 6: General Circular Search ───────────────────────────────────
            else:
                tools_used.append("search_circulars")
                activity_steps.append("Searching circular database in PostgreSQL...")
                query_str = params.get("search_query", message)
                circs = search_circulars(db, query=query_str, limit=4)

                if circs:
                    lines = [f"### Institutional Circulars Matching Search ({len(circs)} found)\n"]
                    for c in circs:
                        lines.append(
                            f"• **{c['ref_no']}: {c['title']}**\n"
                            f"  - **Status:** `{c['status']}` | **Dept:** {c['department']}\n"
                            f"  - **Effective:** {c['effective_date']}\n"
                            f"  - *{c['summary'][:150]}...*\n"
                        )
                        sources.append(AgentSource(
                            source_type="circular",
                            title=c["title"],
                            reference=c["ref_no"],
                            score=1.0
                        ))
                    answer = "\n".join(lines)
                    grounded = True
                else:
                    answer = f"No institutional circulars found matching '{message}'."
                    grounded = False

        except Exception as exc:
            logger.error(f"[AgentService] Error processing query: {exc}", exc_info=True)
            answer = "The current institutional records do not contain enough verified information to answer this question."
            grounded = False

        activity_steps.append("Preparing answer...")

        return AgentChatResponse(
            answer=answer,
            intent=intent,
            tools_used=tools_used,
            sources=sources,
            grounded=grounded,
            activity_steps=activity_steps,
        )
