"""Authorized business discovery providers and public website contact enrichment."""

from __future__ import annotations

import asyncio
import ipaddress
import logging
import re
import socket
import uuid
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from backend.config import DiscoveredLead, NICHES, settings

logger = logging.getLogger("BusinessDiscovery")


class BaseLeadScraper(ABC):
    @abstractmethod
    async def scrape(
        self, niche: str, location: str, limit: int = 10, keyword: Optional[str] = None
    ) -> List[DiscoveredLead]:
        raise NotImplementedError


def normalize_phone(value: Optional[str], default_country_code: str = "91") -> Optional[str]:
    """Return a conservative E.164-style number or None for unusable values."""

    if not value:
        return None
    raw = value.strip()
    digits = re.sub(r"\D", "", raw)
    if digits.startswith("00"):
        digits = digits[2:]
    if len(digits) == 11 and digits.startswith("0"):
        digits = default_country_code + digits[1:]
    elif len(digits) == 10:
        digits = default_country_code + digits
    elif raw.startswith("+"):
        pass
    elif len(digits) == 12 and digits.startswith(default_country_code):
        pass
    if not 8 <= len(digits) <= 15:
        return None
    return f"+{digits}"


class GooglePlacesLeadScraper(BaseLeadScraper):
    """Uses Google Places Text Search (New); it never scrapes Google result pages."""

    endpoint = "https://places.googleapis.com/v1/places:searchText"
    field_mask = ",".join(
        [
            "places.id", "places.displayName", "places.formattedAddress",
            "places.nationalPhoneNumber", "places.internationalPhoneNumber",
            "places.websiteUri", "places.googleMapsUri", "places.primaryType",
            "places.businessStatus", "places.rating", "places.userRatingCount",
            "nextPageToken",
        ]
    )

    def __init__(self, api_key: str = settings.google_places_api_key):
        self.api_key = api_key

    async def scrape(
        self, niche: str, location: str, limit: int = 10, keyword: Optional[str] = None
    ) -> List[DiscoveredLead]:
        if not self.api_key:
            raise RuntimeError("GOOGLE_PLACES_API_KEY is required for google_places campaigns")
        if niche not in NICHES:
            raise ValueError(f"Unsupported niche: {niche}")

        safe_limit = min(max(1, limit), 60, settings.max_results_per_query)
        results: List[DiscoveredLead] = []
        seen: Set[str] = set()
        terms = [keyword] if keyword else NICHES[niche].search_terms
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            for term in terms:
                page_token: Optional[str] = None
                while len(results) < safe_limit:
                    body: Dict[str, object] = {
                        "textQuery": f"{term} in {location}",
                        "pageSize": min(20, safe_limit - len(results)),
                        "languageCode": settings.google_places_language,
                        "regionCode": settings.google_places_region,
                        "includePureServiceAreaBusinesses": True,
                    }
                    if page_token:
                        body["pageToken"] = page_token
                    response: Optional[httpx.Response] = None
                    for attempt in range(5):
                        response = await client.post(
                            self.endpoint,
                            json=body,
                            headers={
                                "Content-Type": "application/json",
                                "X-Goog-Api-Key": self.api_key,
                                "X-Goog-FieldMask": self.field_mask,
                            },
                        )
                        if response.status_code not in {429, 500, 502, 503, 504}:
                            break
                        retry_after = response.headers.get("retry-after")
                        delay = float(retry_after) if retry_after and retry_after.isdigit() else 0.5 * (2**attempt)
                        await asyncio.sleep(min(delay, 8.0))
                    assert response is not None
                    response.raise_for_status()
                    payload = response.json()
                    for place in payload.get("places", []):
                        external_id = place.get("id")
                        if not external_id or external_id in seen:
                            continue
                        seen.add(external_id)
                        display = place.get("displayName") or {}
                        lead_id = "lead_" + uuid.uuid5(uuid.NAMESPACE_URL, f"google_places:{external_id}").hex[:20]
                        results.append(
                            DiscoveredLead(
                                id=lead_id,
                                source="google_places",
                                source_id=external_id,
                                name=display.get("text") or "Unnamed business",
                                phone=normalize_phone(place.get("internationalPhoneNumber") or place.get("nationalPhoneNumber")),
                                website=place.get("websiteUri"),
                                niche=niche,
                                location=location,
                                formatted_address=place.get("formattedAddress"),
                                google_maps_uri=place.get("googleMapsUri"),
                                primary_type=place.get("primaryType"),
                                business_status=place.get("businessStatus"),
                                rating=place.get("rating"),
                                review_count=place.get("userRatingCount"),
                                found_via_keyword=term,
                                raw_snapshot=place,
                            )
                        )
                        if len(results) >= safe_limit:
                            break
                    page_token = payload.get("nextPageToken")
                    if not page_token or len(results) >= safe_limit:
                        break
                if len(results) >= safe_limit:
                    break
        return results


