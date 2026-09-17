"""
Circular PDF Generation Service — Phase 18
Builds a professional university-branded PDF using ReportLab.
"""
import io
import os
import logging
from datetime import date

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image, PageBreak
)
from reportlab.platypus import KeepTogether
from reportlab.lib import colors

from ..schemas.circular_gen import CircularPDFRequest

logger = logging.getLogger("circularflow.pdf")

# ── Asset Paths ───────────────────────────────────────────────────────────────
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_LOGO_PATH = os.path.join(_BACKEND_DIR, "assets", "vignan-logo.jpg")

# ── Brand Colors ──────────────────────────────────────────────────────────────
NAVY = HexColor("#1a2a6c")
BLUE = HexColor("#2563eb")
LIGHT_BLUE = HexColor("#e8f0fe")
GOLD = HexColor("#b21f1f")
LIGHT_GRAY = HexColor("#f8fafc")
MID_GRAY = HexColor("#64748b")
DARK_TEXT = HexColor("#1e293b")
BORDER_GRAY = HexColor("#cbd5e1")


def _get_styles():
    base = getSampleStyleSheet()
    styles = {
        "institution": ParagraphStyle(
            "institution",
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=NAVY,
            alignment=TA_CENTER,
        ),
        "sub_institution": ParagraphStyle(
            "sub_institution",
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=MID_GRAY,
            alignment=TA_CENTER,
        ),
        "circular_heading": ParagraphStyle(
            "circular_heading",
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=NAVY,
            alignment=TA_CENTER,
            spaceAfter=4,
        ),
        "draft_badge": ParagraphStyle(
            "draft_badge",
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=GOLD,
            alignment=TA_CENTER,
            spaceAfter=8,
        ),
        "field_label": ParagraphStyle(
            "field_label",
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=11,
            textColor=MID_GRAY,
        ),
        "field_value": ParagraphStyle(
            "field_value",
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=DARK_TEXT,
        ),
        "subject_line": ParagraphStyle(
            "subject_line",
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=14,
            textColor=DARK_TEXT,
        ),
        "body_text": ParagraphStyle(
            "body_text",
            fontName="Helvetica",
            fontSize=9.5,
            leading=14,
            textColor=DARK_TEXT,
            alignment=TA_JUSTIFY,
            spaceAfter=8,
        ),
        "section_heading": ParagraphStyle(
            "section_heading",
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            textColor=NAVY,
            spaceBefore=10,
            spaceAfter=4,
        ),
        "instruction_text": ParagraphStyle(
            "instruction_text",
            fontName="Helvetica",
            fontSize=9.5,
            leading=14,
            textColor=DARK_TEXT,
            alignment=TA_LEFT,
            spaceAfter=6,
        ),
        "footer_text": ParagraphStyle(
            "footer_text",
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=MID_GRAY,
            alignment=TA_CENTER,
        ),
        "signatory_name": ParagraphStyle(
            "signatory_name",
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            textColor=DARK_TEXT,
        ),
        "signatory_desig": ParagraphStyle(
            "signatory_desig",
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=MID_GRAY,
        ),
        "contact_text": ParagraphStyle(
            "contact_text",
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=DARK_TEXT,
        ),
    }
    return styles


def _add_page_number(canvas, doc):
    """Draws page number in the footer of each page."""
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MID_GRAY)
    page_num = canvas.getPageNumber()
    text = f"Page {page_num} | CircularFlow AI — Vignan's FSTR | DRAFT — Pending Official Approval"
    canvas.drawCentredString(A4[0] / 2.0, 1.0 * cm, text)
    # Bottom line
    canvas.setStrokeColor(BORDER_GRAY)
    canvas.setLineWidth(0.5)
    canvas.line(2 * cm, 1.4 * cm, A4[0] - 2 * cm, 1.4 * cm)
    canvas.restoreState()


