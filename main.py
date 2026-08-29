"""
Scholarship Application Tracker + Deadline Alert System
FlyRank Capstone — Your 10x Solution

Concepts implemented (6, 0 swaps):
1. API endpoints      -> this file, CRUD + review + extract
2. Database            -> database.py (SQLite, survives restart)
3. Background/cron job -> jobs.py (APScheduler, daily flag check)
4. Reporting (PDF)      -> reporting.py (weekly summary PDF)
5. Caching logic        -> review endpoint caches its (expensive) computed
                           result for CACHE_TTL_SECONDS instead of recomputing
6. LLM integration       -> /applications/extract (OpenRouter, cost-logged)
"""
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
from typing import List
import time

from database import init_db, get_db, Application
from schemas import ApplicationCreate, ApplicationUpdate, ApplicationOut, ExtractRequest
from jobs import start_scheduler
from reporting import generate_weekly_pdf
from llm import extract_deadline_and_eligibility

app = FastAPI(title="Scholarship Application Tracker", version="1.0.0")

# ---- simple in-memory cache for the review summary (Concept 6: Caching) ----
_review_cache = {"data": None, "computed_at": 0}
CACHE_TTL_SECONDS = 300  # 5 minutes


@app.on_event("startup")
def on_startup():
    init_db()
    start_scheduler()


# ---------------------------------------------------------------- CRUD ----
@app.post("/applications", response_model=ApplicationOut, status_code=201)
def create_application(payload: ApplicationCreate, db: Session = Depends(get_db)):
    app_row = Application(**payload.model_dump())
    db.add(app_row)
    db.commit()
    db.refresh(app_row)
    _invalidate_cache()
    return app_row


@app.get("/applications", response_model=List[ApplicationOut])
def list_applications(db: Session = Depends(get_db)):
    return db.query(Application).order_by(Application.deadline.asc().nullslast()).all()


@app.get("/applications/{app_id}", response_model=ApplicationOut)
def get_application(app_id: int, db: Session = Depends(get_db)):
    row = db.query(Application).filter(Application.id == app_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Application not found")
    return row


@app.patch("/applications/{app_id}", response_model=ApplicationOut)
def update_application(app_id: int, payload: ApplicationUpdate, db: Session = Depends(get_db)):
    row = db.query(Application).filter(Application.id == app_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Application not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    db.commit()
    db.refresh(row)
    _invalidate_cache()
    return row


@app.delete("/applications/{app_id}", status_code=204)
def delete_application(app_id: int, db: Session = Depends(get_db)):
    row = db.query(Application).filter(Application.id == app_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Application not found")
    db.delete(row)
    db.commit()
    _invalidate_cache()
    return None


# ------------------------------------------------------- REVIEW SUMMARY ----
def _invalidate_cache():
    _review_cache["data"] = None
    _review_cache["computed_at"] = 0


def _compute_review(db: Session) -> dict:
    today = date.today()
    rows = db.query(Application).all()

    follow_up, deadlines, needs_input = [], [], []

    for r in rows:
        if r.status == "Rejected":
            continue

        if not r.status or not (r.applied_date or r.deadline):
            needs_input.append(_row_dict(r))
            continue

        if r.status == "Applied" and r.applied_date:
            days_since = (today - r.applied_date).days
            if days_since >= 14:
                needs_input_entry = _row_dict(r)
                needs_input_entry["days_since_applied"] = days_since
                follow_up.append(needs_input_entry)

        if r.deadline:
            days_to_deadline = (r.deadline - today).days
            if 0 <= days_to_deadline <= 21:
                d = _row_dict(r)
                d["days_to_deadline"] = days_to_deadline
                deadlines.append(d)

    return {
        "generated_at": datetime.utcnow().isoformat(),
        "follow_up_now": follow_up,
        "deadlines_this_month": deadlines,
        "needs_my_input": needs_input,
    }


def _row_dict(r: Application) -> dict:
    return {
        "id": r.id,
        "university": r.university,
        "scholarship_name": r.scholarship_name,
        "status": r.status,
        "applied_date": str(r.applied_date) if r.applied_date else None,
        "deadline": str(r.deadline) if r.deadline else None,
    }


@app.get("/review")
def get_review(db: Session = Depends(get_db)):
    """The expensive-to-compute weekly review. Cached (Concept 6)."""
    now = time.time()
    if _review_cache["data"] and (now - _review_cache["computed_at"]) < CACHE_TTL_SECONDS:
        result = dict(_review_cache["data"])
        result["cache_hit"] = True
        return result

    result = _compute_review(db)
    _review_cache["data"] = result
    _review_cache["computed_at"] = now
    result = dict(result)
    result["cache_hit"] = False
    return result


# --------------------------------------------------------- PDF REPORT -----
@app.get("/review/pdf")
def get_review_pdf(db: Session = Depends(get_db)):
    """Generates the weekly review as a downloadable PDF (Concept 4)."""
    review = _compute_review(db)
    pdf_path = generate_weekly_pdf(review)
    from fastapi.responses import FileResponse
    return FileResponse(pdf_path, media_type="application/pdf", filename="weekly_review.pdf")


# --------------------------------------------------------- LLM EXTRACT ----
@app.post("/applications/extract")
def extract_from_text(payload: ExtractRequest, db: Session = Depends(get_db)):
    """
    Concept 6: LLM integration.
    Paste a raw scholarship description -> LLM extracts deadline + eligibility
    -> writes it onto the matching application row. Cost is logged to llm_costs.log.
    """
    row = db.query(Application).filter(Application.id == payload.application_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Application not found")

    extracted = extract_deadline_and_eligibility(payload.raw_text)

    if extracted.get("deadline"):
        try:
            row.deadline = date.fromisoformat(extracted["deadline"])
        except ValueError:
            pass
    if extracted.get("eligibility"):
        row.eligibility = extracted["eligibility"]

    db.commit()
    db.refresh(row)
    _invalidate_cache()
    return {"application": ApplicationOut.model_validate(row), "llm_raw": extracted}


@app.get("/health")
def health():
    return {"status": "ok"}
