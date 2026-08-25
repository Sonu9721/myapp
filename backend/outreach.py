"""Draft-first outreach with explicit approval, opt-out and delivery safeguards."""

from __future__ import annotations

import asyncio
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict

import httpx

from backend.ai import OpenAIStudioClient
from backend.config import EnrichedBusinessProfile, LeadModel, settings
from backend.database import is_do_not_contact, save_outreach_draft, update_outreach_draft


class B2BOutreachEngine:
    def __init__(self, ai: OpenAIStudioClient | None = None, dry_run: bool | None = None):
        self.ai = ai or OpenAIStudioClient()
        self.force_dry_run = dry_run

    async def prepare(self, campaign_id: str, lead: LeadModel, profile: EnrichedBusinessProfile, preview_url: str) -> Dict[str, Any]:
        copy = await self.ai.draft_outreach(lead, profile, preview_url)
        draft_id = await save_outreach_draft(campaign_id, lead.id, copy["subject"], copy["email_body"], copy["whatsapp_body"])
        return {"id": draft_id, **copy}

    async def deliver(self, draft: Dict[str, Any], lead: LeadModel, campaign_approved: bool) -> Dict[str, Any]:
        if self.force_dry_run is True or settings.outreach_mode != "approved":
            return {"sent": False, "note": "Draft saved; OUTREACH_MODE is not approved"}
        if not campaign_approved:
            return {"sent": False, "note": "Draft saved; this campaign has no outreach approval"}
        if await is_do_not_contact(lead.email, lead.phone):
            await update_outreach_draft(draft["id"], "blocked", "Recipient is on the do-not-contact list")
            return {"sent": False, "note": "Recipient is on the do-not-contact list"}

        email_sent = await self._send_email(lead.email, draft["subject"], draft["email_body"]) if lead.email else False
        whatsapp_sent = await self._send_whatsapp(lead.phone, draft["whatsapp_body"]) if lead.phone else False
        sent = email_sent or whatsapp_sent
        note = f"email={email_sent}; whatsapp={whatsapp_sent}"
        await update_outreach_draft(draft["id"], "sent" if sent else "draft", note)
        return {"sent": sent, "note": note}

    async def execute_outreach_sequence(self, lead: LeadModel, profile: EnrichedBusinessProfile, preview_url: str, campaign_id: str = "legacy", campaign_approved: bool = False) -> Dict[str, Any]:
        draft = await self.prepare(campaign_id, lead, profile, preview_url)
        delivery = await self.deliver(draft, lead, campaign_approved)
        return {"email_dispatched": delivery["sent"], "whatsapp_dispatched": delivery["sent"], "lead_notified": delivery["sent"], "draft_id": draft["id"], "note": delivery["note"]}

    async def _send_email(self, recipient: str | None, subject: str, body: str) -> bool:
        if not recipient or not settings.smtp_user or not settings.smtp_password or not settings.default_from_email:
            return False
        message = MIMEMultipart()
        message["From"] = settings.default_from_email
        message["To"] = recipient
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain", "utf-8"))

        def send() -> None:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
                server.starttls()
                server.login(settings.smtp_user, settings.smtp_password)
                server.sendmail(settings.default_from_email, recipient, message.as_string())

        try:
            await asyncio.get_running_loop().run_in_executor(None, send)
            return True
        except (OSError, smtplib.SMTPException):
            return False

    async def _send_whatsapp(self, recipient: str | None, body: str) -> bool:
        if not recipient or not settings.twilio_account_sid or not settings.twilio_auth_token or not settings.twilio_phone_number:
            return False
        url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.twilio_account_sid}/Messages.json"
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(url, data={"From": f"whatsapp:{settings.twilio_phone_number}", "To": f"whatsapp:{recipient}", "Body": body}, auth=(settings.twilio_account_sid, settings.twilio_auth_token))
                return response.status_code in {200, 201}
        except httpx.HTTPError:
            return False
