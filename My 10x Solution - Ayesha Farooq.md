# My 10x Solution — Ayesha Farooq

## 1. What is the problem I am solving?

I track scholarship applications (Türkiye Bursları and others, including
Master's/PhD funding targets) in a spreadsheet. Every week I have to
manually re-read every row to catch two things: applications that have
been sitting at "Applied" for 14+ days with no response, and deadlines
that have crept inside the next 21 days. Rows with missing status or
dates get silently skipped instead of flagged. This works, but it does
not scale past a handful of applications, and it is easy to miss
something on a busy week.

## 2. How did I implement my solution?

A small FastAPI service backed by SQLite. Every application (university,
scholarship, status, applied date, deadline, notes) is a row in the
database, managed through a CRUD API.

A background job (APScheduler) runs once a day, off the request path,
and logs a flag count so the state of things is visible without me
having to call the API.

The core logic — the same three-part rule I used to apply by hand — is
`GET /review`: it splits every non-rejected application into **follow
up now** (Applied, 14+ days, no response), **deadlines this month**
(within 21 days), and **needs my input** (missing status or date).
Rejected applications never appear. Since this computation gets called
repeatedly, the result is cached for 5 minutes instead of being
recomputed on every call.

That same review can be downloaded as a PDF (`GET /review/pdf`) —
useful for a quick weekly read without opening the API docs.

Finally, `POST /applications/extract` takes a raw pasted scholarship
description and uses an LLM (OpenRouter) to pull out the deadline and
a one-line eligibility summary, writing it onto the matching row. Token
usage is logged to `llm_costs.log` for every call.

**Concepts implemented (6, 0 swaps):** API endpoints, database,
background/cron job, PDF reporting, caching, LLM integration.

**Steps to run:**
```bash
pip install -r requirements.txt
python seed.py && uvicorn main:app --reload
```
Then visit `http://localhost:8000/docs`. Full demo path is in the README.
