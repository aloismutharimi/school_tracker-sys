from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)

from storage import load_json, REPORTS_DIR
from tracker import get_student
from report import (
    build_finance_table, build_performance_table,
    build_student_scores, get_student_rank,
)

# --- Styles ---
STYLES = getSampleStyleSheet()
TITLE = ParagraphStyle(
    "Title", parent=STYLES["Heading1"],
    fontSize=18, spaceAfter=4, textColor=colors.HexColor("#0b1a2e"),
)
SUBTITLE = ParagraphStyle(
    "Subtitle", parent=STYLES["Normal"],
    fontSize=11, textColor=colors.HexColor("#64748b"), spaceAfter=12,
)
SECTION = ParagraphStyle(
    "Section", parent=STYLES["Heading2"],
    fontSize=13, spaceBefore=14, spaceAfter=8,
    textColor=colors.HexColor("#0b1a2e"),
)
CLASS_HEADER = ParagraphStyle(
    "ClassHeader", parent=STYLES["Heading2"],
    fontSize=14, spaceBefore=16, spaceAfter=8,
    textColor=colors.white, backColor=colors.HexColor("#0b1a2e"),
    borderPadding=6, leftIndent=0,
)
BODY = ParagraphStyle(
    "Body", parent=STYLES["Normal"],
    fontSize=10, spaceAfter=6,
)


def _table(data, col_widths=None, header=True):
    """Build a styled ReportLab table."""
    t = Table(data, colWidths=col_widths, hAlign="LEFT")
    style = [
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]
    if header:
        style += [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor("#94a3b8")),
        ]
    style += [
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#f8fafc")]),
        ("LINEBELOW", (0, 1), (-1, -2), 0.25, colors.HexColor("#e2e8f0")),
    ]
    t.setStyle(TableStyle(style))
    return t


def _finance_table(term, students):
    df = build_finance_table(term, students)
    if df.empty:
        return None
    data = [["Student Name", "Class", "Due", "Paid", "Balance", "Status"]]
    for _, r in df.iterrows():
        status = "ARREARS" if r["in_arrears"] else "CLEARED"
        data.append([
            r["name"], r["class"],
            f"{r['due']:,.0f}", f"{r['paid']:,.0f}",
            f"{r['balance']:,.0f}", status,
        ])
    return _table(data, col_widths=[130, 55, 65, 65, 65, 60])


def _perf_table(term, students):
    df = build_performance_table(term, students)
    if df.empty:
        return None
    data = [["Rank", "Student Name", "Class", "Average"]]
    for _, r in df.iterrows():
        data.append([f"#{r['rank']}", r["name"], r["class"], f"{r['average']:.1f}%"])
    return _table(data, col_widths=[45, 180, 70, 75])


def _summary_block(finance_df, perf_df=None, title="SUMMARY"):
    """Return a list of flowables for a summary section."""
    flow = [Paragraph(title, SECTION)]
    if finance_df is None or finance_df.empty:
        return flow
    total_due = finance_df["due"].sum()
    total_paid = finance_df["paid"].sum()
    total_bal = finance_df["balance"].sum()
    arrears = int(finance_df["in_arrears"].sum())

    rows = [
        ["Total billed:", f"{total_due:,.0f}"],
        ["Total collected:", f"{total_paid:,.0f}"],
        ["Outstanding:", f"{total_bal:,.0f}"],
        ["In arrears:", f"{arrears}/{len(finance_df)} students"],
    ]
    if perf_df is not None and not perf_df.empty:
        rows.append(["Class average:", f"{perf_df['average'].mean():.1f}%"])
        top = perf_df.iloc[0]
        rows.append(["Top performer:", f"{top['name']} ({top['average']:.1f}%)"])

    t = Table(rows, colWidths=[130, 200], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
    ]))
    flow.append(t)
    return flow

