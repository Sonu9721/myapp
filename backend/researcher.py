"""Evidence-based public website audit followed by GPT-5.6 Sol analysis."""

from __future__ import annotations

from typing import Any, Dict, List
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from backend.ai import OpenAIStudioClient
from backend.config import EnrichedBusinessProfile, LeadModel, settings
from backend.scraper import _is_public_hostname


class BusinessAuditor:
    def __init__(self, ai: OpenAIStudioClient | None = None):
        self.ai = ai or OpenAIStudioClient()

    async def inspect_website(self, url: str | None) -> Dict[str, Any]:
        if not url:
            return {"available": False, "ui_ux_gaps": ["No business website was supplied"], "is_responsive_missing": False, "lacks_interactive_ai": True}
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or not await _is_public_hostname(parsed.hostname):
            return {"available": False, "ui_ux_gaps": ["Website URL could not be safely inspected"], "is_responsive_missing": False, "lacks_interactive_ai": True}
        try:
            async with httpx.AsyncClient(timeout=settings.website_timeout_seconds, follow_redirects=True, headers={"User-Agent": "CinemaOSBusinessResearch/1.0"}) as client:
                response = await client.get(url)
                response.raise_for_status()
                if "text/html" not in response.headers.get("content-type", ""):
                    return {"available": True, "ui_ux_gaps": ["Homepage is not an HTML page"], "is_responsive_missing": False, "lacks_interactive_ai": True}
                soup = BeautifulSoup(response.text[:1_000_000], "html.parser")
        except httpx.HTTPError as exc:
            return {"available": False, "ui_ux_gaps": [f"Website request failed: {type(exc).__name__}"], "is_responsive_missing": False, "lacks_interactive_ai": True}

        title = soup.title.get_text(" ", strip=True)[:200] if soup.title else ""
        meta_description = ""
        meta = soup.find("meta", attrs={"name": "description"})
        if meta:
            meta_description = str(meta.get("content", ""))[:500]
        viewport_missing = soup.find("meta", attrs={"name": "viewport"}) is None
        text = soup.get_text(" ", strip=True).lower()
        has_contact_link = bool(soup.select('a[href^="tel:"], a[href^="mailto:"], a[href*="contact"], a[href*="book"]'))
        has_form = soup.find("form") is not None
        has_chat_signal = any(term in text for term in ("chat with us", "live chat", "chatbot", "whatsapp us"))
        gaps: List[str] = []
        if viewport_missing:
            gaps.append("No mobile viewport declaration was detected")
        if not has_contact_link:
            gaps.append("No obvious call, email, booking or contact link was detected")
        if not has_form:
            gaps.append("No inquiry form was detected on the homepage")
        if not title or not meta_description:
            gaps.append("Search title or meta description appears incomplete")
        return {
            "available": True,
            "title": title,
            "meta_description": meta_description,
            "ui_ux_gaps": gaps,
            "is_responsive_missing": viewport_missing,
            "lacks_interactive_ai": not has_chat_signal,
            "has_contact_link": has_contact_link,
            "has_form": has_form,
        }

    async def audit_single_business(self, lead: LeadModel) -> EnrichedBusinessProfile:
        evidence = await self.inspect_website(lead.website)
        return await self.ai.analyze_business(lead, evidence)

    async def execute_parallel_audit(self, leads: List[LeadModel]) -> List[EnrichedBusinessProfile]:
        # Campaign-level concurrency is bounded by the orchestrator.
        return [await self.audit_single_business(lead) for lead in leads]
