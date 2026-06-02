import os
from typing import List, Dict, Optional
from pydantic import BaseModel, Field, HttpUrl
from dotenv import load_dotenv

load_dotenv()

# =====================================================================
# Pydantic v2 Models for Validation & Serialization
# =====================================================================

class NicheConfigModel(BaseModel):
    niche_name: str = Field(..., description="Name of the industry niche")
    default_keywords: List[str] = Field(..., description="Default keywords for local scraping")
    pain_points: List[str] = Field(..., description="Niche-specific leakage points & business pain points")
    core_solutions: List[str] = Field(..., description="Tailored core AI & automated product offerings")
    suggested_cta: str = Field(..., description="Actionable zero-friction CTA recommendation")


class LeadModel(BaseModel):
    id: str = Field(..., description="Unique lead identifier")
    name: str = Field(..., description="Business name")
    phone: Optional[str] = Field(None, description="Contact phone number")
    email: Optional[str] = Field(None, description="Contact email address")
    website: Optional[str] = Field(None, description="Company website URL")
    niche: str = Field(..., description="Niche category")
    location: str = Field(..., description="Geographic location of the lead")
    status: str = Field("Scraped", description="Status of lead in outreach pipeline")


class EnrichedBusinessProfile(BaseModel):
    lead_id: str = Field(..., description="Associated lead identifier")
    pain_points: List[str] = Field(..., description="Specific verified operational bottlenecks")
    voice_agent_necessity: str = Field(..., description="Logical justification for an AI voice agent")
    branding_vibe: str = Field(..., description="Minimalist and corporate design style identity recommendation")
    competitors: List[str] = Field(default_factory=list, description="Top 3 geo-competitors if website is weak or absent")
    ui_ux_gaps: List[str] = Field(default_factory=list, description="Gaps analyzed on website if present")
    is_responsive_missing: bool = Field(False, description="True if website lacks mobile responsive layouts")
    lacks_interactive_ai: bool = Field(True, description="True if website lacks custom AI chat systems")

# =====================================================================
# Central Dynamic Niches Configuration Metadata
# =====================================================================

