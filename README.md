# Scholarship Application Tracker + Deadline Alert System

**The problem:** Tracking scholarship applications (Türkiye Bursları and others) in a
spreadsheet means manually re-reading every row every week to catch what needs
follow-up or is close to a deadline. It's easy to miss a 14-day-no-response
application or a deadline that's crept inside a 3-week window.

**The 10x claim:** Reviewing applications for what needs attention goes from a
manual spreadsheet read-through to one API call (or one PDF) that always has
the right three lists.

**Non-goal:** No UI. No auth (single user, personal tool). No outbound
messaging — this only reports what needs attention, it never contacts anyone.

## Concepts implemented (6, 0 swaps)

| # | Concept | Where it lives |
|---|---------|-----------------|
| 1 | API endpoints | `main.py` — CRUD for `/applications`, validated with Pydantic (`schemas.py`) |
| 2 | Database | `database.py` — SQLite via SQLAlchemy, survives restart |
| 3 | Background/cron job | `jobs.py` — APScheduler daily job, logs flags to `daily_flags.log` off the request path |
| 4 | Reporting (PDF) | `reporting.py` + `GET /review/pdf` — weekly review rendered as a PDF |
| 5 | Caching logic | `main.py` — `/review` caches its computed result for 5 minutes instead of recomputing on every call |
| 6 | LLM integration | `llm.py` + `POST /applications/extract` — pastes a scholarship description, extracts deadline + eligibility, cost logged to `llm_costs.log` |

## Run it (2 commands)

```bash
pip install -r requirements.txt
python seed.py && uvicorn main:app --reload
```

Server runs at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

Optional, for the LLM endpoint: `export OPENROUTER_API_KEY=your_key` before starting
the server. Without it, `/applications/extract` responds gracefully with
`"error": "OPENROUTER_API_KEY not set"` instead of crashing.

## 5-minute demo path

1. `python seed.py` — inserts 4 demo applications (one needs follow-up, one has
   a near deadline, one is rejected, one is missing a status).
2. Start the server, open `http://localhost:8000/docs`.
3. `GET /applications` — see all 4 rows.
4. `GET /review` — see the three-section summary:
   - `follow_up_now`: Boğaziçi (applied 21 days ago, no response)
   - `deadlines_this_month`: Boğaziçi (deadline in ~17 days)
   - `needs_my_input`: METU (missing status)
   - Note: TU Munich (Rejected) appears in **none** of the three lists.
5. Call `GET /review` again — `"cache_hit": true` in the response (Concept 5).
6. `GET /review/pdf` — downloads the same summary as a PDF.
7. `POST /applications/extract` with an `application_id` and pasted scholarship
   text — extracts a deadline/eligibility sentence via LLM (Concept 6).

## API endpoints

- `POST /applications` — create
- `GET /applications` — list all
- `GET /applications/{id}` — get one
- `PATCH /applications/{id}` — update
- `DELETE /applications/{id}` — delete
- `GET /review` — the three-section summary (cached)
- `GET /review/pdf` — same summary as a PDF
- `POST /applications/extract` — LLM deadline/eligibility extraction

## Future ideas (out of scope for this capstone)

- Outbound email/Slack nudges for follow-up items
- Multi-user auth
- Google Sheets sync
