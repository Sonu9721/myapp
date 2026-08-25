# CinemaOS AI OPC Engine

CinemaOS is a controlled automation system for a one-person B2B service company. It discovers businesses location by location, analyses public evidence with GPT-5.6 Sol, creates private concept pages, prepares respectful outreach drafts, and records every step in a resumable campaign database.

## What changed in version 3

- Real FastAPI backend and React dashboard integration; no timer-based fake campaign.
- OpenAI Responses API with `gpt-5.6-sol` replaces Gemini and Groq.
- Official Google Places Text Search (New) replaces Google-page scraping and fabricated contacts.
- Each location × niche × keyword is a persistent task with retry, pause and resume checkpoints.
- The scraper now checkpoints every **location × niche × keyword** job, so a failed keyword resumes without repeating a whole city.
- All configured niches can be selected together; each niche uses its own keyword set one by one.
- Google Place IDs deduplicate businesses across campaigns.
- Every keyword/location match is retained as discovery history even when the business is deduplicated.
- Indian phone numbers are conservatively normalized and unusable short values are rejected.
- Each campaign downloads as an Excel-compatible CSV with name, category, contact details, address, rating, reviews, city/state, source keyword, Maps link and data-quality score.
- Public business websites can be checked for a published email; private-network URLs are blocked.
- Generated pages are sanitized and served locally from `/previews`.
- Outreach is draft-first, capped, checked against a do-not-contact table, and requires both server and campaign approval.
- API keys live only in the backend `.env`, never in browser state.

## The business workflow

1. Start with one niche in one city using mock mode and scrape-only settings.
2. Review the business records, keyword coverage and CSV export.
3. Configure OpenAI and Google Places keys.
4. Run a small Google Places campaign (5–10 results).
5. Enable GPT analysis, concept pages or draft preparation only after the data looks correct.
6. Verify contact data and offers manually.
7. Only after validation, enable approved outreach with a low cap.
8. Expand city by city, then use the 36-location India starter queue.

The India queue contains one representative city for each state and union territory. Add rows to `backend/data/india_locations.csv` or paste any city list in the dashboard for deeper coverage. Google Text Search has per-query result limits, quotas and field-based billing, so no responsible system can retrieve “every Indian business” in one request. The machine provides repeatable coverage of the locations and keywords you give it.

## All-niche scraper machine

In the dashboard, open **Campaigns**, click **Select all niches**, paste locations one per line, keep the AI/site/outreach switches off, and run a mock pilot. The job estimate shows the exact number of resumable keyword searches before you start. Switch the provider to Google Places only after adding the API key and reviewing expected billing.

The machine runs in this order:

```text
Location 1 -> Niche 1 -> Keyword 1, Keyword 2, ...
           -> Niche 2 -> Keyword 1, Keyword 2, ...
Location 2 -> repeat
```

Each job retries transient failures up to three times. Place IDs remove duplicates, while the export combines all keywords that found the same business. Download the finished or partial file with **Download CSV**; it opens directly in Excel.

## Setup on Windows

```powershell
cd C:\Users\user\Desktop\myapp
.\setup.ps1
```

Open `.env` and add:

```dotenv
OPENAI_API_KEY=...
GOOGLE_PLACES_API_KEY=...
```

Start both services and open the dashboard:

```powershell
.\start-all.ps1
```

When finished, run `.\stop-all.ps1`. The separate `start-backend.ps1` and `start-frontend.ps1` scripts are also available for development.

Dashboard: `http://localhost:3000`

API documentation: `http://127.0.0.1:8000/docs`

## Safe mock campaign from the command line

```powershell
.\.venv\Scripts\python.exe -m backend.orchestrator --provider mock --niche "Real Estate" --city "Noida" --state "Uttar Pradesh" --limit 2
```

Use `--all-niches` to process every configured business type and every niche keyword one by one. By default this is scrape-only. Use `--provider google_places` only after adding the Places API key.

## Outreach controls

Sending is disabled unless all conditions are true:

1. `.env` contains `OUTREACH_MODE=approved`.
2. The individual campaign has `outreach_approved=true`.
3. A real email or phone was found.
4. The recipient is not on the do-not-contact list.
5. `MAX_OUTREACH_PER_RUN` has not been reached.

Keep draft-only mode until you have reviewed applicable consent, anti-spam, WhatsApp, Google Places and privacy requirements. Never treat guessed contact data as verified.

## Production path

The local background runner is suitable for a controlled OPC pilot. Before unattended cloud operation, add PostgreSQL, a durable worker queue, authentication/roles, encrypted secrets, scheduled source-data deletion, monitoring, backups, domain/email reputation management, and legal review for each outreach channel.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests
cd frontend
npm run build
```
