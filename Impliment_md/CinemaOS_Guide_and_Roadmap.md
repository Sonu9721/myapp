# 🚀 CinemaOS AI Lead Engine — Complete Guide & Roadmap

> **Your software is a fully automated AI-powered revenue machine.**
> It scrapes local businesses, audits them with AI, builds them a custom website, and sends them a personalized pitch — all in minutes, while you sleep.

---

## 📦 PART 1: What Has Been Built For You

You now own a **4-Stage Autonomous Lead Generation & Outreach Engine** made of two integrated systems:

### 🔵 System A — The Python Backend Engine (The Money Machine)
A fully automated pipeline that runs from your terminal. No UI needed. One command fires everything.

| File | What It Does |
|---|---|
| `config.py` | Brain of the system. Stores niche profiles (10 niches), keywords, pain points, AI solutions |
| `scraper.py` | Pulls local business data (Name, Phone, Email, Website) from Tavily or Mock |
| `researcher.py` | Audits each business using Firecrawl + Tavily. Sends data to Llama 3.3 via Groq |
| `generator.py` | Builds a custom premium HTML website for each business using Gemini AI |
| `outreach.py` | Sends a personalized cold email + WhatsApp message with the live preview link |
| `orchestrator.py` | The **Master Controller** — runs all 4 steps in sequence automatically |
| `database.py` | Saves every lead's status in SQLite/PostgreSQL (Scraped → Audited → Generated → Pitched) |

### 🟣 System B — The CinemaOS Dashboard (The Control Center)
A beautiful dark-mode React web app running at `http://localhost:3000`

| Page | What It Shows |
|---|---|
| **Landing Page** | Marketing overview of your AI agency |
| **Dashboard** | Live KPIs — leads scraped, profiles built, sites generated, pitches sent |
| **Project Workspace** | Select niche + location, launch campaigns with one button |
| **Agent Manager** | View and configure all 15 specialized AI agents |
| **Workflow Builder** | Visual n8n-style flow showing the 5-node pipeline |
| **Media Library** | Preview the generated client websites |
| **Live Execution Console** | Watch the AI work in real-time |
| **Settings** | Enter your API keys (Groq, Gemini, Tavily, Firecrawl) |
| **Billing** | 3 pricing tiers for your clients |
| **Team** | Manage your team members |

---

## 🎯 PART 2: What You Can Do With This Software

### ✅ USE CASE 1 — Automated Lead Generation (10 Niches)
Run this one command and the engine scrapes leads, audits them, builds websites, and pitches them:
```powershell
python -m backend.orchestrator --niche "Real Estate" --location "Noida" --mock --limit 5
```
**Works for all 10 niches:**
- Doctors | Real Estate | Gyms | Cafes | Boutiques
- Law Firms | HVAC/Plumbing | Salons | Digital Creators | Private Schools

---

### ✅ USE CASE 2 — Instant Custom Website Generation
For every scraped lead, your system **automatically builds a premium landing page** that includes:
- ✦ Niche-specific hero copy & pain point sections
- ✦ Interactive AI Voice Agent widget (Oliver/Aria male & female voices)
- ✦ Appointment/booking scheduler customized per niche
- ✦ Branding vibe recommended by Llama 3.3 AI
- ✦ Agency footer: *"Engineered by CinemaOS AI Agency"*
- ✦ Saved to `backend/builds/<lead_id>/index.html`

**Example outputs already generated:**
- `backend/builds/lead_rea_1_5854/index.html` → Apex Realty Partners, Noida

---

### ✅ USE CASE 3 — B2B Cold Outreach Machine
After the website is built, the system automatically sends:

**📧 Cold Email (via SMTP)**
- Subject: *"Lead leakage alert for [Business Name]..."*
- Body: Personalized pain point analysis + live preview link + AI Voice Agent pitch
- Positions you as a **System-for-Revenue agency**

