import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
from sqlalchemy import String, Text, Boolean, DateTime, Column, Integer, ForeignKey
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.future import select

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Database")

# Detect database configuration. Default to SQLite inside the current workspace.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./leads.db")
if DATABASE_URL.startswith("postgresql://"):
    # Convert postgres:// to postgresql+asyncpg:// if needed
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

logger.info(f"Connecting to database with URI: {DATABASE_URL}")

engine = create_async_engine(DATABASE_URL, echo=False, future=True)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

# =====================================================================
# Database Tables Schema
# =====================================================================

class LeadTable(Base):
    __tablename__ = "leads"

    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    email = Column(String(100), nullable=True)
    website = Column(String(255), nullable=True)
    niche = Column(String(100), nullable=False, index=True)
    location = Column(String(100), nullable=False, index=True)
    status = Column(String(50), default="Scraped", index=True)  # Scraped, Audited, Generated, Pitched, Failed
    created_at = Column(DateTime, default=datetime.utcnow)


class EnrichedProfileTable(Base):
    __tablename__ = "enriched_profiles"

    lead_id = Column(String(50), ForeignKey("leads.id", ondelete="CASCADE"), primary_key=True)
    pain_points = Column(Text, nullable=False)  # JSON serialized list
    voice_agent_necessity = Column(Text, nullable=False)
    branding_vibe = Column(Text, nullable=False)
    competitors = Column(Text, nullable=False)  # JSON serialized list
    ui_ux_gaps = Column(Text, nullable=False)  # JSON serialized list
    is_responsive_missing = Column(Boolean, default=False)
    lacks_interactive_ai = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class WorkflowLogTable(Base):
    __tablename__ = "workflow_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lead_id = Column(String(50), index=True, nullable=True)
    node_name = Column(String(100), nullable=False)
    log_message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

# =====================================================================
# Async Core Helpers
# =====================================================================

async def init_db():
    """Create database tables if they do not exist."""
    async with engine.begin() as conn:
        logger.info("Initializing database schemas...")
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully.")


async def save_lead(lead_data: Dict[str, Any]) -> None:
    """Save or update a scraped lead record."""
    async with async_session() as session:
        async with session.begin():
            # Check if lead exists
            stmt = select(LeadTable).where(LeadTable.id == lead_data["id"])
            result = await session.execute(stmt)
            existing = result.scalars().first()

            if existing:
                existing.name = lead_data["name"]
                existing.phone = lead_data.get("phone")
                existing.email = lead_data.get("email")
                existing.website = lead_data.get("website")
                existing.niche = lead_data["niche"]
                existing.location = lead_data["location"]
            else:
                lead = LeadTable(
                    id=lead_data["id"],
                    name=lead_data["name"],
                    phone=lead_data.get("phone"),
                    email=lead_data.get("email"),
                    website=lead_data.get("website"),
                    niche=lead_data["niche"],
                    location=lead_data["location"],
                    status=lead_data.get("status", "Scraped")
                )
                session.add(lead)
            await session.commit()


async def update_lead_status(lead_id: str, status: str) -> None:
    """Update outreach lifecycle status of a lead."""
    async with async_session() as session:
        async with session.begin():
            stmt = select(LeadTable).where(LeadTable.id == lead_id)
            result = await session.execute(stmt)
            lead = result.scalars().first()
            if lead:
                lead.status = status
                await session.commit()
                logger.info(f"Lead {lead_id} updated to status '{status}'")


async def save_enriched_profile(profile_data: Dict[str, Any]) -> None:
    """Save enriched business audit data."""
    async with async_session() as session:
        async with session.begin():
            # Check if profile already exists
            stmt = select(EnrichedProfileTable).where(EnrichedProfileTable.lead_id == profile_data["lead_id"])
            result = await session.execute(stmt)
            existing = result.scalars().first()

            # Serialize lists to JSON text strings
            pain_points_str = json.dumps(profile_data.get("pain_points", []))
            competitors_str = json.dumps(profile_data.get("competitors", []))
            ui_ux_gaps_str = json.dumps(profile_data.get("ui_ux_gaps", []))

            if existing:
                existing.pain_points = pain_points_str
                existing.voice_agent_necessity = profile_data["voice_agent_necessity"]
                existing.branding_vibe = profile_data["branding_vibe"]
                existing.competitors = competitors_str
                existing.ui_ux_gaps = ui_ux_gaps_str
                existing.is_responsive_missing = profile_data.get("is_responsive_missing", False)
                existing.lacks_interactive_ai = profile_data.get("lacks_interactive_ai", True)
            else:
                profile = EnrichedProfileTable(
                    lead_id=profile_data["lead_id"],
                    pain_points=pain_points_str,
                    voice_agent_necessity=profile_data["voice_agent_necessity"],
                    branding_vibe=profile_data["branding_vibe"],
                    competitors=competitors_str,
                    ui_ux_gaps=ui_ux_gaps_str,
                    is_responsive_missing=profile_data.get("is_responsive_missing", False),
                    lacks_interactive_ai=profile_data.get("lacks_interactive_ai", True)
                )
                session.add(profile)
            await session.commit()


async def add_workflow_log(lead_id: Optional[str], node_name: str, message: str) -> None:
    """Add a dynamic log entry for a specific lead workflow execution step."""
    async with async_session() as session:
        async with session.begin():
            log = WorkflowLogTable(
                lead_id=lead_id,
                node_name=node_name,
                log_message=message
            )
            session.add(log)
            await session.commit()
            logger.info(f"[{node_name}] {message}")


async def get_lead(lead_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve detailed lead record."""
    async with async_session() as session:
        stmt = select(LeadTable).where(LeadTable.id == lead_id)
        result = await session.execute(stmt)
        lead = result.scalars().first()
        if lead:
            return {
                "id": lead.id,
                "name": lead.name,
                "phone": lead.phone,
                "email": lead.email,
                "website": lead.website,
                "niche": lead.niche,
                "location": lead.location,
                "status": lead.status,
                "created_at": lead.created_at.isoformat()
            }
        return None


async def get_enriched_profile(lead_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve detailed enriched profile record."""
    async with async_session() as session:
        stmt = select(EnrichedProfileTable).where(EnrichedProfileTable.lead_id == lead_id)
        result = await session.execute(stmt)
        profile = result.scalars().first()
        if profile:
            return {
                "lead_id": profile.lead_id,
                "pain_points": json.loads(profile.pain_points),
                "voice_agent_necessity": profile.voice_agent_necessity,
                "branding_vibe": profile.branding_vibe,
                "competitors": json.loads(profile.competitors),
                "ui_ux_gaps": json.loads(profile.ui_ux_gaps),
                "is_responsive_missing": profile.is_responsive_missing,
                "lacks_interactive_ai": profile.lacks_interactive_ai,
                "created_at": profile.created_at.isoformat()
            }
        return None


async def get_all_leads_by_niche_and_location(niche: str, location: str) -> List[Dict[str, Any]]:
    """Get all leads of a niche in a specific location."""
    async with async_session() as session:
        stmt = select(LeadTable).where(LeadTable.niche == niche, LeadTable.location == location)
        result = await session.execute(stmt)
        leads = result.scalars().all()
        return [
            {
                "id": lead.id,
                "name": lead.name,
                "phone": lead.phone,
                "email": lead.email,
                "website": lead.website,
                "niche": lead.niche,
                "location": lead.location,
                "status": lead.status
            }
            for lead in leads
        ]