NICHES: Dict[str, NicheConfigModel] = {
    "Doctors": NicheConfigModel(
        niche_name="Doctors",
        default_keywords=["medical clinic", "pediatrician", "family doctor", "dental clinic"],
        pain_points=[
            "High booking friction leading to missed appointments",
            "Lack of HIPAA-compliant automated intake forms",
            "Front-desk fatigue causing delayed patient follow-ups",
            "After-hours inquiries left completely unanswered"
        ],
        core_solutions=[
            "24/7 HIPAA-compliant conversational booking system",
            "Instant automated digital intake forms mapped to CRM",
            "AI Patient Recall Agent bringing back inactive accounts"
        ],
        suggested_cta="Book patient intake demo in 1-click"
    ),
    "Real Estate": NicheConfigModel(
        niche_name="Real Estate",
        default_keywords=["real estate agency", "property dealer", "luxury homes realtor"],
        pain_points=[
            "Extremely high lead response times causing high drop-off rates",
            "Manual tracking of buyer preferences via static spreadsheets",
            "Outdated property portfolios that load poorly on mobile browsers",
            "Missing interactive conversational tours on listings pages"
        ],
        core_solutions=[
            "Instant property visual page with AI chat concierge",
            "Automated multi-channel CRM lead-nurturing sequences",
            "Cinematic virtual touring hubs that capture buyer intent"
        ],
        suggested_cta="View custom interactive listings demo"
    ),
    "Gyms": NicheConfigModel(
        niche_name="Gyms",
        default_keywords=["fitness center", "crossfit gym", "yoga studio", "health club"],
        pain_points=[
            "High membership churn rates due to lack of engagement",
            "Complex class-booking steps causing user drop-off",
            "No dynamic workout orientation tracking system online",
            "Staff spending hours manually checking members in"
        ],
        core_solutions=[
            "Interactive member onboarding & class booking scheduler",
            "AI Retention Messaging Swarm checking on inactive members",
            "Dynamic localized trainer matching and booking platform"
        ],
        suggested_cta="Check class booking optimization layout"
    ),
    "Cafes": NicheConfigModel(
        niche_name="Cafes",
        default_keywords=["coffee shop", "artisan cafe", "bakery bistro", "roastery"],
        pain_points=[
            "Inefficient digital order routing during peak hours",
            "Outdated, static menu pages on mobile devices",
            "No direct local SEO/Google Maps dynamic loyalty capture",
            "Heavily reliant on expensive third-party delivery fees"
        ],
        core_solutions=[
            "Instant digital menu, ordering, and mobile payment card",
            "Direct loyalty engagement portals bypassed third-party costs",
            "Localized SEO amplifier driving high footfall on Google Maps"
        ],
        suggested_cta="Open digital orders & loyalty demo menu"
    ),
    "Boutiques": NicheConfigModel(
        niche_name="Boutiques",
        default_keywords=["fashion boutique", "designer clothing store", "concept store"],
        pain_points=[
            "Generic standard e-commerce with zero personalization",
            "Very high shopping cart abandonment on mobile checkouts",
            "No dynamic outfit recommendation tools for website visitors",
            "Delayed responses to standard sizing & return inquiries"
        ],
        core_solutions=[
            "Interactive AI personal stylist recommendations",
            "Micro-checkout widgets optimized for smooth mobile sales",
            "Visual character consistency size-guide chatbot"
        ],
        suggested_cta="Launch boutique sizing & stylist AI guide"
    ),
    "Law Firms": NicheConfigModel(
        niche_name="Law Firms",
        default_keywords=["corporate law firm", "family attorney", "criminal defense lawyer"],
        pain_points=[
            "Friction-heavy consultation scheduling procedures",
            "High rate of unqualified leads taking up billable hours",
            "Tiresome manual client intake & questionnaire tracking",
            "No real-time response to emergency litigation inquiries"
        ],
        core_solutions=[
            "Streamlined legal intake questionnaire & booking matrix",
            "Autonomous qualifying agent filtering prospective clients",
            "Secure, responsive document repository portal with AI summary"
        ],
        suggested_cta="Inspect qualified legal intake template"
    ),
    "HVAC/Plumbing": NicheConfigModel(
        niche_name="HVAC/Plumbing",
        default_keywords=["hvac repair", "emergency plumber", "air conditioning services"],
        pain_points=[
            "Off-hours emergency plumbing calls leaking to competitors",
            "Inefficient dispatcher routing causing service delays",
            "No transparent dynamic pricing or booking confirmation online",
            "Missed customer follow-ups for annual system maintenance"
        ],
        core_solutions=[
            "24/7 priority emergency dispatcher dynamic dashboard",
            "Local service status and dispatch tracking widgets",
            "Automated annual system maintenance recall pipeline"
        ],
        suggested_cta="Activate emergency plumber dispatcher layout"
    ),
    "Salons": NicheConfigModel(
        niche_name="Salons",
        default_keywords=["beauty salon", "hair salon", "luxury spa", "nail salon"],
        pain_points=[
            "Revenue loss from last-minute booking cancellations",
            "Unfilled seat hours due to empty booking calendar blocks",
            "No automated follow-up asking for Google reviews",
            "Clunky mobile booking forms that lead to abandonments"
        ],
        core_solutions=[
            "Re-booking discount engine & SMS confirmation matrix",
            "Dynamic calendar filler system matching staff availability",
            "Automated post-service review collector system"
        ],
        suggested_cta="View salon calendar optimization flow"
    ),
    "Digital Creators": NicheConfigModel(
        niche_name="Digital Creators",
        default_keywords=["podcast studio", "content agency", "influencer media agency"],
        pain_points=[
            "Scattered link-in-bios with fragmented sales conversion paths",
            "No direct asset-monetization or course funnel system",
            "Inefficient lead capture for brand deal sponsorships",
            "Time-intensive manual email coordination with prospects"
        ],
        core_solutions=[
            "Premium unified digital asset sales and creator hub",
            "Frictionless course & digital asset checkouts",
            "AI brand sponsorship proposal coordinator agent"
        ],
        suggested_cta="Preview interactive creator media kit"
    ),
    "Private Schools": NicheConfigModel(
        niche_name="Private Schools",
        default_keywords=["private school", "international school", "montessori preschool"],
        pain_points=[
            "Peak-season admission drop-offs due to delayed follow-ups",
            "Heavy administrative overhead handling redundant queries",
            "Unresponsive websites failing to showcase campus facilities",
            "Friction-heavy manual tuition calculation & payment steps"
        ],
        core_solutions=[
            "Virtual admissions tours & automated tuition calculator",
            "School query resolver agent operating 24/7 for parents",
            "Parent-teacher registration dynamic workspace"
        ],
        suggested_cta="Test interactive tuition and tours model"
    )
}

# =====================================================================
# API Configurations & Key Checks
# =====================================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY", "")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "")

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "agency@systemforrevenue.com")
