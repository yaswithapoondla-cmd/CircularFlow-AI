import uuid
import random
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from ..models.circulars import Circular
from ..models.departments import Department
from ..models.audit_logs import AuditLog
from ..models.users import User
from ..schemas.circular import CircularListResponse, Circular as CircularSchema, CircularCreate


class CircularService:

    @staticmethod
    def list_circulars(
        db: Session,
        department: Optional[str] = None,
        status: Optional[str] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> CircularListResponse:
        query = db.query(Circular)

        if department and department.lower() != "all departments":
            query = query.filter(
                func.lower(Circular.department) == department.lower()
            )

        if status and status.lower() != "all":
            query = query.filter(
                func.lower(Circular.status) == status.lower()
            )

        if category and category.lower() != "all":
            query = query.filter(
                func.lower(Circular.category) == category.lower()
            )

        if search:
            q = f"%{search.lower()}%"
            query = query.filter(
                or_(
                    func.lower(Circular.title).like(q),
                    func.lower(Circular.ref_no).like(q),
                    func.lower(Circular.summary).like(q),
                )
            )

        total = query.count()
        active_count = db.query(Circular).filter(
            func.lower(Circular.status) == "active"
        ).count()

        # Distinct department list from full table (not filtered subset)
        departments_rows = db.query(Circular.department).distinct().order_by(Circular.department).all()
        departments: List[str] = [row[0] for row in departments_rows if row[0]]

        start_idx = (page - 1) * page_size
        orm_items = query.order_by(Circular.published_date.desc()).offset(start_idx).limit(page_size).all()

        items = [CircularSchema.model_validate(c.__dict__) for c in orm_items]

        return CircularListResponse(
            items=items,
            total=total,
            active_count=active_count,
            departments=departments,
            page=page,
            page_size=page_size,
        )

    @staticmethod
    def get_circular_by_id(db: Session, circular_id: str) -> Optional[CircularSchema]:
        clean_id = circular_id.strip()
        circular = db.query(Circular).filter(
            or_(
                func.lower(Circular.id) == clean_id.lower(),
                func.lower(Circular.ref_no) == clean_id.lower(),
            )
        ).first()

        if circular is None:
            return None

        return CircularSchema.model_validate(circular.__dict__)

    @staticmethod
    def create_circular(
        db: Session,
        data: CircularCreate,
        current_user: Optional[User] = None,
    ) -> CircularSchema:
        """
        Persist a new circular draft in PostgreSQL.
        Ensures unique ID and reference number, writes audit log, and returns the created circular.
        Never auto-publishes.
        """
        # 1. Unique ID
        new_id = f"circ-{uuid.uuid4().hex[:6]}"
        while db.query(Circular).filter(Circular.id == new_id).first():
            new_id = f"circ-{uuid.uuid4().hex[:6]}"

        # 2. Unique Reference Number
        if data.reference and data.reference.strip():
            ref = data.reference.strip()
            if db.query(Circular).filter(func.lower(Circular.ref_no) == ref.lower()).first():
                ref = f"{ref}-{uuid.uuid4().hex[:4].upper()}"
        else:
            year = datetime.now(timezone.utc).year
            num = random.randint(100, 999)
            ref = f"CIRC-{year}-{num}"
            while db.query(Circular).filter(func.lower(Circular.ref_no) == ref.lower()).first():
                num = random.randint(100, 999)
                ref = f"CIRC-{year}-{num}"

        # 3. Match department_id if found
        dept_id = None
        dept = db.query(Department).filter(
            or_(
                func.lower(Department.name) == data.department.strip().lower(),
                func.lower(Department.code) == data.department.strip().lower(),
                Department.name.ilike(f"%{data.department.strip()}%"),
            )
        ).first()
        if dept:
            dept_id = dept.id

        # 4. Target audience list
        if data.target_audience and len(data.target_audience) > 0:
            target_audience = data.target_audience
        elif data.audience and data.audience.strip():
            parts = [a.strip() for a in data.audience.split(",") if a.strip()]
            target_audience = parts if len(parts) > 1 else [data.audience.strip()]
        else:
            target_audience = ["All Campus Occupants"]

        # 5. Summary
        if data.subject and data.subject.strip():
            summary = data.subject.strip()
        else:
            summary = data.body.strip()[:250]

        # 6. Required actions
        if data.required_actions and len(data.required_actions) > 0:
            required_actions = data.required_actions
        elif data.instructions and data.instructions.strip():
            lines = [
                line.strip().lstrip("0123456789.-* ")
                for line in data.instructions.split("\n")
                if line.strip()
            ]
            required_actions = lines[:5] if lines else []
        else:
            required_actions = []

        # 7. Author & Signatory
        author = current_user.name if current_user and current_user.name else (
            data.signatory_name or "Institutional Administrator"
        )
        signatory = data.signatory_name or (
            current_user.name if current_user and current_user.name else "Registrar"
        )

        # 8. Status: always Draft or Under Review (never Active on creation)
        circ_status = "Draft"
        if data.status and data.status.strip().lower() in ("draft", "under review"):
            circ_status = "Under Review" if data.status.strip().lower() == "under review" else "Draft"

        # 9. Dates & Tags
        now_dt = datetime.now(timezone.utc)
        now_date_str = now_dt.strftime("%Y-%m-%d")
        effective_date = data.effective_date or now_date_str
        tags = data.tags if data.tags else [data.category or "Policy & Compliance", data.priority or "High"]
        file_attachment = f"{ref}.pdf"

        # 10. Instantiate ORM model
        new_circ = Circular(
            id=new_id,
            ref_no=ref,
            title=data.title.strip(),
            department=data.department.strip(),
            department_id=dept_id,
            category=data.category or "Policy & Compliance",
            status=circ_status,
            priority=data.priority or "High",
            published_date=now_date_str,
            effective_date=effective_date,
            version="v1.0",
            author=author,
            signatory=signatory,
            summary=summary,
            body=data.body.strip(),
            target_audience=target_audience,
            tags=tags,
            required_actions=required_actions,
            acknowledgement_rate=0.0,
            total_recipients=0,
            acknowledged_recipients=0,
            file_attachment=file_attachment,
            created_at=now_dt,
            updated_at=now_dt,
        )
        db.add(new_circ)

        # 11. Write Audit Log
        audit = AuditLog(
            id=str(uuid.uuid4()),
            event_type="CIRCULAR_DRAFT_CREATED",
            description=f"Draft circular {ref} ({data.title}) created by {author}.",
            user_name=author,
            user_role=current_user.role if current_user else "Staff",
            related_circular_id=new_id,
            timestamp=now_dt,
            event_metadata={
                "ref_no": ref,
                "title": data.title,
                "department": data.department,
                "priority": data.priority,
                "status": circ_status,
            },
        )
        db.add(audit)

        db.commit()
        db.refresh(new_circ)

        return CircularSchema.model_validate(new_circ.__dict__)

