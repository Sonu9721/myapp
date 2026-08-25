"""Resumable location-by-location, niche-by-niche OPC campaign runner."""

from __future__ import annotations

import argparse
import asyncio
import logging
from typing import Any, Dict, List

from backend.ai import OpenAIStudioClient
from backend.config import CampaignCreate, DiscoveredLead, LeadModel, LocationModel, NICHES, settings
from backend.database import (
    add_campaign_log, attach_lead_to_campaign, create_campaign, find_lead_id_by_source,
    ensure_scrape_jobs, get_campaign, increment_campaign, init_db, list_scrape_jobs,
    next_scrape_job, purge_expired_source_snapshots,
    record_lead_discovery, save_enriched_profile, save_lead, save_lead_source,
    update_campaign, update_lead_status, update_scrape_job,
)
from backend.generator import ProgrammaticSiteGenerator
from backend.outreach import B2BOutreachEngine
from backend.researcher import BusinessAuditor
from backend.scraper import GooglePlacesLeadScraper, MockLeadScraper, WebsiteContactEnricher

logger = logging.getLogger("CampaignRunner")


class CampaignRunner:
    def __init__(self) -> None:
        self.ai = OpenAIStudioClient()
        self.auditor = BusinessAuditor(self.ai)
        self.generator = ProgrammaticSiteGenerator(self.ai)
        self.outreach = B2BOutreachEngine(self.ai)
        self.contacts = WebsiteContactEnricher()
        self.lead_semaphore = asyncio.Semaphore(max(1, settings.max_concurrent_leads))

    async def run(self, campaign_id: str) -> Dict[str, Any]:
        await init_db()
        await purge_expired_source_snapshots()
        campaign = await get_campaign(campaign_id)
        if not campaign:
            raise ValueError("Campaign not found")
        if campaign["status"] == "running":
            return campaign
        config = CampaignCreate.model_validate(campaign["configuration"])
        await ensure_scrape_jobs(campaign_id, config)
        if config.provider == "google_places" and not settings.google_places_api_key:
            await update_campaign(campaign_id, status="blocked", error_message="GOOGLE_PLACES_API_KEY is not configured")
            return (await get_campaign(campaign_id)) or {}

        await update_campaign(campaign_id, status="running", stop_requested=False, error_message=None)
        await add_campaign_log(
            campaign_id, "campaign",
            f"Started {config.provider} campaign: {config.scrape_job_count} keyword jobs, "
            f"{len(config.niches)} niches, {len(config.locations)} locations",
        )
        had_errors = False
        while True:
            current = await get_campaign(campaign_id)
            if not current or current["stop_requested"]:
                await update_campaign(campaign_id, status="paused")
                await add_campaign_log(campaign_id, "campaign", "Campaign paused at a safe checkpoint")
                break
            job = await next_scrape_job(campaign_id)
            if not job:
                failed_jobs = any(item["status"] == "failed" for item in await list_scrape_jobs(campaign_id))
                final_status = "completed_with_errors" if had_errors or failed_jobs else "completed"
                await update_campaign(campaign_id, status=final_status)
                await add_campaign_log(campaign_id, "campaign", f"Campaign {final_status.replace('_', ' ')}")
                break
            await update_scrape_job(job["id"], "running")
            await add_campaign_log(
                campaign_id, "discover",
                f"Searching '{job['keyword']}' for {job['niche']} in {job['location']}",
            )
            try:
                scraper = MockLeadScraper() if config.provider == "mock" else GooglePlacesLeadScraper()
                leads = await scraper.scrape(
                    job["niche"], job["location"], config.results_per_query, job["keyword"]
                )
                for lead in leads:
                    lead.found_via_keyword = job["keyword"]
                    lead.city, lead.state, lead.country = job["city"], job["state"], job["country"]
                fully_processed = await self._process_task(campaign_id, config, leads)
                if not fully_processed:
                    await update_scrape_job(
                        job["id"], "queued", result_count=len(leads),
                        attempt_count=job["attempt_count"], error_message=None,
                    )
                    continue
                await update_scrape_job(job["id"], "completed", result_count=len(leads), error_message=None)
                await increment_campaign(campaign_id, "completed_tasks")
                await add_campaign_log(
                    campaign_id, "discover",
                    f"Completed '{job['keyword']}' in {job['location']}: {len(leads)} raw matches",
                )
            except Exception as exc:  # isolate a failed location/category and keep checkpoints
                had_errors = True
                terminal_failure = job["attempt_count"] + 1 >= 3
                await update_scrape_job(job["id"], "failed", error_message=str(exc)[:2000])
                if terminal_failure:
                    await increment_campaign(campaign_id, "completed_tasks")
                retry_note = "no retries left" if terminal_failure else "will retry safely"
                await add_campaign_log(
                    campaign_id, "error",
                    f"Keyword job failed ({retry_note}): {type(exc).__name__}: {exc}", level="error",
                )
        return (await get_campaign(campaign_id)) or {}

    async def _process_task(self, campaign_id: str, config: CampaignCreate, leads: List[DiscoveredLead]) -> bool:
        for discovered in leads:
            current = await get_campaign(campaign_id)
            if not current or current["stop_requested"]:
                return False
            async with self.lead_semaphore:
                try:
                    await self._process_lead(campaign_id, config, discovered)
                except Exception as exc:
                    await add_campaign_log(campaign_id, "lead_error", f"{discovered.name}: {type(exc).__name__}: {exc}", discovered.id, "error")
                    await update_lead_status(discovered.id, "Failed")
        return True

    async def _process_lead(self, campaign_id: str, config: CampaignCreate, discovered: DiscoveredLead) -> None:
        existing_id = await find_lead_id_by_source(discovered.source, discovered.source_id)
        if existing_id:
            discovered.id = existing_id
        if not discovered.email and discovered.website:
            discovered.email = await self.contacts.find_public_email(discovered.website)

        source_payload = discovered.model_dump()
        source_payload["raw_snapshot"] = discovered.raw_snapshot
        await save_lead(discovered.model_dump(exclude={"source", "source_id", "formatted_address", "google_maps_uri", "primary_type", "business_status", "rating", "review_count", "raw_snapshot"}))
        await save_lead_source(discovered.id, source_payload)
        await record_lead_discovery(campaign_id, discovered.id, source_payload)
        is_new_for_campaign = await attach_lead_to_campaign(campaign_id, discovered.id)
        if not is_new_for_campaign:
            await add_campaign_log(
                campaign_id, "dedupe",
                f"Reused {discovered.name}; already found by another keyword", discovered.id,
            )
            return
        await increment_campaign(campaign_id, "leads_processed")
        if not config.analyse_businesses:
            await update_lead_status(discovered.id, "Scraped")
            return
        await update_lead_status(discovered.id, "Researching")
        await add_campaign_log(campaign_id, "research", f"Analyzing {discovered.name}", discovered.id)

        lead = LeadModel(**discovered.model_dump(include={"id", "name", "phone", "email", "website", "niche", "location", "status"}))
        profile = await self.auditor.audit_single_business(lead)
        await save_enriched_profile(profile.model_dump())
        await update_lead_status(lead.id, "Analyzed")

        preview_url = ""
        if config.generate_sites:
            preview_url = await self.generator.generate_site(lead, profile)
            await increment_campaign(campaign_id, "sites_generated")
            await update_lead_status(lead.id, "Preview Ready")

        if config.prepare_outreach:
            draft = await self.outreach.prepare(campaign_id, lead, profile, preview_url)
            await increment_campaign(campaign_id, "drafts_prepared")
            await update_lead_status(lead.id, "Draft Ready")
            latest = await get_campaign(campaign_id)
            allowed_by_cap = bool(latest and latest["sent_count"] < settings.max_outreach_per_run)
            delivery = await self.outreach.deliver(draft, lead, config.outreach_approved and allowed_by_cap)
            if delivery["sent"]:
                await increment_campaign(campaign_id, "sent_count")
                await update_lead_status(lead.id, "Contacted")
            await add_campaign_log(campaign_id, "outreach", delivery["note"], lead.id)


