"""Async persistence for leads, resumable campaigns, drafts and audit logs."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from backend.config import CampaignCreate, NICHES, settings

DATABASE_URL = settings.database_url
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(DATABASE_URL, echo=False, future=True)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class LeadTable(Base):
    __tablename__ = "leads"
    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    email = Column(String(100), nullable=True)
    website = Column(String(500), nullable=True)
    niche = Column(String(100), nullable=False, index=True)
    location = Column(String(255), nullable=False, index=True)
    status = Column(String(50), default="Discovered", index=True)
    created_at = Column(DateTime, default=utcnow)


class EnrichedProfileTable(Base):
    __tablename__ = "enriched_profiles"
    lead_id = Column(String(50), ForeignKey("leads.id", ondelete="CASCADE"), primary_key=True)
    pain_points = Column(Text, nullable=False)
    voice_agent_necessity = Column(Text, nullable=False)
    branding_vibe = Column(Text, nullable=False)
    competitors = Column(Text, nullable=False)
    ui_ux_gaps = Column(Text, nullable=False)
    is_responsive_missing = Column(Boolean, default=False)
    lacks_interactive_ai = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)


class WorkflowLogTable(Base):
    __tablename__ = "workflow_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    lead_id = Column(String(50), index=True, nullable=True)
    node_name = Column(String(100), nullable=False)
    log_message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=utcnow)


class CampaignTable(Base):
    __tablename__ = "campaigns"
    id = Column(String(36), primary_key=True)
    name = Column(String(160), nullable=False)
    provider = Column(String(40), nullable=False)
    status = Column(String(30), default="queued", index=True)
    configuration = Column(Text, nullable=False)
    outreach_approved = Column(Boolean, default=False)
    total_tasks = Column(Integer, default=0)
    completed_tasks = Column(Integer, default=0)
    leads_processed = Column(Integer, default=0)
    sites_generated = Column(Integer, default=0)
    drafts_prepared = Column(Integer, default=0)
    sent_count = Column(Integer, default=0)
    stop_requested = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class CampaignTaskTable(Base):
    __tablename__ = "campaign_tasks"
    id = Column(String(36), primary_key=True)
    campaign_id = Column(String(36), ForeignKey("campaigns.id", ondelete="CASCADE"), index=True, nullable=False)
    niche = Column(String(100), nullable=False)
    location = Column(String(255), nullable=False)
    status = Column(String(30), default="queued", index=True)
    attempt_count = Column(Integer, default=0)
    result_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    __table_args__ = (UniqueConstraint("campaign_id", "niche", "location", name="uq_campaign_niche_location"),)


class ScrapeJobTable(Base):
    """Smallest resumable discovery unit: one keyword in one location."""

    __tablename__ = "scrape_jobs"
    id = Column(String(36), primary_key=True)
    campaign_id = Column(String(36), ForeignKey("campaigns.id", ondelete="CASCADE"), index=True, nullable=False)
    niche = Column(String(100), nullable=False, index=True)
    keyword = Column(String(160), nullable=False)
    location = Column(String(255), nullable=False, index=True)
    city = Column(String(120), nullable=False)
    state = Column(String(120), nullable=False)
    country = Column(String(120), nullable=False, default="India")
    position = Column(Integer, nullable=False, default=0, index=True)
    status = Column(String(30), default="queued", index=True)
    attempt_count = Column(Integer, default=0)
    result_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    __table_args__ = (
        UniqueConstraint("campaign_id", "niche", "keyword", "location", name="uq_campaign_scrape_job"),
    )


class CampaignLeadTable(Base):
    __tablename__ = "campaign_leads"
    id = Column(Integer, primary_key=True, autoincrement=True)
    campaign_id = Column(String(36), ForeignKey("campaigns.id", ondelete="CASCADE"), index=True, nullable=False)
    lead_id = Column(String(50), ForeignKey("leads.id", ondelete="CASCADE"), index=True, nullable=False)
    __table_args__ = (UniqueConstraint("campaign_id", "lead_id", name="uq_campaign_lead"),)


class LeadDiscoveryTable(Base):
    """Preserves every keyword/location match even after lead deduplication."""

    __tablename__ = "lead_discoveries"
    id = Column(Integer, primary_key=True, autoincrement=True)
    campaign_id = Column(String(36), ForeignKey("campaigns.id", ondelete="CASCADE"), index=True, nullable=False)
    lead_id = Column(String(50), ForeignKey("leads.id", ondelete="CASCADE"), index=True, nullable=False)
    provider = Column(String(40), nullable=False)
    niche = Column(String(100), nullable=False)
    keyword = Column(String(160), nullable=False)
    location = Column(String(255), nullable=False)
    city = Column(String(120), nullable=False)
    state = Column(String(120), nullable=False)
    country = Column(String(120), nullable=False, default="India")
    discovered_at = Column(DateTime, default=utcnow)
    __table_args__ = (
        UniqueConstraint("campaign_id", "lead_id", "niche", "keyword", "location", name="uq_lead_discovery"),
    )


class LeadSourceTable(Base):
    __tablename__ = "lead_sources"
    id = Column(Integer, primary_key=True, autoincrement=True)
    lead_id = Column(String(50), ForeignKey("leads.id", ondelete="CASCADE"), unique=True, nullable=False)
    provider = Column(String(40), nullable=False, index=True)
    external_id = Column(String(255), nullable=False, index=True)
    formatted_address = Column(Text, nullable=True)
    google_maps_uri = Column(Text, nullable=True)
    primary_type = Column(String(120), nullable=True)
    business_status = Column(String(80), nullable=True)
    rating = Column(String(20), nullable=True)
    review_count = Column(Integer, nullable=True)
    raw_snapshot = Column(Text, nullable=True)
    snapshot_expires_at = Column(DateTime, nullable=True)
    discovered_at = Column(DateTime, default=utcnow)
    __table_args__ = (UniqueConstraint("provider", "external_id", name="uq_provider_external_id"),)


class OutreachDraftTable(Base):
    __tablename__ = "outreach_drafts"
    id = Column(String(36), primary_key=True)
    campaign_id = Column(String(36), ForeignKey("campaigns.id", ondelete="CASCADE"), index=True, nullable=False)
    lead_id = Column(String(50), ForeignKey("leads.id", ondelete="CASCADE"), index=True, nullable=False)
    subject = Column(Text, nullable=False)
    email_body = Column(Text, nullable=False)
    whatsapp_body = Column(Text, nullable=False)
    status = Column(String(30), default="draft", index=True)
    delivery_note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    sent_at = Column(DateTime, nullable=True)
    __table_args__ = (UniqueConstraint("campaign_id", "lead_id", name="uq_campaign_draft"),)


class CampaignLogTable(Base):
    __tablename__ = "campaign_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    campaign_id = Column(String(36), ForeignKey("campaigns.id", ondelete="CASCADE"), index=True, nullable=False)
    lead_id = Column(String(50), nullable=True, index=True)
    stage = Column(String(80), nullable=False)
    level = Column(String(20), default="info")
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow)


class DoNotContactTable(Base):
    __tablename__ = "do_not_contact"
    id = Column(Integer, primary_key=True, autoincrement=True)
    kind = Column(String(20), nullable=False)
    value = Column(String(255), nullable=False)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    __table_args__ = (UniqueConstraint("kind", "value", name="uq_dnc_kind_value"),)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def save_lead(lead_data: Dict[str, Any]) -> str:
    async with async_session() as session:
        existing = await session.get(LeadTable, lead_data["id"])
        if existing:
            for field in ("name", "phone", "email", "website"):
                if lead_data.get(field):
                    setattr(existing, field, lead_data[field])
        else:
            values = {key: lead_data.get(key) for key in ("id", "name", "phone", "email", "website", "niche", "location", "status")}
            session.add(LeadTable(**values))
        await session.commit()
    return lead_data["id"]


async def find_lead_id_by_source(provider: str, external_id: str) -> Optional[str]:
    async with async_session() as session:
        return (await session.execute(select(LeadSourceTable.lead_id).where(LeadSourceTable.provider == provider, LeadSourceTable.external_id == external_id))).scalar_one_or_none()


async def save_lead_source(lead_id: str, source: Dict[str, Any]) -> None:
    expires_at = utcnow() + timedelta(hours=max(1, settings.google_places_cache_ttl_hours)) if source.get("raw_snapshot") else None
    async with async_session() as session:
        row = (await session.execute(select(LeadSourceTable).where(LeadSourceTable.provider == source["source"], LeadSourceTable.external_id == source["source_id"]))).scalars().first()
        values = {
            "lead_id": lead_id, "provider": source["source"], "external_id": source["source_id"],
            "formatted_address": source.get("formatted_address"), "google_maps_uri": source.get("google_maps_uri"),
            "primary_type": source.get("primary_type"), "business_status": source.get("business_status"),
            "rating": str(source.get("rating")) if source.get("rating") is not None else None,
            "review_count": source.get("review_count"),
            "raw_snapshot": json.dumps(source.get("raw_snapshot"), ensure_ascii=False) if source.get("raw_snapshot") else None,
            "snapshot_expires_at": expires_at,
        }
        if row:
            for key, value in values.items():
                setattr(row, key, value)
        else:
            session.add(LeadSourceTable(**values))
        await session.commit()


async def purge_expired_source_snapshots() -> int:
    async with async_session() as session:
        result = await session.execute(update(LeadSourceTable).where(LeadSourceTable.snapshot_expires_at < utcnow(), LeadSourceTable.raw_snapshot.is_not(None)).values(raw_snapshot=None))
        await session.commit()
        return result.rowcount or 0


async def update_lead_status(lead_id: str, status: str) -> None:
    async with async_session() as session:
        await session.execute(update(LeadTable).where(LeadTable.id == lead_id).values(status=status))
        await session.commit()


async def save_enriched_profile(profile_data: Dict[str, Any]) -> None:
    serialized = {key: json.dumps(profile_data.get(key, []), ensure_ascii=False) for key in ("pain_points", "competitors", "ui_ux_gaps")}
    values = {**serialized, "voice_agent_necessity": profile_data["voice_agent_necessity"], "branding_vibe": profile_data["branding_vibe"], "is_responsive_missing": profile_data.get("is_responsive_missing", False), "lacks_interactive_ai": profile_data.get("lacks_interactive_ai", True)}
    async with async_session() as session:
        row = await session.get(EnrichedProfileTable, profile_data["lead_id"])
        if row:
            for key, value in values.items():
                setattr(row, key, value)
        else:
            session.add(EnrichedProfileTable(lead_id=profile_data["lead_id"], **values))
        await session.commit()


async def add_workflow_log(lead_id: Optional[str], node_name: str, message: str) -> None:
    async with async_session() as session:
        session.add(WorkflowLogTable(lead_id=lead_id, node_name=node_name, log_message=message))
        await session.commit()


async def create_campaign(payload: CampaignCreate) -> str:
    task_count = payload.scrape_job_count
    if task_count > settings.max_campaign_tasks:
        raise ValueError(f"Campaign has {task_count} keyword jobs; maximum is {settings.max_campaign_tasks}")
    campaign_id = str(uuid.uuid4())
    async with async_session() as session:
        session.add(CampaignTable(id=campaign_id, name=payload.name, provider=payload.provider, status="queued", configuration=payload.model_dump_json(), outreach_approved=payload.outreach_approved, total_tasks=task_count))
        position = 0
        for location in payload.locations:
            for niche in payload.niches:
                for keyword in NICHES[niche].search_terms:
                    position += 1
                    session.add(
                        ScrapeJobTable(
                            id=str(uuid.uuid4()), campaign_id=campaign_id, niche=niche,
                            keyword=keyword, location=location.label, city=location.city,
                            state=location.state, country=location.country, position=position,
                            status="queued",
                        )
                    )
        await session.commit()
    return campaign_id


async def ensure_scrape_jobs(campaign_id: str, payload: CampaignCreate) -> int:
    """Upgrade a pre-v3 campaign lazily without destructive database migration."""

    async with async_session() as session:
        existing_count = (
            await session.execute(
                select(func.count()).select_from(ScrapeJobTable).where(ScrapeJobTable.campaign_id == campaign_id)
            )
        ).scalar_one()
        if existing_count:
            return existing_count
        position = 0
        for location in payload.locations:
            for niche in payload.niches:
                for keyword in NICHES[niche].search_terms:
                    position += 1
                    session.add(
                        ScrapeJobTable(
                            id=str(uuid.uuid4()), campaign_id=campaign_id, niche=niche,
                            keyword=keyword, location=location.label, city=location.city,
                            state=location.state, country=location.country, position=position,
                            status="queued",
                        )
                    )
        await session.execute(
            update(CampaignTable).where(CampaignTable.id == campaign_id).values(
                total_tasks=position, completed_tasks=0, error_message=None, updated_at=utcnow()
            )
        )
        await session.commit()
        return position


def _campaign_dict(row: CampaignTable) -> Dict[str, Any]:
    return {"id": row.id, "name": row.name, "provider": row.provider, "status": row.status, "configuration": json.loads(row.configuration), "outreach_approved": row.outreach_approved, "total_tasks": row.total_tasks, "completed_tasks": row.completed_tasks, "leads_processed": row.leads_processed, "sites_generated": row.sites_generated, "drafts_prepared": row.drafts_prepared, "sent_count": row.sent_count, "stop_requested": row.stop_requested, "error_message": row.error_message, "created_at": row.created_at.isoformat() if row.created_at else None, "updated_at": row.updated_at.isoformat() if row.updated_at else None}


async def get_campaign(campaign_id: str) -> Optional[Dict[str, Any]]:
    async with async_session() as session:
        row = await session.get(CampaignTable, campaign_id)
        return _campaign_dict(row) if row else None


async def list_campaigns(limit: int = 50) -> List[Dict[str, Any]]:
    async with async_session() as session:
        rows = (await session.execute(select(CampaignTable).order_by(CampaignTable.created_at.desc()).limit(limit))).scalars().all()
        return [_campaign_dict(row) for row in rows]


async def update_campaign(campaign_id: str, **values: Any) -> None:
    values["updated_at"] = utcnow()
    async with async_session() as session:
        await session.execute(update(CampaignTable).where(CampaignTable.id == campaign_id).values(**values))
        await session.commit()


async def increment_campaign(campaign_id: str, field: str, amount: int = 1) -> None:
    allowed = {"completed_tasks", "leads_processed", "sites_generated", "drafts_prepared", "sent_count"}
    if field not in allowed:
        raise ValueError("Unsupported campaign counter")
    column = getattr(CampaignTable, field)
    async with async_session() as session:
        await session.execute(update(CampaignTable).where(CampaignTable.id == campaign_id).values({field: column + amount, "updated_at": utcnow()}))
        await session.commit()


async def next_campaign_task(campaign_id: str) -> Optional[Dict[str, Any]]:
    async with async_session() as session:
        row = (await session.execute(select(CampaignTaskTable).where(CampaignTaskTable.campaign_id == campaign_id, CampaignTaskTable.status.in_(["queued", "failed"]), CampaignTaskTable.attempt_count < 3).order_by(CampaignTaskTable.id).limit(1))).scalars().first()
        return {"id": row.id, "niche": row.niche, "location": row.location, "attempt_count": row.attempt_count} if row else None


async def update_campaign_task(task_id: str, status: str, **values: Any) -> None:
    values["status"] = status
    if status == "running":
        values.update(started_at=utcnow(), attempt_count=CampaignTaskTable.attempt_count + 1)
    if status in {"completed", "failed"}:
        values["completed_at"] = utcnow()
    async with async_session() as session:
        await session.execute(update(CampaignTaskTable).where(CampaignTaskTable.id == task_id).values(**values))
        await session.commit()


async def next_scrape_job(campaign_id: str) -> Optional[Dict[str, Any]]:
    async with async_session() as session:
        row = (
            await session.execute(
                select(ScrapeJobTable)
                .where(
                    ScrapeJobTable.campaign_id == campaign_id,
                    ScrapeJobTable.status.in_(["queued", "failed"]),
                    ScrapeJobTable.attempt_count < 3,
                )
                .order_by(ScrapeJobTable.position)
                .limit(1)
            )
        ).scalars().first()
        if not row:
            return None
        return {
            "id": row.id, "niche": row.niche, "keyword": row.keyword,
            "location": row.location, "city": row.city, "state": row.state,
            "country": row.country, "position": row.position, "attempt_count": row.attempt_count,
        }


async def update_scrape_job(job_id: str, status: str, **values: Any) -> None:
    values["status"] = status
    if status == "running":
        values.update(started_at=utcnow(), attempt_count=ScrapeJobTable.attempt_count + 1)
    if status in {"completed", "failed"}:
        values["completed_at"] = utcnow()
    async with async_session() as session:
        await session.execute(update(ScrapeJobTable).where(ScrapeJobTable.id == job_id).values(**values))
        await session.commit()


async def list_scrape_jobs(campaign_id: str, limit: int = 5000) -> List[Dict[str, Any]]:
    async with async_session() as session:
        rows = (
            await session.execute(
                select(ScrapeJobTable)
                .where(ScrapeJobTable.campaign_id == campaign_id)
                .order_by(ScrapeJobTable.position)
                .limit(limit)
            )
        ).scalars().all()
        return [
            {
                "id": row.id, "niche": row.niche, "keyword": row.keyword,
                "location": row.location, "city": row.city, "state": row.state,
                "country": row.country, "position": row.position, "status": row.status,
                "attempt_count": row.attempt_count, "result_count": row.result_count,
                "error_message": row.error_message,
            }
            for row in rows
        ]


async def attach_lead_to_campaign(campaign_id: str, lead_id: str) -> bool:
    async with async_session() as session:
        exists = (await session.execute(select(CampaignLeadTable.id).where(CampaignLeadTable.campaign_id == campaign_id, CampaignLeadTable.lead_id == lead_id))).scalar_one_or_none()
        if exists:
            return False
        session.add(CampaignLeadTable(campaign_id=campaign_id, lead_id=lead_id))
        await session.commit()
        return True


async def record_lead_discovery(campaign_id: str, lead_id: str, discovery: Dict[str, Any]) -> bool:
    values = {
        "campaign_id": campaign_id, "lead_id": lead_id,
        "provider": discovery["source"], "niche": discovery["niche"],
        "keyword": discovery.get("found_via_keyword") or discovery["niche"],
        "location": discovery["location"], "city": discovery.get("city") or discovery["location"].split(",")[0],
        "state": discovery.get("state") or "Unknown", "country": discovery.get("country") or "India",
    }
    async with async_session() as session:
        exists = (
            await session.execute(
                select(LeadDiscoveryTable.id).where(
                    LeadDiscoveryTable.campaign_id == campaign_id,
                    LeadDiscoveryTable.lead_id == lead_id,
                    LeadDiscoveryTable.niche == values["niche"],
                    LeadDiscoveryTable.keyword == values["keyword"],
                    LeadDiscoveryTable.location == values["location"],
                )
            )
        ).scalar_one_or_none()
        if exists:
            return False
        session.add(LeadDiscoveryTable(**values))
        await session.commit()
        return True


async def save_outreach_draft(campaign_id: str, lead_id: str, subject: str, email_body: str, whatsapp_body: str) -> str:
    async with async_session() as session:
        row = (await session.execute(select(OutreachDraftTable).where(OutreachDraftTable.campaign_id == campaign_id, OutreachDraftTable.lead_id == lead_id))).scalars().first()
        if row:
            row.subject, row.email_body, row.whatsapp_body = subject, email_body, whatsapp_body
            draft_id = row.id
        else:
            draft_id = str(uuid.uuid4())
            session.add(OutreachDraftTable(id=draft_id, campaign_id=campaign_id, lead_id=lead_id, subject=subject, email_body=email_body, whatsapp_body=whatsapp_body))
        await session.commit()
        return draft_id


async def update_outreach_draft(draft_id: str, status: str, note: str = "") -> None:
    values: Dict[str, Any] = {"status": status, "delivery_note": note}
    if status == "sent":
        values["sent_at"] = utcnow()
    async with async_session() as session:
        await session.execute(update(OutreachDraftTable).where(OutreachDraftTable.id == draft_id).values(**values))
        await session.commit()


async def add_campaign_log(campaign_id: str, stage: str, message: str, lead_id: Optional[str] = None, level: str = "info") -> None:
    async with async_session() as session:
        session.add(CampaignLogTable(campaign_id=campaign_id, lead_id=lead_id, stage=stage, level=level, message=message))
        await session.commit()


async def list_campaign_logs(campaign_id: str, limit: int = 300) -> List[Dict[str, Any]]:
    async with async_session() as session:
        rows = (await session.execute(select(CampaignLogTable).where(CampaignLogTable.campaign_id == campaign_id).order_by(CampaignLogTable.id.desc()).limit(limit))).scalars().all()
        return [{"id": row.id, "lead_id": row.lead_id, "stage": row.stage, "level": row.level, "message": row.message, "created_at": row.created_at.isoformat()} for row in reversed(rows)]


async def is_do_not_contact(email: Optional[str], phone: Optional[str]) -> bool:
    checks = [("email", email.lower())] if email else []
    if phone:
        checks.append(("phone", "".join(ch for ch in phone if ch.isdigit() or ch == "+")))
    async with async_session() as session:
        for kind, value in checks:
            if (await session.execute(select(DoNotContactTable.id).where(DoNotContactTable.kind == kind, DoNotContactTable.value == value))).scalar_one_or_none():
                return True
    return False


async def list_leads(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    async with async_session() as session:
        latest_discovery = (
            select(LeadDiscoveryTable.lead_id, func.max(LeadDiscoveryTable.id).label("discovery_id"))
            .group_by(LeadDiscoveryTable.lead_id)
            .subquery()
        )
        rows = (
            await session.execute(
                select(LeadTable, LeadSourceTable, LeadDiscoveryTable)
                .select_from(LeadTable)
                .outerjoin(LeadSourceTable, LeadSourceTable.lead_id == LeadTable.id)
                .outerjoin(latest_discovery, latest_discovery.c.lead_id == LeadTable.id)
                .outerjoin(LeadDiscoveryTable, LeadDiscoveryTable.id == latest_discovery.c.discovery_id)
                .order_by(LeadTable.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
        ).all()
        output: List[Dict[str, Any]] = []
        for lead, source, discovery in rows:
            quality = (
                (30 if lead.phone else 0) + (15 if lead.email else 0) + (20 if lead.website else 0)
                + (10 if source and source.formatted_address else 0) + (10 if source and source.rating else 0)
                + (10 if source and source.review_count else 0) + (5 if source and source.google_maps_uri else 0)
            )
            output.append({
                "id": lead.id, "name": lead.name, "phone": lead.phone, "email": lead.email,
                "website": lead.website, "niche": discovery.niche if discovery else lead.niche,
                "location": discovery.location if discovery else lead.location, "status": lead.status,
                "source": source.provider if source else None,
                "formatted_address": source.formatted_address if source else None,
                "google_maps_uri": source.google_maps_uri if source else None,
                "rating": float(source.rating) if source and source.rating else None,
                "review_count": source.review_count if source else None,
                "found_via_keyword": discovery.keyword if discovery else None,
                "city": discovery.city if discovery else None, "state": discovery.state if discovery else None,
                "country": discovery.country if discovery else None, "data_quality_score": quality,
                "created_at": lead.created_at.isoformat() if lead.created_at else None,
            })
        return output


async def campaign_export_rows(campaign_id: str) -> List[Dict[str, Any]]:
    """Return one deduplicated, Excel-friendly row per campaign business."""

    async with async_session() as session:
        lead_rows = (
            await session.execute(
                select(LeadTable, LeadSourceTable)
                .select_from(CampaignLeadTable)
                .join(LeadTable, LeadTable.id == CampaignLeadTable.lead_id)
                .outerjoin(LeadSourceTable, LeadSourceTable.lead_id == LeadTable.id)
                .where(CampaignLeadTable.campaign_id == campaign_id)
                .order_by(LeadTable.name)
            )
        ).all()
        discovery_rows = (
            await session.execute(
                select(LeadDiscoveryTable).where(LeadDiscoveryTable.campaign_id == campaign_id)
            )
        ).scalars().all()

    discoveries: Dict[str, List[LeadDiscoveryTable]] = {}
    for row in discovery_rows:
        discoveries.setdefault(row.lead_id, []).append(row)

    output: List[Dict[str, Any]] = []
    for lead, source in lead_rows:
        matches = discoveries.get(lead.id, [])
        niches = sorted({item.niche for item in matches}) or [lead.niche]
        keywords = sorted({item.keyword for item in matches})
        cities = sorted({item.city for item in matches})
        states = sorted({item.state for item in matches})
        countries = sorted({item.country for item in matches})
        quality = (
            (30 if lead.phone else 0) + (15 if lead.email else 0) + (20 if lead.website else 0)
            + (10 if source and source.formatted_address else 0) + (10 if source and source.rating else 0)
            + (10 if source and source.review_count else 0) + (5 if source and source.google_maps_uri else 0)
        )
        output.append({
            "Business Name": lead.name, "Category": ", ".join(niches), "Phone": lead.phone or "",
            "Email": lead.email or "", "Website": lead.website or "",
            "Address": source.formatted_address if source else "",
            "Rating": source.rating if source and source.rating else "",
            "Reviews": source.review_count if source and source.review_count is not None else "",
            "City": ", ".join(cities), "State": ", ".join(states),
            "Country": ", ".join(countries), "Found Via Keyword": ", ".join(keywords),
            "Google Maps Link": source.google_maps_uri if source else "",
            "Source": source.provider if source else "", "Status": lead.status,
            "Data Quality Score": quality,
        })
    return output


async def dashboard_stats() -> Dict[str, int]:
    async with async_session() as session:
        leads = (await session.execute(select(func.count()).select_from(LeadTable))).scalar_one()
        profiles = (await session.execute(select(func.count()).select_from(EnrichedProfileTable))).scalar_one()
        campaigns = (await session.execute(select(func.count()).select_from(CampaignTable))).scalar_one()
        drafts = (await session.execute(select(func.count()).select_from(OutreachDraftTable))).scalar_one()
        sent = (await session.execute(select(func.count()).select_from(OutreachDraftTable).where(OutreachDraftTable.status == "sent"))).scalar_one()
        return {"leads": leads, "profiles": profiles, "campaigns": campaigns, "drafts": drafts, "sent": sent}


async def get_lead(lead_id: str) -> Optional[Dict[str, Any]]:
    async with async_session() as session:
        lead = await session.get(LeadTable, lead_id)
        if not lead:
            return None
        return {"id": lead.id, "name": lead.name, "phone": lead.phone, "email": lead.email, "website": lead.website, "niche": lead.niche, "location": lead.location, "status": lead.status, "created_at": lead.created_at.isoformat() if lead.created_at else None}


async def get_enriched_profile(lead_id: str) -> Optional[Dict[str, Any]]:
    async with async_session() as session:
        row = await session.get(EnrichedProfileTable, lead_id)
        if not row:
            return None
        return {"lead_id": row.lead_id, "pain_points": json.loads(row.pain_points), "voice_agent_necessity": row.voice_agent_necessity, "branding_vibe": row.branding_vibe, "competitors": json.loads(row.competitors), "ui_ux_gaps": json.loads(row.ui_ux_gaps), "is_responsive_missing": row.is_responsive_missing, "lacks_interactive_ai": row.lacks_interactive_ai}


async def get_all_leads_by_niche_and_location(niche: str, location: str) -> List[Dict[str, Any]]:
    return [row for row in await list_leads(limit=10000) if row["niche"] == niche and row["location"] == location]
