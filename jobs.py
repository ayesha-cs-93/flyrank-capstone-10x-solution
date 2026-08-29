"""
Background / cron job (Concept 3).
Runs once a day (and once at startup for demo purposes) to recompute
the review and log anything that needs attention to daily_flags.log —
work that happens off the request path, on a schedule.
"""
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

_scheduler = BackgroundScheduler()


def _daily_flag_check():
    from database import SessionLocal
    from main import _compute_review  # local import avoids circular import at module load

    db = SessionLocal()
    try:
        review = _compute_review(db)
        with open("daily_flags.log", "a") as f:
            f.write(
                f"[{datetime.utcnow().isoformat()}] "
                f"follow_up={len(review['follow_up_now'])} "
                f"deadlines={len(review['deadlines_this_month'])} "
                f"needs_input={len(review['needs_my_input'])}\n"
            )
    finally:
        db.close()


def start_scheduler():
    if not _scheduler.running:
        _scheduler.add_job(_daily_flag_check, "interval", hours=24, next_run_time=datetime.now())
        _scheduler.start()