**💬 WhatsApp Message (via Twilio)**
- Mobile-optimized bold formatting
- Zero-friction CTA: *"Reply YES to book a 10-minute demo"*
- Mentions 24/7/365 AI Voice Agent with PostgreSQL memory

---

### ✅ USE CASE 4 — AI Business Intelligence Reports
For every business, Llama 3.3 (via Groq) generates a structured JSON profile:
```json
{
  "pain_points": ["Friction in booking loops", "No AI chatbot", "Local competitors faster"],
  "voice_agent_necessity": "Realtors who respond after 5 min lose 380% of leads...",
  "branding_vibe": "Luxurious dark charcoal + golden sand glassmorphic cards"
}
```
This is stored in your database and used to personalize every piece of communication.

---

### ✅ USE CASE 5 — AI Voice Agent Demo (Client-Facing)
Every generated website has a **live AI Voice Agent simulation widget** where your potential client can:
1. Select Male voice (Oliver) or Female voice (Aria)
2. Click "Trigger Call Simulation"
3. Watch the audio equalizer animate
4. Read AI dialogue responses in real-time

This is your **product demo** built into every pitch asset.

---

### ✅ USE CASE 6 — Multi-Niche Agency Business
You can run this for any city, any niche, any number of leads:
```powershell
python -m backend.orchestrator --niche "Doctors" --location "Delhi" --mock --limit 10
python -m backend.orchestrator --niche "Salons" --location "Mumbai" --mock --limit 5
python -m backend.orchestrator --niche "Private Schools" --location "Noida" --limit 3
```

---

## 🗺️ PART 3: Your 90-Day Roadmap (Phase-by-Phase)

---

### 📅 PHASE 1 — VALIDATE (Days 1–15) | No Investment Needed
**Goal:** Get your first 1-2 paying clients using mock mode.

**Day 1-3: Setup & Test**
- [ ] Open terminal in `c:\Users\digit\Desktop\myapp`
- [ ] Run: `npm run dev` inside `frontend/` → Open `http://localhost:3000`
- [ ] Run: `python -m backend.orchestrator --niche "Real Estate" --location "Noida" --mock --limit 1`
- [ ] Open the generated `backend/builds/<lead_id>/index.html` in browser
- [ ] Review the full output — email copy, WhatsApp message, website

**Day 4-7: Pick Your First Target Niche**
- Choose **ONE niche** to start (Recommended: Real Estate or Gyms or Private Schools)
- Find 10 local businesses manually on Google Maps
- Add their Name, Phone, Email, Website to a spreadsheet

**Day 8-15: Manual Outreach with AI Assets**
- For each business, run the generator to build their custom preview site
- Send the cold email and WhatsApp **manually** using the templates generated
- Track replies in your spreadsheet

> **Target:** 1 client signs up for a ₹5,000–₹15,000 pilot project

---

### 📅 PHASE 2 — ACTIVATE APIS (Days 16–45) | Small Investment
**Goal:** Remove mock mode. Connect real APIs to run fully automated campaigns.

**Week 1: Get Your API Keys**

| API | Cost | Where to Sign Up |
|---|---|---|
| Groq (Llama 3.3 70B) | FREE tier available | console.groq.com |
| Google Gemini API | FREE tier available | aistudio.google.com |
| Tavily Search API | FREE tier (1000 req/mo) | tavily.com |
| Firecrawl API | FREE tier (500 pages/mo) | firecrawl.dev |