def build_circular_pdf(request: CircularPDFRequest) -> bytes:
    """
    Builds an official university circular PDF and returns raw bytes.
    Falls back gracefully if logo asset is missing.
    """
    c = request.content
    buffer = io.BytesIO()
    s = _get_styles()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2.0 * cm,
        bottomMargin=2.0 * cm,
        title=c.title,
        author=c.signatory_name,
        subject=c.subject,
        creator="CircularFlow AI — Vignan's FSTR",
    )

    story = []

    # ── HEADER: Logo + Institution Name ──────────────────────────────────────
    has_logo = os.path.exists(_LOGO_PATH)
    if has_logo:
        try:
            logo = Image(_LOGO_PATH, width=3.5 * cm, height=3.5 * cm, kind="proportional")
            logo.hAlign = "CENTER"
            header_data = [[logo, Paragraph(
                f'<b>VIGNAN\'S FOUNDATION FOR SCIENCE, TECHNOLOGY &amp; RESEARCH</b><br/>'
                f'<font size="8" color="#64748b">Deemed to be University | NAAC A+ | NIRF Ranked</font><br/>'
                f'<font size="7" color="#64748b">Vadlamudi, Guntur — 522 213, Andhra Pradesh, India</font><br/>'
                f'<font size="7" color="#94a3b8">Phone: +91-863-2344700 | www.vignan.ac.in</font>',
                s["institution"]
            )]]
            header_table = Table(header_data, colWidths=[4 * cm, 13 * cm])
            header_table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (0, 0), "CENTER"),
            ]))
            story.append(header_table)
        except Exception as e:
            logger.warning(f"[PDF] Could not embed logo: {e}. Using text header.")
            story.append(Paragraph("VIGNAN'S FOUNDATION FOR SCIENCE, TECHNOLOGY & RESEARCH", s["institution"]))
    else:
        story.append(Paragraph("VIGNAN'S FOUNDATION FOR SCIENCE, TECHNOLOGY & RESEARCH", s["institution"]))
        story.append(Paragraph("Deemed to be University | Vadlamudi, Guntur — 522 213", s["sub_institution"]))

    story.append(Spacer(1, 0.3 * cm))
    story.append(HRFlowable(width="100%", thickness=2, color=NAVY, spaceAfter=0))
    story.append(HRFlowable(width="100%", thickness=1, color=GOLD, spaceBefore=2, spaceAfter=6))

    # ── CIRCULAR HEADING ──────────────────────────────────────────────────────
    story.append(Paragraph("CIRCULAR", s["circular_heading"]))
    if c.is_ai_generated:
        story.append(Paragraph("⚠  AI-GENERATED DRAFT — REQUIRES OFFICIAL REVIEW AND APPROVAL BEFORE ISSUANCE", s["draft_badge"]))

    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_GRAY, spaceAfter=8))

    # ── METADATA TABLE ────────────────────────────────────────────────────────
    priority_color = {"Critical": "#dc2626", "High": "#ea580c", "Medium": "#d97706", "Low": "#16a34a"}.get(c.priority, "#64748b")
    meta_data = [
        [
            Paragraph("Circular Reference:", s["field_label"]),
            Paragraph(f'<b>{c.reference}</b>', s["field_value"]),
            Paragraph("Date of Issue:", s["field_label"]),
            Paragraph(c.date, s["field_value"]),
        ],
        [
            Paragraph("Issuing Department:", s["field_label"]),
            Paragraph(c.department, s["field_value"]),
            Paragraph("Priority:", s["field_label"]),
            Paragraph(f'<font color="{priority_color}"><b>{c.priority}</b></font>', s["field_value"]),
        ],
        [
            Paragraph("Effective From:", s["field_label"]),
            Paragraph(f'<b>{c.effective_date}</b>', s["field_value"]),
            Paragraph("Category:", s["field_label"]),
            Paragraph(c.category, s["field_value"]),
        ],
    ]

    meta_table = Table(meta_data, colWidths=[4 * cm, 7 * cm, 3.5 * cm, 3.5 * cm])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BLUE),
        ("BACKGROUND", (0, 0), (0, -1), HexColor("#dbeafe")),
        ("BACKGROUND", (2, 0), (2, -1), HexColor("#dbeafe")),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_GRAY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [LIGHT_BLUE, white]),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 0.5 * cm))

    # ── TO / AUDIENCE ─────────────────────────────────────────────────────────
    addr_data = [
        [Paragraph("To:", s["field_label"]), Paragraph(c.audience, s["field_value"])],
    ]
    addr_table = Table(addr_data, colWidths=[2 * cm, 16 * cm])
    addr_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(addr_table)
    story.append(Spacer(1, 0.2 * cm))

    # ── SUBJECT ───────────────────────────────────────────────────────────────
    subj_data = [
        [Paragraph("Subject:", s["field_label"]), Paragraph(f'<b>{c.subject}</b>', s["subject_line"])],
    ]
    subj_table = Table(subj_data, colWidths=[2 * cm, 16 * cm])
    subj_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(subj_table)
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_GRAY, spaceBefore=8, spaceAfter=10))

    # ── BODY ──────────────────────────────────────────────────────────────────
    story.append(Paragraph("Matter", s["section_heading"]))
    for para in c.body.split("\n\n"):
        para = para.strip()
        if para:
            story.append(Paragraph(para.replace("\n", "<br/>"), s["body_text"]))

    # ── INSTRUCTIONS ──────────────────────────────────────────────────────────
    if c.instructions:
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph("Compliance Instructions", s["section_heading"]))
        for line in c.instructions.split("\n"):
            line = line.strip()
            if line:
                story.append(Paragraph(line, s["instruction_text"]))

    # ── CONTACT INFORMATION ───────────────────────────────────────────────────
    if c.contact_information:
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph("For Queries", s["section_heading"]))
        for line in c.contact_information.split("\n"):
            line = line.strip()
            if line:
                story.append(Paragraph(line, s["contact_text"]))

    # ── SIGNATORY ─────────────────────────────────────────────────────────────
    story.append(Spacer(1, 1.0 * cm))
    sig_block = [
        [
            Paragraph("", s["body_text"]),
            Paragraph(
                f'{c.signatory_name}<br/>'
                f'<font color="#64748b">{c.signatory_designation}</font><br/>'
                f'<font size="8" color="#94a3b8">Vignan\'s Foundation for Science, Technology &amp; Research</font>',
                s["signatory_name"]
            )
        ]
    ]
    sig_table = Table(sig_block, colWidths=[10 * cm, 8 * cm])
    sig_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
    ]))
    story.append(sig_table)
    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_GRAY))

    # ── FOOTER NOTE ───────────────────────────────────────────────────────────
    if c.is_ai_generated:
        story.append(Spacer(1, 0.2 * cm))
        story.append(Paragraph(
            "This document was generated by CircularFlow AI as a DRAFT. "
            "It has NOT been officially approved or published. "
            "Review and obtain appropriate authorization before formal issuance.",
            s["footer_text"]
        ))

    # ── BUILD ─────────────────────────────────────────────────────────────────
    try:
        doc.build(story, onFirstPage=_add_page_number, onLaterPages=_add_page_number)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
    except Exception as e:
        logger.error(f"[PDF] Build error: {e}", exc_info=True)
        raise
