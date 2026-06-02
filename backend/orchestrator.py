import argparse
import asyncio
import logging
import sys
from typing import List, Dict, Any, Optional
from backend.config import NICHES
from backend.database import (
    init_db, save_lead, save_enriched_profile,
    update_lead_status, add_workflow_log, get_all_leads_by_niche_and_location
)
from backend.scraper import TavilyLeadScraper, MockLeadScraper
from backend.researcher import BusinessAuditor
from backend.generator import ProgrammaticSiteGenerator
from backend.outreach import B2BOutreachEngine

# Configure Logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("OrchestrationEngine")

# =====================================================================
# Programmatic Workflow State Machine Engine
# =====================================================================

class LeadWorkflowOrchestrator:
    """Core state machine executing and recovering lead generation campaigns."""

    def __init__(self, niche: str, location: str, mock_mode: bool = False, limit: int = 2):
        self.niche = niche
        self.location = location
        self.mock_mode = mock_mode
        self.limit = limit
        
        # Validate Niche
        if niche not in NICHES:
            raise ValueError(f"Unsupported niche '{niche}'. Supported niches: {list(NICHES.keys())}")

        # Initialize pipeline classes
        self.scraper = MockLeadScraper() if mock_mode else TavilyLeadScraper()
        self.auditor = BusinessAuditor()
        self.generator = ProgrammaticSiteGenerator(agency_name="CinemaOS AI Agency")
        self.outreach = B2BOutreachEngine(dry_run=mock_mode)

    async def execute_pipeline(self) -> Dict[str, Any]:
        """Runs the complete 4-step lead generation and B2B outreach workflow."""
        await init_db()
        campaign_msg = f"Starting campaigns for Niche='{self.niche}' in Location='{self.location}' (MockMode={self.mock_mode})"
        logger.info(campaign_msg)
        await add_workflow_log(None, "ORCHESTRATOR", campaign_msg)

        # -------------------------------------------------------------
        # STEP 1: Scrape & Config Pipeline
        # -------------------------------------------------------------
        logger.info("Executing STEP 1: Scrape Leads & Save to DB...")
        await add_workflow_log(None, "SCRAPE", f"Initiating lead mining for {self.niche} in {self.location}...")
        
        try:
            leads = await self.scraper.scrape(self.niche, self.location, limit=self.limit)
            if not leads:
                logger.warning("No leads found. Pipeline stopping.")
                await add_workflow_log(None, "SCRAPE", "No leads returned. Orchestrator terminated.")
                return {"status": "No Leads Found", "processed_count": 0}

            for lead in leads:
                # Save scraped lead in database
                await save_lead(lead.model_dump())
                await add_workflow_log(lead.id, "SCRAPE", f"Scraped and registered lead: {lead.name}")
        except Exception as e:
            err_msg = f"Step 1 Scrape failed: {str(e)}"
            logger.error(err_msg)
            await add_workflow_log(None, "SCRAPE", f"CRITICAL ERROR: {err_msg}")
            return {"status": "Step 1 Scrape Failure", "error": str(e)}

        # -------------------------------------------------------------
        # STEP 2: Firecrawl/Tavily Deep Auditing & Llama Profiling
        # -------------------------------------------------------------
        logger.info("Executing STEP 2: Run Deep Audits & AI Profiling...")
        enriched_profiles: Dict[str, Any] = {}
        
        for lead in leads:
            await update_lead_status(lead.id, "Scraped")
            await add_workflow_log(lead.id, "AUDIT", f"Analyzing site elements and competitors...")
            try:
                profile = await self.auditor.audit_single_business(lead)
                # Store in DB state
                await save_enriched_profile(profile.model_dump())
                enriched_profiles[lead.id] = profile
                await update_lead_status(lead.id, "Audited")
                await add_workflow_log(lead.id, "AUDIT", "Deep background audit compiled successfully.")
            except Exception as e:
                err_msg = f"Step 2 Audit failed for lead {lead.id}: {str(e)}"
                logger.error(err_msg)
                await update_lead_status(lead.id, "Failed")
                await add_workflow_log(lead.id, "AUDIT", f"ERROR: {err_msg}")

        # -------------------------------------------------------------
        # STEP 3: Gemini 3.5 Programmatic Page Generation & Deploy
        # -------------------------------------------------------------
        logger.info("Executing STEP 3: Page Generation & Mock Deployment...")
        preview_urls: Dict[str, str] = {}
        
        for lead in leads:
            if lead.id not in enriched_profiles:
                continue
            
            await add_workflow_log(lead.id, "GENERATE", "Triggering programmatic Gemini 3.5 HTML build...")
            try:
                preview_url = await self.generator.generate_site(lead, enriched_profiles[lead.id])
                preview_urls[lead.id] = preview_url
                await update_lead_status(lead.id, "Generated")
                await add_workflow_log(lead.id, "GENERATE", f"Custom live preview asset created: {preview_url}")
            except Exception as e:
                err_msg = f"Step 3 Generation failed for lead {lead.id}: {str(e)}"
                logger.error(err_msg)
                await update_lead_status(lead.id, "Failed")
                await add_workflow_log(lead.id, "GENERATE", f"ERROR: {err_msg}")

        # -------------------------------------------------------------
        # STEP 4: Twilio WhatsApp & SMTP Cold Outreach Dispatcher
        # -------------------------------------------------------------
        logger.info("Executing STEP 4: Multi-Channel Cold Outreach...")
        pitches_triggered = 0
        
        for lead in leads:
            if lead.id not in enriched_profiles or lead.id not in preview_urls:
                continue
            
            await add_workflow_log(lead.id, "OUTREACH", "Assembling pitch stacks and triggering sends...")
            try:
                outreach_results = await self.outreach.execute_outreach_sequence(
                    lead, enriched_profiles[lead.id], preview_urls[lead.id]
                )
                
                if outreach_results["lead_notified"]:
                    await update_lead_status(lead.id, "Pitched")
                    await add_workflow_log(lead.id, "OUTREACH", "SMTP email and WhatsApp pitches successfully fired.")
                    pitches_triggered += 1
                else:
                    await update_lead_status(lead.id, "Failed")
                    await add_workflow_log(lead.id, "OUTREACH", "Failed to dispatch email or WhatsApp pitches.")
            except Exception as e:
                err_msg = f"Step 4 Outreach failed for lead {lead.id}: {str(e)}"
                logger.error(err_msg)
                await update_lead_status(lead.id, "Failed")
                await add_workflow_log(lead.id, "OUTREACH", f"ERROR: {err_msg}")

        summary_msg = f"Campaign concluded. Processed leads: {len(leads)}. Fired pitches: {pitches_triggered}."
        logger.info(summary_msg)
        await add_workflow_log(None, "ORCHESTRATOR", summary_msg)
        
        return {
            "status": "Success",
            "scraped_count": len(leads),
            "pitched_count": pitches_triggered
        }

# =====================================================================
# CLI Entry Point
# =====================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CinemaOS AI Programmatic Lead Gen & Outreach Engine")
    parser.add_argument("--niche", type=str, default="Real Estate", help="Niche category to target (e.g. Real Estate, Doctors)")
    parser.add_argument("--location", type=str, default="Noida", help="Geographic target location")
    parser.add_argument("--mock", action="store_true", default=True, help="Run scraper and outreach in safe mock/dry-run mode")
    parser.add_argument("--limit", type=int, default=2, help="Number of leads to scrape and process")
    
    args = parser.parse_args()
    
    # Run the async state-machine
    asyncio.run(
        LeadWorkflowOrchestrator(
            niche=args.niche,
            location=args.location,
            mock_mode=args.mock,
            limit=args.limit
        ).execute_pipeline()
    )
