"""FastAPI control plane used by the real CinemaOS dashboard."""

from __future__ import annotations

import csv
import io
import re
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.config import CampaignCreate, LocationModel, NICHES, settings
from backend.database import (
    campaign_export_rows, create_campaign, dashboard_stats, get_campaign, init_db,
    list_campaign_logs, list_campaigns, list_leads, list_scrape_jobs,
    purge_expired_source_snapshots, update_campaign,
)
from backend.orchestrator import CampaignRunner

ROOT = Path(__file__).resolve().parent
BUILDS = ROOT / "builds"
LOCATIONS_FILE = ROOT / "data" / "india_locations.csv"


def load_india_locations() -> List[LocationModel]:
    with LOCATIONS_FILE.open(encoding="utf-8", newline="") as handle:
        return [LocationModel(**row) for row in csv.DictReader(handle)]


class IndiaCampaignRequest(BaseModel):
    name: str = Field(default="India OPC Campaign", min_length=3, max_length=160)
    niches: List[str] = Field(default_factory=lambda: list(NICHES))
    provider: str = "google_places"
    results_per_query: int = Field(default=10, ge=1, le=60)
    analyse_businesses: bool = False
    generate_sites: bool = False
    prepare_outreach: bool = False
    outreach_approved: bool = False


@asynccontextmanager
async def lifespan(_: FastAPI):
    BUILDS.mkdir(parents=True, exist_ok=True)
    await init_db()
    await purge_expired_source_snapshots()
    yield


app = FastAPI(title="CinemaOS OPC API", version="3.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=False, allow_methods=["GET", "POST"], allow_headers=["*"])
app.mount("/previews", StaticFiles(directory=BUILDS, html=True), name="previews")


async def run_campaign_job(campaign_id: str) -> None:
    await CampaignRunner().run(campaign_id)


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "3.0.0", "model": settings.openai_model, "openai_configured": bool(settings.openai_api_key), "google_places_configured": bool(settings.google_places_api_key), "outreach_mode": settings.outreach_mode}


@app.get("/api/config")
async def public_config():
    return {
        "niches": list(NICHES),
        "niche_keywords": {name: niche.search_terms for name, niche in NICHES.items()},
        "total_keywords": sum(len(niche.search_terms) for niche in NICHES.values()),
        "india_location_count": len(load_india_locations()),
        "model": settings.openai_model, "max_campaign_tasks": settings.max_campaign_tasks,
        "max_results_per_query": settings.max_results_per_query,
        "outreach_mode": settings.outreach_mode,
    }


@app.get("/api/locations")
async def locations():
    return [item.model_dump() | {"label": item.label} for item in load_india_locations()]


@app.get("/api/stats")
async def stats():
    return await dashboard_stats()


@app.get("/api/leads")
async def leads(limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0)):
    return await list_leads(limit, offset)


@app.get("/api/campaigns")
async def campaigns(limit: int = Query(50, ge=1, le=200)):
    return await list_campaigns(limit)


@app.post("/api/campaigns", status_code=201)
async def new_campaign(payload: CampaignCreate):
    try:
        campaign_id = await create_campaign(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return await get_campaign(campaign_id)


@app.post("/api/campaigns/india", status_code=201)
async def new_india_campaign(payload: IndiaCampaignRequest):
    try:
        campaign = CampaignCreate(name=payload.name, niches=payload.niches, locations=load_india_locations(), provider=payload.provider, results_per_query=payload.results_per_query, analyse_businesses=payload.analyse_businesses, generate_sites=payload.generate_sites, prepare_outreach=payload.prepare_outreach, outreach_approved=payload.outreach_approved)
        campaign_id = await create_campaign(campaign)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return await get_campaign(campaign_id)


@app.get("/api/campaigns/{campaign_id}")
async def campaign_detail(campaign_id: str):
    campaign = await get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@app.get("/api/campaigns/{campaign_id}/logs")
async def campaign_logs(campaign_id: str):
    if not await get_campaign(campaign_id):
        raise HTTPException(status_code=404, detail="Campaign not found")
    return await list_campaign_logs(campaign_id)


@app.get("/api/campaigns/{campaign_id}/jobs")
async def campaign_jobs(campaign_id: str):
    if not await get_campaign(campaign_id):
        raise HTTPException(status_code=404, detail="Campaign not found")
    return await list_scrape_jobs(campaign_id)


@app.get("/api/campaigns/{campaign_id}/export.csv")
async def export_campaign_csv(campaign_id: str):
    campaign = await get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    rows = await campaign_export_rows(campaign_id)
    columns = [
        "Business Name", "Category", "Phone", "Email", "Website", "Address", "Rating",
        "Reviews", "City", "State", "Country", "Found Via Keyword", "Google Maps Link",
        "Source", "Status", "Data Quality Score",
    ]
    stream = io.StringIO()
    stream.write("\ufeff")
    writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    safe_name = re.sub(r"[^A-Za-z0-9_-]+", "-", campaign["name"]).strip("-") or "campaign"
    return StreamingResponse(
        iter([stream.getvalue()]), media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}.csv"'},
    )


@app.post("/api/campaigns/{campaign_id}/run", status_code=202)
async def run_campaign(campaign_id: str, background_tasks: BackgroundTasks):
    campaign = await get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if campaign["status"] in {"running", "starting"}:
        return campaign
    await update_campaign(campaign_id, status="starting", stop_requested=False)
    background_tasks.add_task(run_campaign_job, campaign_id)
    return {**campaign, "status": "starting"}


@app.post("/api/campaigns/{campaign_id}/pause", status_code=202)
async def pause_campaign(campaign_id: str):
    if not await get_campaign(campaign_id):
        raise HTTPException(status_code=404, detail="Campaign not found")
    await update_campaign(campaign_id, stop_requested=True)
    return {"status": "pause_requested"}
