"""Seed script — insert demo data so a stranger can see the system work."""
from datetime import date, timedelta
from database import init_db, SessionLocal, Application

init_db()
db = SessionLocal()

today = date.today()

demo = [
    Application(
        university="Bogazici University",
        scholarship_name="Turkiye Burslari",
        status="Applied",
        applied_date=today - timedelta(days=21),
        deadline=today + timedelta(days=17),
        notes="Submitted via portal, no confirmation email yet",
    ),
    Application(
        university="TU Munich",
        scholarship_name="DAAD PhD Scholarship",
        status="Rejected",
        applied_date=today - timedelta(days=40),
        deadline=today - timedelta(days=10),
    ),
    Application(
        university="ETH Zurich",
        scholarship_name="Excellence Scholarship",
        status="Applied",
        applied_date=today - timedelta(days=3),
        deadline=today + timedelta(days=60),
        notes="Recently submitted, too early to follow up",
    ),
    Application(
        university="METU",
        scholarship_name="METU International Scholarship",
        status="",  # deliberately incomplete -> needs input
    ),
]

db.add_all(demo)
db.commit()
db.close()
print(f"Seeded {len(demo)} applications into scholarships.db")
