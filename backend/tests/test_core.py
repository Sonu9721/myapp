import pytest
import httpx
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend.ai import OpenAIStudioClient, fallback_page, sanitize_generated_html
from backend.config import CampaignCreate, EnrichedBusinessProfile, LeadModel, LocationModel, NICHES
from backend import database
from backend.api import app
from backend.orchestrator import CampaignRunner
from backend.scraper import MockLeadScraper, normalize_phone


def test_all_required_niches_are_configured():
    assert set(NICHES) == {"Doctors", "Real Estate", "Gyms", "Cafes", "Boutiques", "Law Firms", "HVAC/Plumbing", "Salons", "Digital Creators", "Private Schools"}


def test_campaign_rejects_unknown_niche():
    with pytest.raises(ValueError):
        CampaignCreate(name="Bad campaign", niches=["Unknown"], locations=[LocationModel(city="Noida", state="Uttar Pradesh")])


@pytest.mark.asyncio
async def test_mock_discovery_is_deterministic_and_non_deliverable():
    scraper = MockLeadScraper()
    first = await scraper.scrape("Real Estate", "Noida, Uttar Pradesh, India", 2)
    second = await scraper.scrape("Real Estate", "Noida, Uttar Pradesh, India", 2)
    assert [lead.id for lead in first] == [lead.id for lead in second]
    assert all(not lead.email and not lead.phone for lead in first)


def test_html_sanitizer_removes_active_content():
    cleaned = sanitize_generated_html("<html><body onload='bad()'><script>bad()</script><h1>Safe</h1></body></html>")
    assert "script" not in cleaned.lower()
    assert "onload" not in cleaned.lower()
    assert "Safe" in cleaned


def test_fallback_page_escapes_business_name():
    lead = LeadModel(id="lead_1", name="<script>alert(1)</script>", niche="Gyms", location="Noida")
    profile = EnrichedBusinessProfile(lead_id=lead.id, pain_points=["Slow replies"], voice_agent_necessity="Useful", branding_vibe="Clean", recommended_offer="Trial booking")
    page = fallback_page(lead, profile)
    assert "<script>alert" not in page
    assert "&lt;script&gt;" in page


def test_openai_default_model_is_sol():
    assert OpenAIStudioClient(api_key="test").model == "gpt-5.6-sol"


def test_scraper_machine_counts_every_keyword_job():
    payload = CampaignCreate(
        name="All niche machine",
        niches=["Doctors", "Real Estate"],
        locations=[
            LocationModel(city="Mumbai", state="Maharashtra"),
            LocationModel(city="Pune", state="Maharashtra"),
        ],
    )
    assert payload.scrape_job_count == 2 * (len(NICHES["Doctors"].search_terms) + len(NICHES["Real Estate"].search_terms))


def test_duplicate_locations_are_removed_before_jobs_are_created():
    payload = CampaignCreate(
        name="Location dedupe",
        niches=["Gyms"],
        locations=[
            LocationModel(city="Noida", state="Uttar Pradesh"),
            LocationModel(city="noida", state="uttar pradesh", country="india"),
        ],
    )
    assert len(payload.locations) == 1


def test_phone_normalization_is_conservative_for_india():
    assert normalize_phone("98765-43210") == "+919876543210"
    assert normalize_phone("+91 98765 43210") == "+919876543210"
    assert normalize_phone("123") is None


@pytest.mark.asyncio
async def test_mock_keyword_jobs_preserve_found_via_keyword():
    scraper = MockLeadScraper()
    clinics = await scraper.scrape("Doctors", "Mumbai, Maharashtra, India", 1, "medical clinic")
    dentists = await scraper.scrape("Doctors", "Mumbai, Maharashtra, India", 1, "dental clinic")
    assert clinics[0].found_via_keyword == "medical clinic"
    assert dentists[0].found_via_keyword == "dental clinic"
    assert clinics[0].source_id != dentists[0].source_id


@pytest.mark.asyncio
async def test_scraper_machine_runs_and_exports_one_row_per_keyword(tmp_path):
    original_engine, original_sessions = database.engine, database.async_session
    test_engine = create_async_engine(f"sqlite+aiosqlite:///{(tmp_path / 'machine.db').as_posix()}")
    database.engine = test_engine
    database.async_session = async_sessionmaker(test_engine, expire_on_commit=False)
    try:
        await database.init_db()
        payload = CampaignCreate(
            name="Doctors scraper machine", niches=["Doctors"],
            locations=[LocationModel(city="Mumbai", state="Maharashtra")],
            provider="mock", results_per_query=1,
        )
        campaign_id = await database.create_campaign(payload)
        result = await CampaignRunner().run(campaign_id)
        rows = await database.campaign_export_rows(campaign_id)
        assert result["status"] == "completed"
        assert result["total_tasks"] == len(NICHES["Doctors"].search_terms)
        assert result["completed_tasks"] == result["total_tasks"]
        assert len(rows) == len(NICHES["Doctors"].search_terms)
        assert {row["Found Via Keyword"] for row in rows} == set(NICHES["Doctors"].search_terms)
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            jobs_response = await client.get(f"/api/campaigns/{campaign_id}/jobs")
            export_response = await client.get(f"/api/campaigns/{campaign_id}/export.csv")
        assert jobs_response.status_code == 200
        assert [job["keyword"] for job in jobs_response.json()] == NICHES["Doctors"].search_terms
        assert export_response.status_code == 200
        assert "Found Via Keyword" in export_response.text
    finally:
        await test_engine.dispose()
        database.engine, database.async_session = original_engine, original_sessions
