"""
PDF report generation service using ReportLab.
Produces professional forensics investigation reports.
"""

import os
import logging
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from flask import current_app

logger = logging.getLogger(__name__)

# ── Palette ────────────────────────────────────────────────────────────────
DARK_BG    = colors.HexColor("#0d1117")
ACCENT     = colors.HexColor("#00d4ff")
ACCENT2    = colors.HexColor("#00ff88")
HEADER_BG  = colors.HexColor("#161b22")
ROW_ALT    = colors.HexColor("#1c2333")
WHITE      = colors.white
GRAY       = colors.HexColor("#8b949e")
RED        = colors.HexColor("#ff4444")
GREEN      = colors.HexColor("#00ff88")
YELLOW     = colors.HexColor("#ffd700")


def _make_styles():
    base = getSampleStyleSheet()
    styles = {}

    styles["title"] = ParagraphStyle(
        "title", parent=base["Title"],
        fontName="Helvetica-Bold", fontSize=22,
        textColor=ACCENT, alignment=TA_CENTER, spaceAfter=6,
    )
    styles["subtitle"] = ParagraphStyle(
        "subtitle", parent=base["Normal"],
        fontName="Helvetica", fontSize=11,
        textColor=GRAY, alignment=TA_CENTER, spaceAfter=4,
    )
    styles["section"] = ParagraphStyle(
        "section", parent=base["Heading2"],
        fontName="Helvetica-Bold", fontSize=13,
        textColor=ACCENT, spaceBefore=14, spaceAfter=6,
    )
    styles["body"] = ParagraphStyle(
        "body", parent=base["Normal"],
        fontName="Helvetica", fontSize=9,
        textColor=WHITE, spaceAfter=4,
    )
    styles["small"] = ParagraphStyle(
        "small", parent=base["Normal"],
        fontName="Helvetica", fontSize=8,
        textColor=GRAY,
    )
    return styles


def _tbl_style(header_rows=1):
    cmds = [
        ("BACKGROUND",  (0, 0), (-1, header_rows - 1), HEADER_BG),
        ("TEXTCOLOR",   (0, 0), (-1, header_rows - 1), ACCENT),
        ("FONTNAME",    (0, 0), (-1, header_rows - 1), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, header_rows - 1), 8),
        ("BACKGROUND",  (0, header_rows), (-1, -1), DARK_BG),
        ("TEXTCOLOR",   (0, header_rows), (-1, -1), WHITE),
        ("FONTNAME",    (0, header_rows), (-1, -1), "Helvetica"),
        ("FONTSIZE",    (0, header_rows), (-1, -1), 7.5),
        ("ROWBACKGROUNDS", (0, header_rows), (-1, -1), [DARK_BG, ROW_ALT]),
        ("GRID",        (0, 0), (-1, -1), 0.3, colors.HexColor("#30363d")),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",  (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]
    return TableStyle(cmds)