class MockLeadScraper(BaseLeadScraper):
    """Deterministic, non-deliverable records for development and tests."""

    async def scrape(
        self, niche: str, location: str, limit: int = 10, keyword: Optional[str] = None
    ) -> List[DiscoveredLead]:
        if niche not in NICHES:
            raise ValueError(f"Unsupported niche: {niche}")
        term = keyword or NICHES[niche].search_terms[0]
        names = [
            f"{location.split(',')[0]} {term.title()} Demo {index}"
            for index in range(1, min(limit, settings.max_results_per_query, 10) + 1)
        ]
        output: List[DiscoveredLead] = []
        for index, name in enumerate(names, 1):
            source_id = uuid.uuid5(uuid.NAMESPACE_URL, f"mock:{niche}:{location}:{term}:{index}").hex
            output.append(
                DiscoveredLead(
                    id="lead_" + source_id[:20], source="mock", source_id=source_id,
                    name=name, niche=niche, location=location, status="Discovered",
                    formatted_address=location, found_via_keyword=term,
                )
            )
        return output


async def _is_public_hostname(hostname: str) -> bool:
    if not hostname or hostname.lower() in {"localhost", "localhost.localdomain"}:
        return False
    try:
        loop = asyncio.get_running_loop()
        infos = await loop.run_in_executor(None, lambda: socket.getaddrinfo(hostname, None))
        addresses = {item[4][0] for item in infos}
        return bool(addresses) and all(not (ipaddress.ip_address(address).is_private or ipaddress.ip_address(address).is_loopback or ipaddress.ip_address(address).is_link_local or ipaddress.ip_address(address).is_reserved) for address in addresses)
    except (socket.gaierror, ValueError):
        return False


class WebsiteContactEnricher:
    """Finds a public business email from its own website, with SSRF and size limits."""

    email_pattern = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)

    async def find_public_email(self, website: Optional[str]) -> Optional[str]:
        if not website or not settings.website_enrichment_enabled:
            return None
        parsed = urlparse(website)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or not await _is_public_hostname(parsed.hostname):
            return None
        urls = [website, urljoin(website, "/contact"), urljoin(website, "/contact-us")]
        async with httpx.AsyncClient(timeout=settings.website_timeout_seconds, follow_redirects=True, headers={"User-Agent": "CinemaOSBusinessResearch/1.0"}) as client:
            for url in urls:
                try:
                    response = await client.get(url)
                    if response.status_code >= 400 or "text/html" not in response.headers.get("content-type", ""):
                        continue
                    text = response.text[:1_000_000]
                    soup = BeautifulSoup(text, "html.parser")
                    candidates = set(self.email_pattern.findall(soup.get_text(" ")))
                    for link in soup.select('a[href^="mailto:"]'):
                        candidates.add(link.get("href", "")[7:].split("?", 1)[0])
                    clean = sorted(email.lower().strip() for email in candidates if not email.lower().endswith((".png", ".jpg", ".jpeg", ".webp")))
                    if clean:
                        return clean[0]
                except (httpx.HTTPError, UnicodeError):
                    continue
        return None


# Kept as an import alias for older integrations; behavior now uses Google Places.
TavilyLeadScraper = GooglePlacesLeadScraper
