"""GPT-5.6 Sol client for analysis, offer design, pages and outreach drafts."""

from __future__ import annotations

import html
import json
import logging
import re
from typing import Any, Dict

import httpx
from bs4 import BeautifulSoup

from backend.config import EnrichedBusinessProfile, LeadModel, NICHES, settings

logger = logging.getLogger("OpenAIStudio")


PROFILE_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "pain_points": {"type": "array", "items": {"type": "string"}, "minItems": 3, "maxItems": 5},
        "voice_agent_necessity": {"type": "string"},
        "branding_vibe": {"type": "string"},
        "ui_ux_gaps": {"type": "array", "items": {"type": "string"}, "maxItems": 5},
        "is_responsive_missing": {"type": "boolean"},
        "lacks_interactive_ai": {"type": "boolean"},
        "recommended_offer": {"type": "string"},
        "outreach_angle": {"type": "string"},
    },
    "required": ["pain_points", "voice_agent_necessity", "branding_vibe", "ui_ux_gaps", "is_responsive_missing", "lacks_interactive_ai", "recommended_offer", "outreach_angle"],
}

OUTREACH_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "subject": {"type": "string"},
        "email_body": {"type": "string"},
        "whatsapp_body": {"type": "string"},
    },
    "required": ["subject", "email_body", "whatsapp_body"],
}


class OpenAIStudioClient:
    endpoint = "https://api.openai.com/v1/responses"

    def __init__(self, api_key: str = settings.openai_api_key, model: str = settings.openai_model):
        self.api_key = api_key
        self.model = model

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    @staticmethod
    def _output_text(payload: Dict[str, Any]) -> str:
        if payload.get("output_text"):
            return payload["output_text"]
        parts = []
        for item in payload.get("output", []):
            if item.get("type") != "message":
                continue
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    parts.append(content.get("text", ""))
        return "".join(parts)

    async def _respond(self, developer: str, user: str, *, schema: Dict[str, Any] | None = None, schema_name: str = "result", verbosity: str = "medium", max_output_tokens: int = 4000) -> str:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        text_config: Dict[str, Any] = {"verbosity": verbosity}
        if schema:
            text_config["format"] = {"type": "json_schema", "name": schema_name, "strict": True, "schema": schema}
        body = {
            "model": self.model,
            "input": [
                {"role": "developer", "content": [{"type": "input_text", "text": developer}]},
                {"role": "user", "content": [{"type": "input_text", "text": user}]},
            ],
            "reasoning": {"effort": settings.openai_reasoning_effort},
            "text": text_config,
            "max_output_tokens": max_output_tokens,
            "store": False,
            "safety_identifier": "cinemaos-opc-automation",
        }
        async with httpx.AsyncClient(timeout=settings.openai_timeout_seconds) as client:
            response = await client.post(self.endpoint, headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}, json=body)
            response.raise_for_status()
            text = self._output_text(response.json()).strip()
            if not text:
                raise RuntimeError("OpenAI returned an empty response")
            return text

    async def analyze_business(self, lead: LeadModel, website_summary: Dict[str, Any]) -> EnrichedBusinessProfile:
        niche = NICHES[lead.niche]
        if not self.configured:
            return EnrichedBusinessProfile(
                lead_id=lead.id,
                pain_points=niche.pain_points[:3],
                voice_agent_necessity="A fast response and booking assistant can capture inquiries when staff are unavailable.",
                branding_vibe="A clear, trustworthy mobile-first design using restrained colours and strong calls to action.",
                ui_ux_gaps=website_summary.get("ui_ux_gaps", ["Website was not available for a detailed audit"]),
                is_responsive_missing=website_summary.get("is_responsive_missing", False),
                lacks_interactive_ai=website_summary.get("lacks_interactive_ai", True),
                recommended_offer=niche.core_solutions[0],
                outreach_angle=f"Show how {niche.core_solutions[0].lower()} can reduce response delay.",
            )
        developer = "You are a cautious Indian B2B growth analyst. Use only supplied evidence. Never invent revenue figures, legal compliance, product capabilities, or competitor facts. Return the requested JSON."
        user = json.dumps({"business": lead.model_dump(), "website_observations": website_summary, "niche_baseline": niche.model_dump()}, ensure_ascii=False)
        data = json.loads(await self._respond(developer, user, schema=PROFILE_SCHEMA, schema_name="business_profile", verbosity="low", max_output_tokens=2500))
        return EnrichedBusinessProfile(lead_id=lead.id, competitors=[], **data)

    async def draft_outreach(self, lead: LeadModel, profile: EnrichedBusinessProfile, preview_url: str) -> Dict[str, str]:
        if not self.configured:
            pain = profile.pain_points[0] if profile.pain_points else "slow inquiry response"
            return {
                "subject": f"A practical improvement idea for {lead.name}",
                "email_body": f"Hello {lead.name} team,\n\nI reviewed your public business presence and prepared a short concept showing one way to improve {pain.lower()}.\n\nPreview: {preview_url}\n\nIf this is relevant, reply and I will share the assumptions behind it. If you do not want further messages, reply STOP.\n\nCinemaOS OPC",
                "whatsapp_body": f"Hello {lead.name}. I prepared a concept for improving {pain.lower()}: {preview_url}\nReply YES for details or STOP to opt out.",
            }
        developer = "Draft respectful, evidence-based B2B outreach for India. Do not claim deployment, guaranteed revenue, hidden audits, or capabilities not in the input. Include a clear opt-out. Keep email under 170 words and WhatsApp under 500 characters. Return JSON."
        user = json.dumps({"lead": lead.model_dump(), "profile": profile.model_dump(), "preview_url": preview_url}, ensure_ascii=False)
        return json.loads(await self._respond(developer, user, schema=OUTREACH_SCHEMA, schema_name="outreach_draft", verbosity="low", max_output_tokens=1500))

    async def generate_page(self, lead: LeadModel, profile: EnrichedBusinessProfile) -> str:
        if not self.configured:
            return fallback_page(lead, profile)
        developer = "Create a polished, accessible single-file HTML business concept page. Output raw HTML only. Use inline CSS; do not use scripts, external assets, forms that submit data, tracking, or unsupported claims. Make it responsive and clearly label it as a private concept preview."
        user = json.dumps({"lead": lead.model_dump(), "analysis": profile.model_dump(), "offer_options": NICHES[lead.niche].core_solutions}, ensure_ascii=False)
        raw = await self._respond(developer, user, verbosity="high", max_output_tokens=9000)
        raw = re.sub(r"^```(?:html)?\s*|\s*```$", "", raw.strip(), flags=re.IGNORECASE)
        return sanitize_generated_html(raw)


