"""Safe local concept-page generation powered by GPT-5.6 Sol or fallback HTML."""

from __future__ import annotations

import os
import re
from pathlib import Path

from backend.ai import OpenAIStudioClient
from backend.config import EnrichedBusinessProfile, LeadModel


class ProgrammaticSiteGenerator:
    def __init__(self, ai: OpenAIStudioClient | None = None, agency_name: str = "CinemaOS OPC"):
        self.ai = ai or OpenAIStudioClient()
        self.agency_name = agency_name
        self.builds_dir = Path(__file__).resolve().parent / "builds"
        self.builds_dir.mkdir(parents=True, exist_ok=True)

    async def generate_site(self, lead: LeadModel, profile: EnrichedBusinessProfile) -> str:
        safe_id = re.sub(r"[^a-zA-Z0-9_-]", "", lead.id)
        if not safe_id:
            raise ValueError("Lead ID is not safe for a build path")
        build_dir = (self.builds_dir / safe_id).resolve()
        if self.builds_dir.resolve() not in build_dir.parents:
            raise ValueError("Build path escaped the build directory")
        build_dir.mkdir(parents=True, exist_ok=True)
        html_code = await self.ai.generate_page(lead, profile)
        target = build_dir / "index.html"
        temporary = build_dir / "index.html.tmp"
        temporary.write_text(html_code, encoding="utf-8")
        os.replace(temporary, target)
        return f"/previews/{safe_id}/index.html"