def _build_full_doc(story, term, mode):
    """Full school report, broken down by class."""
    students = load_json("students.json")
    groups = {}
    for s in students:
        groups.setdefault(s["class"], []).append(s)
    groups = dict(sorted(groups.items()))

    all_finance = []

    for class_name, class_students in groups.items():
        story.append(Paragraph(f"{class_name.upper()}", CLASS_HEADER))
        story.append(Spacer(1, 6))

        finance_df = None
        perf_df = None

        if mode in ("fees", "full"):
            finance_df = build_finance_table(term, class_students)
            story.append(Paragraph("Fees &amp; Balances", SECTION))
            t = _finance_table(term, class_students)
            if t: story.append(t)
            else: story.append(Paragraph("No fee data.", BODY))

        if mode in ("grades", "full"):
            perf_df = build_performance_table(term, class_students)
            story.append(Paragraph("Performance Ranking", SECTION))
            t = _perf_table(term, class_students)
            if t: story.append(t)
            else: story.append(Paragraph("No scores recorded.", BODY))

        if mode == "full":
            story.extend(_summary_block(finance_df, perf_df, "Class Summary"))

        if finance_df is not None and not finance_df.empty:
            all_finance.append(finance_df)

        story.append(PageBreak())

    # School summary
    if mode == "full" and all_finance:
        import pandas as pd
        combined = pd.concat(all_finance, ignore_index=True)
        story.append(Paragraph("SCHOOL SUMMARY", CLASS_HEADER))
        story.append(Spacer(1, 6))
        story.extend(_summary_block(combined, None, "Totals"))


def _build_class_doc(story, term, class_name, mode):
    students = [s for s in load_json("students.json") if s["class"] == class_name]
    if not students:
        story.append(Paragraph(f"No students in {class_name}.", BODY))
        return

    finance_df = None
    perf_df = None

    if mode in ("fees", "full"):
        finance_df = build_finance_table(term, students)
        story.append(Paragraph("Fees &amp; Balances", SECTION))
        t = _finance_table(term, students)
        if t: story.append(t)

    if mode in ("grades", "full"):
        perf_df = build_performance_table(term, students)
        story.append(Paragraph("Performance Ranking", SECTION))
        t = _perf_table(term, students)
        if t: story.append(t)

    if mode == "full":
        story.extend(_summary_block(finance_df, perf_df, "Class Summary"))


def _build_student_doc(story, term, student_id, mode):
    student = get_student(student_id)
    if not student:
        story.append(Paragraph(f"Unknown student {student_id}.", BODY))
        return

    story.append(Paragraph(f"{student['name']} · {student['class']}", SUBTITLE))

    finance_df = None
    if mode in ("fees", "full"):
        finance_df = build_finance_table(term, [student])
        story.append(Paragraph("Fees &amp; Balances", SECTION))
        t = _finance_table(term, [student])
        if t: story.append(t)

    if mode in ("grades", "full"):
        rank, total = get_student_rank(student_id, term)
        story.append(Paragraph("Performance", SECTION))

        perf_df = build_performance_table(term, [student])
        if not perf_df.empty:
            avg = perf_df.iloc[0]["average"]
            if rank:
                story.append(Paragraph(f"Rank in class: <b>#{rank} of {total}</b>", BODY))
            story.append(Paragraph(f"Class average: <b>{avg:.1f}%</b>", BODY))
        else:
            story.append(Paragraph("No scores recorded this term.", BODY))

        story.append(Paragraph("Subject Breakdown", SECTION))
        subjects = build_student_scores(student_id, term)
        if subjects.empty:
            story.append(Paragraph("No scores recorded.", BODY))
        else:
            data = [["Subject", "Score", "Percentage"]]
            for _, r in subjects.iterrows():
                data.append([
                    r["subject"],
                    f"{r['score']:.0f}/{r['out_of']:.0f}",
                    f"{r['pct']:.1f}%",
                ])
            story.append(_table(data, col_widths=[180, 90, 100]))

def export_pdf(term, mode="full", class_filter=None, student_id=None):
    """Generate a PDF report. Returns the path."""
    REPORTS_DIR.mkdir(exist_ok=True)

    parts = [term]
    if student_id:
        parts.append(student_id)
    elif class_filter:
        parts.append(class_filter.replace(" ", "-"))
    parts.append(mode)
    filename = "-".join(parts) + ".pdf"
    path = REPORTS_DIR / filename

    doc = SimpleDocTemplate(
        str(path), pagesize=A4,
        leftMargin=18*mm, rightMargin=18*mm,
        topMargin=18*mm, bottomMargin=18*mm,
        title=f"Term Report — {term}",
    )

    story = []

    # Header
    if student_id:
        s = get_student(student_id)
        heading = f"Student Report — {s['name']}"
    elif class_filter:
        heading = f"Class Report — {class_filter}"
    else:
        heading = "Term Report"
    story.append(Paragraph(f"{heading} · {term}", TITLE))
    story.append(Paragraph("School Fees &amp; Results Tracker", SUBTITLE))

    if student_id:
        _build_student_doc(story, term, student_id, mode)
    elif class_filter:
        _build_class_doc(story, term, class_filter, mode)
    else:
        _build_full_doc(story, term, mode)

    doc.build(story)
    return path