def sanitize_generated_html(raw: str) -> str:
    soup = BeautifulSoup(raw, "html.parser")
    for tag in soup.find_all(["script", "iframe", "object", "embed"]):
        tag.decompose()
    for tag in soup.find_all(True):
        for attr in list(tag.attrs):
            if attr.lower().startswith("on") or attr.lower() in {"srcdoc", "formaction"}:
                del tag.attrs[attr]
        if tag.name == "form":
            tag.attrs.pop("action", None)
            tag.attrs.pop("method", None)
    text = str(soup)
    if "<html" not in text.lower():
        raise ValueError("Generated page did not contain an HTML document")
    return text


def fallback_page(lead: LeadModel, profile: EnrichedBusinessProfile) -> str:
    name = html.escape(lead.name)
    niche = html.escape(lead.niche)
    location = html.escape(lead.location)
    pain_items = "".join(f"<li>{html.escape(item)}</li>" for item in profile.pain_points)
    offer = html.escape(profile.recommended_offer or NICHES[lead.niche].core_solutions[0])
    return f"""<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>{name} concept</title><style>*{{box-sizing:border-box}}body{{margin:0;font-family:Inter,system-ui,sans-serif;background:#07111f;color:#edf4ff}}main{{max-width:980px;margin:auto;padding:72px 24px}}.tag{{color:#8dd7ff;text-transform:uppercase;letter-spacing:.14em;font-size:12px}}h1{{font-size:clamp(42px,8vw,78px);line-height:1;margin:.25em 0}}p,li{{color:#b8c7dc;line-height:1.7}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:20px;margin-top:42px}}.card{{padding:26px;border:1px solid #233650;border-radius:22px;background:#0d1a2c}}.cta{{display:inline-block;margin-top:24px;padding:14px 20px;border-radius:12px;background:#4f7cff;color:white;font-weight:700}}footer{{margin-top:64px;color:#6f829c;font-size:13px}}</style></head><body><main><div class=\"tag\">Private concept preview · {niche} · {location}</div><h1>A faster inquiry journey for {name}</h1><p>This concept shows how a clearer digital experience could help customers understand services and request the next step.</p><div class=\"grid\"><section class=\"card\"><h2>Opportunities to review</h2><ul>{pain_items}</ul></section><section class=\"card\"><h2>Suggested first offer</h2><p>{offer}</p><span class=\"cta\">Request a human review</span></section></div><footer>Concept prepared by CinemaOS OPC. This is a demonstration, not the official website of {name}.</footer></main></body></html>"""