def generate_case_report(case, evidence_list, custody_records, output_dir: str) -> str:
    """
    Generate a full forensics PDF report for the given case.
    Returns the absolute path to the generated file.
    """
    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"DFEMS_Report_{case.case_number}_{ts}.pdf"
    filepath = os.path.join(output_dir, filename)

    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=f"DFEMS – {case.case_number}",
        author="Digital Forensics Evidence Management System",
    )

    styles = _make_styles()
    story  = []

    # ── Cover header ──────────────────────────────────────────────────────
    story.append(Paragraph("DIGITAL FORENSICS EVIDENCE MANAGEMENT SYSTEM", styles["title"]))
    story.append(Paragraph("Confidential Forensic Investigation Report", styles["subtitle"]))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=12))

    # ── Case details ──────────────────────────────────────────────────────
    story.append(Paragraph("Case Details", styles["section"]))
    case_data = [
        ["Case Number",  case.case_number,         "Status",   case.status],
        ["Title",        case.title,                "Priority", case.priority],
        ["Created",      case.created_at.strftime("%Y-%m-%d %H:%M UTC"),
         "Updated",      case.updated_at.strftime("%Y-%m-%d %H:%M UTC")],
        ["Description",  Paragraph(case.description or "—", styles["body"]), "", ""],
    ]
    tbl = Table(case_data, colWidths=[3.5 * cm, 7.5 * cm, 3 * cm, 4 * cm])
    tbl.setStyle(_tbl_style(0))
    story.append(tbl)
    story.append(Spacer(1, 10))

    # ── Evidence inventory ─────────────────────────────────────────────────
    story.append(Paragraph(f"Evidence Inventory ({len(evidence_list)} items)", styles["section"]))
    ev_header = ["Evidence ID", "Filename", "Size", "Type", "Status", "Uploaded"]
    ev_rows   = [ev_header]
    for ev in evidence_list:
        size_str = _human_size(ev.file_size)
        status_color = GREEN if ev.integrity_status == "Verified" else (
                       RED if ev.integrity_status == "Tampered" else YELLOW)
        ev_rows.append([
            ev.evidence_id,
            Paragraph(ev.original_name[:40], styles["small"]),
            size_str,
            ev.file_type or "—",
            Paragraph(f'<font color="#{_hex(status_color)}">{ev.integrity_status}</font>',
                      styles["small"]),
            ev.uploaded_at.strftime("%Y-%m-%d"),
        ])
    ev_tbl = Table(ev_rows, colWidths=[3 * cm, 6 * cm, 2 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm])
    ev_tbl.setStyle(_tbl_style(1))
    story.append(ev_tbl)
    story.append(Spacer(1, 10))

    # ── Hash values ────────────────────────────────────────────────────────
    story.append(Paragraph("Cryptographic Hash Values", styles["section"]))
    hash_header = ["Evidence ID", "Filename", "SHA-256", "MD5"]
    hash_rows   = [hash_header]
    for ev in evidence_list:
        hash_rows.append([
            ev.evidence_id,
            Paragraph(ev.original_name[:35], styles["small"]),
            Paragraph(f'<font size="6">{ev.sha256_hash}</font>', styles["small"]),
            Paragraph(f'<font size="6">{ev.md5_hash}</font>',    styles["small"]),
        ])
    hash_tbl = Table(hash_rows, colWidths=[3 * cm, 4.5 * cm, 8 * cm, 3 * cm])
    hash_tbl.setStyle(_tbl_style(1))
    story.append(hash_tbl)
    story.append(Spacer(1, 10))

    # ── Chain of custody ──────────────────────────────────────────────────
    story.append(Paragraph("Chain of Custody Timeline", styles["section"]))
    coc_header = ["#", "Timestamp", "Action", "Actor", "Evidence", "Notes"]
    coc_rows   = [coc_header]
    for i, rec in enumerate(custody_records, 1):
        actor = rec.actor.username if rec.actor else "—"
        ev_ref = rec.evidence.evidence_id if rec.evidence else "—"
        coc_rows.append([
            str(i),
            rec.timestamp.strftime("%Y-%m-%d %H:%M"),
            rec.action,
            actor,
            ev_ref,
            Paragraph(rec.notes or "", styles["small"]),
        ])
    coc_tbl = Table(coc_rows, colWidths=[0.8 * cm, 3.5 * cm, 4 * cm, 2.5 * cm, 2.5 * cm, 5.2 * cm])
    coc_tbl.setStyle(_tbl_style(1))
    story.append(coc_tbl)

    # ── Footer ────────────────────────────────────────────────────────────
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRAY))
    story.append(Paragraph(
        f"Generated by DFEMS on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC  |  CONFIDENTIAL",
        styles["small"],
    ))

    doc.build(story)
    logger.info("Report generated: %s", filepath)
    return filename, filepath


def _human_size(size_bytes: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def _hex(color) -> str:
    """Convert reportlab color to 6-char hex string."""
    r = int(color.red * 255)
    g = int(color.green * 255)
    b = int(color.blue * 255)
    return f"{r:02x}{g:02x}{b:02x}"
