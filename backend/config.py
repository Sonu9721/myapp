"""Central configuration and validated domain models for CinemaOS OPC."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List, Literal, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator, model_validator

load_dotenv()


class NicheConfigModel(BaseModel):
    niche_name: str
    search_terms: List[str]
    pain_points: List[str]
    core_solutions: List[str]
    suggested_cta: str

    @property
    def default_keywords(self) -> List[str]:
        return self.search_terms


class LocationModel(BaseModel):
    city: str = Field(min_length=2, max_length=120)
    state: str = Field(min_length=2, max_length=120)
    country: str = Field(default="India", min_length=2, max_length=120)

    @property
    def label(self) -> str:
        return ", ".join(part for part in (self.city, self.state, self.country) if part)


class LeadModel(BaseModel):
    id: str
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    niche: str
    location: str
    status: str = "Discovered"


class DiscoveredLead(LeadModel):
    source: Literal["google_places", "mock", "import"] = "mock"
    source_id: str
    formatted_address: Optional[str] = None
    google_maps_uri: Optional[str] = None
    primary_type: Optional[str] = None
    business_status: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    found_via_keyword: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: str = "India"
    raw_snapshot: Dict = Field(default_factory=dict, exclude=True)


class EnrichedBusinessProfile(BaseModel):
    lead_id: str
    pain_points: List[str]
    voice_agent_necessity: str
    branding_vibe: str
    competitors: List[str] = Field(default_factory=list)
    ui_ux_gaps: List[str] = Field(default_factory=list)
    is_responsive_missing: bool = False
    lacks_interactive_ai: bool = True
    recommended_offer: str = ""
    outreach_angle: str = ""


NICHES: Dict[str, NicheConfigModel] = {
    "Doctors": NicheConfigModel(niche_name="Doctors", search_terms=["medical clinic", "doctor", "dental clinic", "pediatrician"], pain_points=["Missed calls and slow appointment booking", "Manual patient follow-up", "After-hours inquiries go unanswered"], core_solutions=["AI appointment receptionist", "Automated patient recall", "Digital intake and reminders"], suggested_cta="Book a patient-intake demo"),
    "Real Estate": NicheConfigModel(niche_name="Real Estate", search_terms=["real estate agency", "property dealer", "real estate consultant"], pain_points=["Slow response to property inquiries", "Manual lead qualification", "Outdated mobile property experience"], core_solutions=["Instant lead qualification", "Automated viewing scheduler", "Personalized property landing pages"], suggested_cta="Preview the property lead system"),
    "Gyms": NicheConfigModel(niche_name="Gyms", search_terms=["gym", "fitness center", "yoga studio", "crossfit gym"], pain_points=["Membership churn", "Trial inquiries are not followed up", "Complicated class booking"], core_solutions=["Trial-booking assistant", "Member retention automation", "Class scheduling portal"], suggested_cta="Test the membership conversion flow"),
    "Cafes": NicheConfigModel(niche_name="Cafes", search_terms=["cafe", "coffee shop", "bakery", "bistro"], pain_points=["Third-party delivery commissions", "Outdated mobile menus", "Weak direct loyalty capture"], core_solutions=["Direct order and menu portal", "Loyalty automation", "Local discovery landing pages"], suggested_cta="Open the direct-order demo"),
    "Boutiques": NicheConfigModel(niche_name="Boutiques", search_terms=["fashion boutique", "clothing store", "designer boutique"], pain_points=["Mobile cart abandonment", "Repeated sizing questions", "Low personalization"], core_solutions=["AI shopping assistant", "Fast mobile inquiry flow", "Automated catalogue follow-up"], suggested_cta="Preview the personal-stylist flow"),
    "Law Firms": NicheConfigModel(niche_name="Law Firms", search_terms=["law firm", "advocate", "legal consultant"], pain_points=["Unqualified inquiries consume staff time", "Slow consultation intake", "Emergency inquiries are missed"], core_solutions=["Consultation qualification", "Secure intake workflow", "Automated appointment routing"], suggested_cta="Inspect the legal-intake demo"),
    "HVAC/Plumbing": NicheConfigModel(niche_name="HVAC/Plumbing", search_terms=["plumber", "plumbing service", "HVAC contractor", "air conditioning repair"], pain_points=["Missed emergency calls", "Manual dispatching", "Weak maintenance follow-up"], core_solutions=["24/7 call qualification", "Dispatch request portal", "Maintenance reminder automation"], suggested_cta="Test the emergency-dispatch flow"),
    "Salons": NicheConfigModel(niche_name="Salons", search_terms=["beauty salon", "hair salon", "spa", "nail salon"], pain_points=["Last-minute cancellations", "Empty appointment slots", "Manual review requests"], core_solutions=["Booking and reminder assistant", "Wait-list slot filler", "Automated review follow-up"], suggested_cta="View the salon booking flow"),
    "Digital Creators": NicheConfigModel(niche_name="Digital Creators", search_terms=["digital marketing agency", "content creator", "podcast studio", "media agency"], pain_points=["Fragmented sales links", "Manual sponsor coordination", "Weak lead capture"], core_solutions=["Unified creator hub", "Sponsor inquiry assistant", "Digital-product funnel"], suggested_cta="Preview the creator revenue hub"),
    "Private Schools": NicheConfigModel(niche_name="Private Schools", search_terms=["private school", "international school", "montessori school", "preschool"], pain_points=["Admission inquiries receive slow replies", "Repeated parent questions", "Manual campus-tour scheduling"], core_solutions=["Admissions inquiry assistant", "Campus-tour booking", "Automated parent follow-up"], suggested_cta="Test the admissions flow"),
}


class CampaignCreate(BaseModel):
    name: str = Field(min_length=3, max_length=160)
    niches: List[str] = Field(min_length=1)
    locations: List[LocationModel] = Field(min_length=1)
    provider: Literal["mock", "google_places"] = "mock"
    results_per_query: int = Field(default=10, ge=1, le=60)
    analyse_businesses: bool = False
    generate_sites: bool = False
    prepare_outreach: bool = False
    outreach_approved: bool = False

    @field_validator("niches")
    @classmethod
    def validate_niches(cls, value: List[str]) -> List[str]:
        unknown = sorted(set(value) - set(NICHES))
        if unknown:
            raise ValueError(f"Unsupported niches: {', '.join(unknown)}")
        return list(dict.fromkeys(value))

    @field_validator("locations")
    @classmethod
    def deduplicate_locations(cls, value: List[LocationModel]) -> List[LocationModel]:
        unique: Dict[str, LocationModel] = {}
        for location in value:
            unique[location.label.casefold()] = location
        return list(unique.values())

    @model_validator(mode="after")
    def enable_required_stages(self) -> "CampaignCreate":
        if self.generate_sites or self.prepare_outreach:
            self.analyse_businesses = True
        return self

    @property
    def scrape_job_count(self) -> int:
        keyword_count = sum(len(NICHES[niche].search_terms) for niche in self.niches)
        return keyword_count * len(self.locations)


def _bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "development")
    database_url: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./leads.db")
    frontend_origins: str = os.getenv("FRONTEND_ORIGINS", "http://localhost:3000")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-5.6-sol")
    openai_reasoning_effort: str = os.getenv("OPENAI_REASONING_EFFORT", "medium")
    openai_timeout_seconds: int = _int("OPENAI_TIMEOUT_SECONDS", 120)
    google_places_api_key: str = os.getenv("GOOGLE_PLACES_API_KEY", "")
    google_places_language: str = os.getenv("GOOGLE_PLACES_LANGUAGE", "en")
    google_places_region: str = os.getenv("GOOGLE_PLACES_REGION", "IN")
    google_places_cache_ttl_hours: int = _int("GOOGLE_PLACES_CACHE_TTL_HOURS", 24)
    max_results_per_query: int = _int("MAX_RESULTS_PER_QUERY", 20)
    max_campaign_tasks: int = _int("MAX_CAMPAIGN_TASKS", 5000)
    max_concurrent_leads: int = _int("MAX_CONCURRENT_LEADS", 3)
    website_enrichment_enabled: bool = _bool("WEBSITE_ENRICHMENT_ENABLED", True)
    website_timeout_seconds: int = _int("WEBSITE_TIMEOUT_SECONDS", 10)
    outreach_mode: str = os.getenv("OUTREACH_MODE", "draft").lower()
    max_outreach_per_run: int = _int("MAX_OUTREACH_PER_RUN", 10)
    smtp_host: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port: int = _int("SMTP_PORT", 587)
    smtp_user: str = os.getenv("SMTP_USER", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    default_from_email: str = os.getenv("DEFAULT_FROM_EMAIL", "")
    twilio_account_sid: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    twilio_auth_token: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    twilio_phone_number: str = os.getenv("TWILIO_PHONE_NUMBER", "")

    @property
    def cors_origins(self) -> List[str]:
        return [item.strip() for item in self.frontend_origins.split(",") if item.strip()]


settings = Settings()

# Backward-compatible names for older imports.
GROQ_API_KEY = GEMINI_API_KEY = TAVILY_API_KEY = FIRECRAWL_API_KEY = ""
TWILIO_ACCOUNT_SID = settings.twilio_account_sid
TWILIO_AUTH_TOKEN = settings.twilio_auth_token
TWILIO_PHONE_NUMBER = settings.twilio_phone_number
SMTP_HOST = settings.smtp_host
SMTP_PORT = settings.smtp_port
SMTP_USER = settings.smtp_user
SMTP_PASSWORD = settings.smtp_password
DEFAULT_FROM_EMAIL = settings.default_from_email
