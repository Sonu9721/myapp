import smtplib
import httpx
import logging
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any
from backend.config import (
    LeadModel, EnrichedBusinessProfile, NICHES,
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, DEFAULT_FROM_EMAIL,
    TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER
)

logger = logging.getLogger("OutreachEngine")

# =====================================================================
# Enterprise Outreach automation (Email SMTP & Twilio WhatsApp)
# =====================================================================

class B2BOutreachEngine:
    """Orchestrates high-converting B2B outreach across Email and WhatsApp platforms."""

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run

    def _compile_email_template(self, lead: LeadModel, profile: EnrichedBusinessProfile, preview_url: str) -> Dict[str, str]:
        """Generates dynamic subject lines and copy for cold emails based on niche leakage."""
        niche_data = NICHES.get(lead.niche)
        niche_label = lead.niche
        
        # Unbeatable, short, curiosity-driven subject lines by niche
        subject_lines = {
            "Doctors": f"Quick question about missed appointments at {lead.name}?",
            "Real Estate": f"Lead leakage alert for {lead.name}...",
            "Gyms": f"Quick question regarding member onboarding at {lead.name}?",
            "Cafes": f"Bypassing delivery commissions for {lead.name}?",
            "Boutiques": f"Abandoned shopping carts at {lead.name}?",
            "Law Firms": f"Emergency consultation intakes at {lead.name}?",
            "HVAC/Plumbing": f"Off-hours plumbing dispatch leak at {lead.name}?",
            "Salons": f"Filling empty styling seats at {lead.name}?",
            "Digital Creators": f"Strategic asset question for {lead.name}?",
            "Private Schools": f"Admissions drop-off warning at {lead.name}..."
        }
        
        subject = subject_lines.get(lead.niche, f"Revenue leakage notice: {lead.name}")
        
        # Primary operational leakage description
        primary_leak = profile.pain_points[0] if profile.pain_points else "missed operational inquiries"
        
        # Compile hyper-personalized body
        body = f"""Hi team at {lead.name},

I was auditing local {niche_label.lower()} businesses in {lead.location} and noticed a critical gap on your client onboarding systems. Specifically, we analyzed that {primary_leak.lower()} is directly bleeding inquiries straight into your local competitors.

Most agencies try to sell you more 'Time-for-Money' marketing setups. We don't. 

We transition local businesses into 'System-for-Revenue' assets by deploying autonomous, ultra-low latency AI Voice Representatives. 

Here is what we engineered for you:
- Powered by Llama 3.3 and Groq running 24/7/365 with perfect conversational memory.
- Seamlessly supports both customized natural Male and Female voice profiles.
- Integrated directly into a secure PostgreSQL backend to schedule appointments and qualify calls with zero lag.

We've actually deployed a fully functioning custom live preview for {lead.name} where you can test the AI Voice assistant yourself right now:
{preview_url}

Would you be open to a 10-minute demo to see how this completely plugs your leakage? Reply to this email and let me know.

Best regards,

Growth Architect
CinemaOS AI Agency
"Transitioning Businesses to System-for-Revenue Assets."
"""
        return {"subject": subject, "body": body}

    def _compile_whatsapp_template(self, lead: LeadModel, profile: EnrichedBusinessProfile, preview_url: str) -> str:
        """Generates concise, bolding-formatted WhatsApp outreach script optimized for mobile screens."""
        niche_data = NICHES.get(lead.niche)
        primary_leak = profile.pain_points[0] if profile.pain_points else "inbound lead drop-off"

        whatsapp_msg = (
            f"Hey! Mapped a critical inquiry leak at *{lead.name}*.\n\n"
            f"Specifically: *{primary_leak}* is routing high-value {lead.niche.lower()} clients directly to local competitors.\n\n"
            f"We've engineered an *Autonomous AI Voice Agent* (latency-free, Male/Female voice profiles, 24/7/365 operations with PostgreSQL memory) specifically to secure your bookings.\n\n"
            f"Check your *custom live preview* here:\n"
            f"{preview_url}\n\n"
            f"Reply *YES* to schedule a 10-minute demo call."
        )
        return whatsapp_msg

    async def send_email(self, recipient_email: str, subject: str, body: str) -> bool:
        """Triggers direct cold email delivery via SMTP."""
        if self.dry_run or not SMTP_USER or not SMTP_PASSWORD:
            logger.info(f"[DRY-RUN EMAIL] Sending to {recipient_email}:")
            logger.info(f"Subject: {subject}")
            logger.info(f"Body:\n{body}\n{'-'*40}")
            return True

        try:
            msg = MIMEMultipart()
            msg["From"] = DEFAULT_FROM_EMAIL
            msg["To"] = recipient_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            # Run in executor block to prevent blocking async event loop
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._smtp_send_sync, recipient_email, msg)
            logger.info(f"SMTP Cold Email successfully delivered to {recipient_email}")
            return True
        except Exception as e:
            logger.error(f"Failed SMTP delivery to {recipient_email}: {str(e)}")
            return False

    def _smtp_send_sync(self, recipient: str, msg: MIMEMultipart):
        """Synchronous SMTP worker."""
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(DEFAULT_FROM_EMAIL, recipient, msg.as_string())

    async def send_whatsapp(self, recipient_phone: str, message: str) -> bool:
        """Triggers WhatsApp delivery via Twilio API or Custom POST webhook."""
        if self.dry_run or not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
            logger.info(f"[DRY-RUN WHATSAPP] Sending to {recipient_phone}:")
            logger.info(f"Message:\n{message}\n{'-'*40}")
            return True

        try:
            twilio_url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
            auth = (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            
            # Format numbers correctly for Twilio WhatsApp
            payload = {
                "From": f"whatsapp:{TWILIO_PHONE_NUMBER}",
                "To": f"whatsapp:{recipient_phone}",
                "Body": message
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(twilio_url, data=payload, auth=auth)
                if response.status_code in [200, 201]:
                    logger.info(f"Twilio WhatsApp outreach successfully delivered to {recipient_phone}")
                    return True
                else:
                    logger.error(f"Twilio WhatsApp endpoint failed with status {response.status_code}: {response.text}")
                    return False
        except Exception as e:
            logger.error(f"Twilio WhatsApp outreach failed: {str(e)}")
            return False

    async def execute_outreach_sequence(self, lead: LeadModel, profile: EnrichedBusinessProfile, preview_url: str) -> Dict[str, Any]:
        """Assembles copy and dispatches outreach across Email and WhatsApp concurrently."""
        logger.info(f"Assembling outbound pitch stack for business: {lead.name}")
        
        email_pack = self._compile_email_template(lead, profile, preview_url)
        whatsapp_msg = self._compile_whatsapp_template(lead, profile, preview_url)

        # Trigger both channels concurrently
        email_task = self.send_email(lead.email or "leads@cinemaos.agency", email_pack["subject"], email_pack["body"])
        whatsapp_task = self.send_whatsapp(lead.phone or "+15550199", whatsapp_msg)
        
        email_success, whatsapp_success = await asyncio.gather(email_task, whatsapp_task)

        return {
            "email_dispatched": email_success,
            "whatsapp_dispatched": whatsapp_success,
            "lead_notified": email_success or whatsapp_success
        }
