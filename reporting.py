"""PDF reporting (Concept 4) — builds the weekly review as a PDF, no browser needed."""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from datetime import datetime


def generate_weekly_pdf(review: dict, path: str = "weekly_review.pdf") -> str:
    c = canvas.Canvas(path, pagesize=A4)
    width, height = A4
    y = height - 25 * mm

    def line(text, size=11, bold=False, gap=7 * mm):
        nonlocal y
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        c.drawString(20 * mm, y, text)
        y -= gap

    line("Weekly Scholarship Review", size=16, bold=True, gap=10 * mm)
    line(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", size=9, gap=10 * mm)

    def section(title, rows, empty_msg, formatter):
        nonlocal y
        line(title, size=13, bold=True)
        if not rows:
            line(f"  {empty_msg}", size=10)
        for r in rows:
            line(f"  - {formatter(r)}", size=10)
        y -= 5 * mm

    section(
        "1. Follow Up Now",
        review["follow_up_now"],
        "Nothing pending follow-up.",
        lambda r: f"{r['university']} — {r['scholarship_name']} ({r.get('days_since_applied','?')} days since applied)",
    )
    section(
        "2. Deadlines This Month",
        review["deadlines_this_month"],
        "No deadlines in the next 21 days.",
        lambda r: f"{r['university']} — {r['scholarship_name']} (deadline in {r.get('days_to_deadline','?')} days)",
    )
    section(
        "3. Needs Your Input",
        review["needs_my_input"],
        "Nothing missing status/date.",
        lambda r: f"{r['university']} — {r['scholarship_name']} (missing status or date)",
    )

    c.save()
    return path
