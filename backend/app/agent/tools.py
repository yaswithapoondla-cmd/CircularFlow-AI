import re
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc
from ..models.circulars import Circular
from ..models.actions import ActionItem
from ..models.acknowledgements import Acknowledgement
from ..models.recipients import Recipient
from ..services.rag_service import RAGService


def search_circulars(
    db: Session,
    query: str = "",
    department: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Searches institutional circulars in PostgreSQL by keyword, department, or status.
    """
    q = db.query(Circular)

    if query:
        STOP_WORDS = {
            "search", "circulars", "circular", "find", "show", "list", "tell", "me", "what",
            "is", "the", "are", "for", "about", "regarding", "with", "all", "please", "directive", "policy"
        }
        clean_q = re.sub(r'[^\w\s-]', ' ', query).strip().lower()
        search_terms = [t for t in clean_q.split() if t not in STOP_WORDS and len(t) > 2]
        if not search_terms:
            search_terms = [t for t in clean_q.split() if len(t) > 2]

        term_filters = []
        for term in search_terms:
            stem = term
            if stem.startswith("examin"):
                stem = "exam"
            elif stem.endswith("s") and len(stem) > 4:
                stem = stem[:-1]
            t = f"%{stem}%"
            term_filters.append(
                or_(
                    Circular.title.ilike(t),
                    Circular.ref_no.ilike(t),
                    Circular.summary.ilike(t),
                    Circular.category.ilike(t),
                    Circular.department.ilike(t),
                )
            )
        if term_filters:
            q = q.filter(and_(*term_filters))

    if department:
        q = q.filter(Circular.department.ilike(f"%{department}%"))

    if status:
        q = q.filter(Circular.status.ilike(status))

    # Order by published_date descending
    records = q.order_by(desc(Circular.published_date), desc(Circular.created_at)).limit(limit).all()

    return [
        {
            "id": c.id,
            "ref_no": c.ref_no,
            "title": c.title,
            "department": c.department,
            "category": c.category,
            "status": c.status,
            "priority": c.priority,
            "effective_date": c.effective_date,
            "published_date": c.published_date,
            "summary": c.summary,
            "supersedes_ref": c.supersedes_ref,
            "superseded_by_ref": c.superseded_by_ref,
        }
        for c in records
    ]


def get_latest_circular(
    db: Session,
    topic_or_dept: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Retrieves the most recent circular, optionally filtered by a specific topic or department.
    """
    q = db.query(Circular)

    if topic_or_dept:
        clean = topic_or_dept.strip().lower()
        # Remove punctuation
        clean = re.sub(r'[^\w\s-]', ' ', clean)
        # Remove filler words
        clean = re.sub(r'\b(about|on|the|regarding|for|policy|circular|directive|show|me|tell|latest)\b', ' ', clean).strip()
        terms = [t for t in clean.split() if len(t) > 2]
        if terms:
            term_clauses = [
                or_(
                    Circular.title.ilike(f"%{t}%"),
                    Circular.category.ilike(f"%{t}%"),
                    Circular.department.ilike(f"%{t}%"),
                    Circular.summary.ilike(f"%{t}%")
                )
                for t in terms
            ]
            q = q.filter(and_(*term_clauses))

    record = q.order_by(desc(Circular.published_date), desc(Circular.created_at)).first()
    if not record:
        return None

    return {
        "id": record.id,
        "ref_no": record.ref_no,
        "title": record.title,
        "department": record.department,
        "category": record.category,
        "status": record.status,
        "priority": record.priority,
        "effective_date": record.effective_date,
        "published_date": record.published_date,
        "author": record.author,
        "signatory": record.signatory,
        "summary": record.summary,
        "supersedes_ref": record.supersedes_ref,
        "superseded_by_ref": record.superseded_by_ref,
        "acknowledgement_rate": record.acknowledgement_rate,
    }


def get_circular_lineage(
    db: Session,
    identifier: str
) -> Dict[str, Any]:
    """
    Trace the governance lineage chain for a circular: what it superseded and what superseded it.
    """
    ident = identifier.strip()
    # Find circular by id or ref_no or title keyword
    circ = (
        db.query(Circular)
        .filter(or_(Circular.ref_no.ilike(ident), Circular.id.ilike(ident), Circular.title.ilike(f"%{ident}%")))
        .first()
    )

    if not circ:
        # Check if user mentioned a keyword like 'attendance' or 'exam'
        clean = re.sub(r'\b(policy|circular|directive|the|about)\b', '', ident, flags=re.I).strip()
        if clean:
            circ = db.query(Circular).filter(Circular.title.ilike(f"%{clean}%")).first()

    if not circ:
        return {"found": False, "target": identifier, "message": f"No circular found matching identifier '{identifier}'."}

    # Find what this circular supersedes (previous rule)
    superseded_circ = None
    if circ.supersedes_ref:
        superseded_circ = db.query(Circular).filter(Circular.ref_no == circ.supersedes_ref).first()
    elif circ.supersedes_id:
        superseded_circ = db.query(Circular).filter(Circular.id == circ.supersedes_id).first()

    # Find what superseded this circular (newer replacing rule)
    superseding_circ = None
    if circ.superseded_by_ref:
        superseding_circ = db.query(Circular).filter(Circular.ref_no == circ.superseded_by_ref).first()
    elif circ.superseded_by_id:
        superseding_circ = db.query(Circular).filter(Circular.id == circ.superseded_by_id).first()
    else:
        # Check if another circular lists this one as supersedes_ref
        superseding_circ = db.query(Circular).filter(
            or_(Circular.supersedes_ref == circ.ref_no, Circular.supersedes_id == circ.id)
        ).first()

    return {
        "found": True,
        "circular": {
            "id": circ.id,
            "ref_no": circ.ref_no,
            "title": circ.title,
            "status": circ.status,
            "effective_date": circ.effective_date,
        },
        "superseded_rule": {
            "ref_no": superseded_circ.ref_no,
            "title": superseded_circ.title,
            "status": superseded_circ.status,
            "effective_date": superseded_circ.effective_date,
        } if superseded_circ else ({"ref_no": circ.supersedes_ref} if circ.supersedes_ref else None),
        "superseding_replacement": {
            "ref_no": superseding_circ.ref_no,
            "title": superseding_circ.title,
            "status": superseding_circ.status,
            "effective_date": superseding_circ.effective_date,
        } if superseding_circ else ({"ref_no": circ.superseded_by_ref} if circ.superseded_by_ref else None),
    }


def get_acknowledgement_status(
    db: Session,
    circular_ref_or_id: Optional[str] = None,
    role_filter: Optional[str] = None,
    pending_only: bool = False
) -> Dict[str, Any]:
    """
    Queries acknowledgement compliance and recipient lists for circulars from PostgreSQL.
    """
    target_circ = None
    if circular_ref_or_id:
        clean = circular_ref_or_id.strip()
        target_circ = db.query(Circular).filter(
            or_(Circular.ref_no.ilike(clean), Circular.id.ilike(clean), Circular.title.ilike(f"%{clean}%"))
        ).first()
    else:
        # Default to latest active circular if unspecified
        target_circ = db.query(Circular).filter(Circular.status == "Active").order_by(desc(Circular.published_date)).first()

    if not target_circ:
        return {"found": False, "message": "No circular found to check acknowledgement records."}

    q = (
        db.query(Acknowledgement, Recipient)
        .join(Recipient, Acknowledgement.recipient_id == Recipient.id)
        .filter(Acknowledgement.circular_id == target_circ.id)
    )

    if role_filter:
        q = q.filter(Recipient.role.ilike(f"%{role_filter}%"))

    if pending_only:
        q = q.filter(Acknowledgement.acknowledgement_status == "Pending")

    rows = q.all()

    total_count = db.query(Acknowledgement).filter(Acknowledgement.circular_id == target_circ.id).count()
    ack_count = db.query(Acknowledgement).filter(
        Acknowledgement.circular_id == target_circ.id,
        Acknowledgement.acknowledgement_status == "Acknowledged"
    ).count()

    recipients_list = [
        {
            "name": rec.name,
            "role": rec.role,
            "department": rec.department,
            "status": ack.acknowledgement_status,
            "delivery_status": ack.delivery_status,
            "acknowledged_at": ack.acknowledged_at,
        }
        for ack, rec in rows
    ]

    return {
        "found": True,
        "circular": {
            "id": target_circ.id,
            "ref_no": target_circ.ref_no,
            "title": target_circ.title,
            "total_recipients": total_count,
            "acknowledged_recipients": ack_count,
            "compliance_rate": round((ack_count / total_count * 100) if total_count > 0 else target_circ.acknowledgement_rate, 1),
        },
        "filtered_count": len(recipients_list),
        "recipients": recipients_list,
        "role_filter": role_filter,
        "pending_only": pending_only,
    }


def get_pending_actions(
    db: Session,
    circular_ref: Optional[str] = None,
    department: Optional[str] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Retrieves pending and overdue action items from PostgreSQL.
    """
    q = db.query(ActionItem).filter(ActionItem.status.in_(["NOT_STARTED", "IN_PROGRESS", "OVERDUE"]))

    if circular_ref:
        clean = circular_ref.strip()
        q = q.filter(or_(
            ActionItem.source_circular_ref.ilike(f"%{clean}%"),
            ActionItem.source_circular_id.ilike(f"%{clean}%")
        ))

    if department:
        q = q.filter(ActionItem.responsible_department.ilike(f"%{department}%"))

    actions = q.order_by(desc(ActionItem.priority == "Critical"), desc(ActionItem.deadline)).limit(limit).all()

    return [
        {
            "action_id": a.action_id,
            "title": a.title,
            "description": a.description,
            "source_circular_ref": a.source_circular_ref,
            "responsible_role": a.responsible_role,
            "responsible_department": a.responsible_department,
            "deadline": a.deadline,
            "priority": a.priority,
            "status": a.status,
        }
        for a in actions
    ]


def search_knowledge_base(
    query: str,
    top_k: int = 4
) -> List[Dict[str, Any]]:
    """
    Queries ChromaDB RAG vector repository for verified institutional policy documents.
    """
    try:
        chunks = RAGService.retrieve(query=query, top_k=top_k)
        return [
            {
                "document": c.document,
                "content": c.content,
                "score": c.score,
                "chunk_id": c.chunk_id,
            }
            for c in chunks
        ]
    except Exception as exc:
        print(f"[Tools] ChromaDB knowledge retrieval error: {exc}")
        return []