class LeadWorkflowOrchestrator:
    """Compatibility wrapper for the former single-command interface."""

    def __init__(self, niche: str, location: str, mock_mode: bool = True, limit: int = 2):
        self.niche, self.location, self.mock_mode, self.limit = niche, location, mock_mode, limit

    async def execute_pipeline(self) -> Dict[str, Any]:
        parts = [part.strip() for part in self.location.split(",")]
        location = LocationModel(city=parts[0], state=parts[1] if len(parts) > 1 else parts[0], country=parts[2] if len(parts) > 2 else "India")
        payload = CampaignCreate(name=f"{self.niche} - {location.label}", niches=[self.niche], locations=[location], provider="mock" if self.mock_mode else "google_places", results_per_query=self.limit)
        await init_db()
        campaign_id = await create_campaign(payload)
        return await CampaignRunner().run(campaign_id)


async def _main() -> None:
    parser = argparse.ArgumentParser(description="CinemaOS OPC resumable business campaign runner")
    parser.add_argument("--niche", choices=list(NICHES), default="Real Estate")
    parser.add_argument("--all-niches", action="store_true", help="Run every configured niche one by one")
    parser.add_argument("--city", default="Noida")
    parser.add_argument("--state", default="Uttar Pradesh")
    parser.add_argument("--country", default="India")
    parser.add_argument("--provider", choices=["mock", "google_places"], default="mock")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--approve-outreach", action="store_true", help="Also requires OUTREACH_MODE=approved")
    args = parser.parse_args()
    payload = CampaignCreate(name=f"CLI campaign - {args.city}", niches=list(NICHES) if args.all_niches else [args.niche], locations=[LocationModel(city=args.city, state=args.state, country=args.country)], provider=args.provider, results_per_query=args.limit, outreach_approved=args.approve_outreach)
    await init_db()
    campaign_id = await create_campaign(payload)
    result = await CampaignRunner().run(campaign_id)
    print(result)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    asyncio.run(_main())
