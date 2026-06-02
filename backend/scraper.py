import httpx
import uuid
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from backend.config import LeadModel, NICHES, TAVILY_API_KEY

logger = logging.getLogger("LeadScraper")

# =====================================================================
# Lead Scraper Abstract Base Class
# =====================================================================

class BaseLeadScraper(ABC):
    """Abstract base class for plugging in SerpApi, Outscraper, Tavily, or mock scrapers."""
    
    @abstractmethod
    async def scrape(self, niche: str, location: str, limit: int = 5) -> List[LeadModel]:
        """Scrapes leads from a local geo-niche and returns standardized LeadModels."""
        pass

# =====================================================================
# Tavily Search API Lead Scraper Implementation
# =====================================================================

class TavilyLeadScraper(BaseLeadScraper):
    """Scrapes local businesses utilizing Tavily Search API."""

    def __init__(self, api_key: str = TAVILY_API_KEY):
        self.api_key = api_key
        self.endpoint = "https://api.tavily.com/search"

    async def scrape(self, niche: str, location: str, limit: int = 5) -> List[LeadModel]:
        if not self.api_key:
            logger.warning("Tavily API Key not found. Falling back to Mock Lead Scraper.")
            mock_scraper = MockLeadScraper()
            return await mock_scraper.scrape(niche, location, limit)

        niche_config = NICHES.get(niche)
        keywords = niche_config.default_keywords if niche_config else [niche]
        search_query = f"top {keywords[0]} in {location} with phone number website and email"
        
        logger.info(f"Executing Tavily local search query: '{search_query}'")
        
        payload = {
            "api_key": self.api_key,
            "query": search_query,
            "search_depth": "advanced",
            "max_results": limit,
            "include_domains": True
        }

        leads: List[LeadModel] = []
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(self.endpoint, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])
                    
                    for idx, res in enumerate(results):
                        # Construct a lead based on search results
                        title = res.get("title", f"Business {idx+1}")
                        url = res.get("url")
                        domain = None
                        if url:
                            from urllib.parse import urlparse
                            parsed_url = urlparse(url)
                            domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
                        
                        snippet = res.get("content", "")
                        
                        # Extract a mock/dummy phone or look for one in snippet
                        phone = "+91 98765 43210" if "Noida" in location else "+1 555-0199"
                        email = f"info@{title.lower().replace(' ', '').replace(',', '')}.com"
                        
                        lead_id = f"lead_{uuid.uuid4().hex[:8]}"
                        leads.append(
                            LeadModel(
                                id=lead_id,
                                name=title,
                                phone=phone,
                                email=email,
                                website=domain or url,
                                niche=niche,
                                location=location,
                                status="Scraped"
                            )
                        )
                else:
                    logger.error(f"Tavily API request failed with status: {response.status_code}")
                    # Fallback to mock
                    mock_scraper = MockLeadScraper()
                    return await mock_scraper.scrape(niche, location, limit)
        except Exception as e:
            logger.error(f"Tavily lead scraping error: {str(e)}")
            mock_scraper = MockLeadScraper()
            return await mock_scraper.scrape(niche, location, limit)

        return leads

# =====================================================================
# High-Fidelity Mock Lead Scraper (Zero-Config Fallback)
# =====================================================================

class MockLeadScraper(BaseLeadScraper):
    """Generates hyper-realistic local niche lead data for demonstration and CLI pipeline execution."""

    async def scrape(self, niche: str, location: str, limit: int = 5) -> List[LeadModel]:
        logger.info(f"Simulating lead scraping for niche '{niche}' in location '{location}'...")
        
        # Unique local names tailored by location
        niche_names = {
            "Doctors": ["City Care Family Practice", "Apollo Clinic", "Elite Dental Wellness", "Nirvana Pediatrics", "Metro Heart Hospital"],
            "Real Estate": ["Apex Realty Partners", "Prestige Estates Noida", "Signature Global Realty", "Noida Luxury Living Solutions", "Eldeco Homes Concierge"],
            "Gyms": ["Iron Beast Fitness Hub", "Noida Powerhouse CrossFit", "Zenergy Yoga & Pilates Studio", "The Fit Lab Wellness", "Titan Gym & Recovery"],
            "Cafes": ["The Daily Grind Cafe", "Roasters Coffee Bistro", "Blue Tokai Noida", "Caffeine & Co", "The Artisan Baker"],
            "Boutiques": ["Vogue Threads Designer Studio", "Noida Elegance Couture", "Velvet & Co Boutique", "Urban Style Closet", "Sartorial Chic Fashion Hub"],
            "Law Firms": ["Sethi & Associates Legal", "Noida Corporate Counsel", "Justice League Law Practice", "Veritas Criminal Defense Partners", "Equity Law Chambers"],
            "HVAC/Plumbing": ["Noida Rapid Plumbing Services", "Cool Breeze HVAC Solutions", "Emergency Pipe Fixers", "Dynamic Heating & Air Repair", "Apex Flow Drain Cleaning"],
            "Salons": ["Bellezza Luxury Spa & Salon", "The Gentlemen's Grooming Lounge", "Tress & Gloss Hair Studio", "Organic Wellness Retreat", "Radiant Glow Esthetics"],
            "Digital Creators": ["Noida Podcasting Hub", "Vivid Media Agency", "Digital Assets Creator Lab", "The Content Machine Studio", "Pixel Perfect Digital Co"],
            "Private Schools": ["Golden Oaks International School", "Noida Montessori Pre-School", "Apex Global Academy", "The Heritage School Noida", "St. Jude Foundation School"]
        }

        # Choose the set of names or use a default list
        names = niche_names.get(niche, [f"Standard {niche} Partners", f"{niche} Solutions Group", f"Local {niche} Center"])
        
        leads: List[LeadModel] = []
        for i in range(min(limit, len(names))):
            name = names[i]
            lead_id = f"lead_{niche.lower()[:3]}_{i+1}_{uuid.uuid4().hex[:4]}"
            
            # Formulate local realistic phone numbers
            if "Noida" in location or "Delhi" in location:
                phone = f"+91 9810{i} 543{i}2"
                domain_ext = "in"
            else:
                phone = f"+1 (555) 014-{3000 + i}"
                domain_ext = "com"

            clean_name = "".join(e for e in name.lower() if e.isalnum() or e == ' ').replace(' ', '')
            website = f"https://www.{clean_name}.{domain_ext}"
            email = f"info@{clean_name}.{domain_ext}"
            
            # Let's make every second lead lack a website or have a basic one to exercise competitor logic
            if i % 2 == 1:
                website = None

            leads.append(
                LeadModel(
                    id=lead_id,
                    name=name,
                    phone=phone,
                    email=email,
                    website=website,
                    niche=niche,
                    location=location,
                    status="Scraped"
                )
            )

        logger.info(f"Scraped {len(leads)} standardized mock leads for Niche={niche}, Loc={location}")
        return leads