**Enter Keys in `.env` file** (create in `c:\Users\digit\Desktop\myapp\`):
```
GROQ_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
TAVILY_API_KEY=your_key_here
FIRECRAWL_API_KEY=your_key_here
SMTP_USER=your_gmail@gmail.com
SMTP_PASSWORD=your_app_password
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_NUMBER=+91xxxxxxxxxx
```

**Week 3-4: First Automated Campaign (No Mock)**
```powershell
python -m backend.orchestrator --niche "Gyms" --location "Noida" --limit 5
```
Watch it scrape 5 real leads → audit → build 5 websites → send 5 emails + WhatsApp.

> **Target:** 2-3 clients. Monthly recurring ₹15,000–₹30,000

---

### 📅 PHASE 3 — SCALE (Days 46–90) | System-for-Revenue Mode
**Goal:** Run campaigns for 3+ niches simultaneously. ₹1L+/month.

**Run parallel campaigns:**
```powershell
python -m backend.orchestrator --niche "Real Estate" --location "Noida" --limit 20
python -m backend.orchestrator --niche "Doctors" --location "Delhi" --limit 20
python -m backend.orchestrator --niche "Private Schools" --location "Gurgaon" --limit 15
```

**Productize Your Offering (use the Billing page):**

| Tier | Price | What They Get |
|---|---|---|
| **Starter** | ₹8,000/mo | 1 niche, 20 leads/mo, custom website + email outreach |
| **Growth** | ₹25,000/mo | 3 niches, 100 leads/mo, WhatsApp + email + AI Voice Agent demo |
| **Enterprise** | ₹80,000/mo | Unlimited niches, full automation + dedicated AI Voice Agent deployed |

> **Target:** 5 Growth clients = ₹1.25 Lakh/month

---

## 🔑 PART 4: Your Quick Reference Control Panel

```
COMMAND REFERENCE
══════════════════════════════════════════════════════
Start Dashboard      → cd frontend && npm run dev
Run Campaign (mock)  → python -m backend.orchestrator --niche "Real Estate" --location "Noida" --mock --limit 1
Run Campaign (live)  → python -m backend.orchestrator --niche "Doctors" --location "Delhi" --limit 10
View builds          → Open backend/builds/<lead_id>/index.html in Chrome
Add API keys         → Create .env file in c:\Users\digit\Desktop\myapp\

SUPPORTED NICHES
══════════════════════════════════════════════════════
Doctors | Real Estate | Gyms | Cafes | Boutiques
Law Firms | HVAC/Plumbing | Salons | Digital Creators | Private Schools

INCOME TARGETS
══════════════════════════════════════════════════════
Phase 1 (Days 1-15)  → ₹5,000–₹15,000 first client
Phase 2 (Days 16-45) → ₹30,000–₹60,000/month (2-3 clients)
Phase 3 (Days 46-90) → ₹1,00,000+/month (5+ clients)
```

---

## 💡 PART 5: The Business Model Visualized

```
YOU RUN THE ENGINE (1 command)
          ↓
Engine finds N local businesses via Tavily/Scraper
          ↓
AI audits every business website via Firecrawl
          ↓
Llama 3.3 identifies their exact revenue leakage
          ↓
Gemini builds them a premium custom website (₹25,000 value)
          ↓
Engine sends personalized cold pitch (email + WhatsApp)
with the live demo link → already showing their AI Voice Agent
          ↓
Business replies "YES" → You book a 10-min call
          ↓
You show: custom site + voice demo + revenue leak analysis
          ↓
You charge ₹8,000–₹80,000/month
          ↓
Repeat for next 100 businesses automatically
```

> You are not selling your time. You are delivering pre-built AI assets and charging for the system.

---

## ⚠️ PART 6: Risks & How to Handle Them

| Risk | Solution |
|---|---|
| Emails going to spam | Use a dedicated domain email. Warm up slowly (5-10 emails/day first week) |
| WhatsApp account banned | Use Twilio Business API, not personal WhatsApp |
| Low reply rates | A/B test subject lines. Try 3 variants per campaign |
| API rate limits | Start with free tiers; upgrade only when you have clients paying |
| Leads without websites | System already handles this — uses Tavily competitor search instead |
| Client wants real voice AI | That is your Phase 3 upsell — charge ₹30K–₹60K/month for deployment |

---

*Engineered by CinemaOS AI Agency — Transitioning Businesses to System-for-Revenue Assets.*
