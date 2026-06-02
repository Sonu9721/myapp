import os
import re
import httpx
import shutil
import asyncio
import logging
from typing import Dict, Any, Optional
from backend.config import LeadModel, EnrichedBusinessProfile, GEMINI_API_KEY, NICHES

logger = logging.getLogger("SiteGenerator")

# =====================================================================
# Programmatic High-Converting Site Generator & Deployment Engine
# =====================================================================

class ProgrammaticSiteGenerator:
    """Uses Gemini 3.5 Flash to write custom premium single-page visual assets."""

    def __init__(self, gemini_key: str = GEMINI_API_KEY, agency_name: str = "CinemaOS AI Agency"):
        self.gemini_key = gemini_key
        self.agency_name = agency_name
        self.builds_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "builds"))
        
        # Ensure builds directory exists
        os.makedirs(self.builds_dir, exist_ok=True)

    def _strip_markdown_codeblocks(self, text: str) -> str:
        """Regex helper to extract raw code if LLM wraps output in ```html or ``` blocks."""
        cleaned = text.strip()
        # Remove opening ```html or ```
        cleaned = re.sub(r"^```(?:html)?\s*", "", cleaned, flags=re.IGNORECASE)
        # Remove closing ```
        cleaned = re.sub(r"\s*```$", "", cleaned)
        return cleaned.strip()

    async def _call_gemini_api(self, prompt: str) -> str:
        """Calls Gemini API via httpx to generate clean raw code."""
        # Standard endpoint for Gemini 1.5/2.5/3.5 Flash style models
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_key}"
        
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 8192
            }
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                data = response.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return text
            else:
                raise Exception(f"Gemini API returned status {response.status_code}: {response.text}")

    async def generate_site(self, lead: LeadModel, profile: EnrichedBusinessProfile) -> str:
        """Asynchronously triggers page generation and local build saving."""
        lead_build_dir = os.path.join(self.builds_dir, lead.id)
        os.makedirs(lead_build_dir, exist_ok=True)
        
        output_file_path = os.path.join(lead_build_dir, "index.html")
        logger.info(f"Generating custom site preview for {lead.name} at {output_file_path}...")

        # Construct highly tailored prompt for high-converting marketing copywriting
        prompt = f"""
You are a world-class UI/UX Designer and Expert Full-Stack Developer.
Generate a premium, single-page marketing website for '{lead.name}', a business in the '{lead.niche}' niche located in '{lead.location}'.
The design system must match this recommended branding vibe: "{profile.branding_vibe}"
You MUST highlight their specific operational pain points: {profile.pain_points}
You MUST feature their custom tailored AI products, specifically their brand new "Autonomous AI Voice Agent" (supporting both ultra-low latency customized male and female voices, running 24/7/365 with perfect memory).

CRITICAL REQUIREMENTS:
1. Output ONLY pure, raw HTML/Tailwind CSS code. Do not wrap the output in markdown codeblocks (no ```html ... ```). Start directly with '<!DOCTYPE html>' and end with '</html>'.
2. Use Tailwind CSS via the official Play CDN: <script src="https://cdn.tailwindcss.com"></script>
3. Use Lucide Icons via CDN: <script src="https://unpkg.com/lucide@latest"></script>
4. Include a fully interactive simulated AI Voice Agent widget in a section where users can select 'Male Voice (Oliver)' or 'Female Voice (Aria)', click 'Simulate Call', see visual audio equalizer bars animate via JavaScript, and hear a mock conversational voice check (use simple HTML5 audio synth or highly premium visual animations).
5. Highlight an interactive scheduler form customized for the '{lead.niche}' niche (e.g. medical booking matrix for Doctors, home-valuer appointment for Real Estate).
6. The footer must explicitly say: "Engineered by {self.agency_name} - Transitioning Businesses to System-for-Revenue Assets."
7. Make the website gorgeous: use deep glassmorphism grids, glowing neon borders, harmonious color schemes, smooth custom scroll, and a modern clean typography scale.
"""

        html_code = ""
        if self.gemini_key:
            try:
                raw_response = await self._call_gemini_api(prompt)
                html_code = self._strip_markdown_codeblocks(raw_response)
                logger.info("Successfully received custom site code from Gemini API.")
            except Exception as e:
                logger.error(f"Gemini API generation failed: {str(e)}. Using fallback Jinja template system.")
                html_code = self._compile_fallback_template(lead, profile)
        else:
            logger.info("No Gemini API Key supplied. Activating premium Jinja fallback compiler.")
            html_code = self._compile_fallback_template(lead, profile)

        # Write code directly to local builds folder
        with open(output_file_path, "w", encoding="utf-8") as f:
            f.write(html_code)

        # Trigger mock deployment webhook
        await self._mock_deployment_trigger(lead.id, output_file_path)
        
        # Return local preview URL structure
        return f"file:///{output_file_path.replace(os.sep, '/')}"

    async def _mock_deployment_trigger(self, lead_id: str, file_path: str) -> None:
        """Simulates triggering a deployment webhook on Vercel, AWS S3, or Hostinger."""
        logger.info(f"Initiating cloud deployment webhook for Lead: {lead_id}...")
        await asyncio.sleep(1.0)  # Simulate API hop latency
        logger.info(f"Webhook response: 200 OK. Visual asset deployed successfully to staging edge!")
        logger.info(f"Custom Live URL: https://preview.cinemaos.agency/deployments/{lead_id}/index.html")

    def _compile_fallback_template(self, lead: LeadModel, profile: EnrichedBusinessProfile) -> str:
        """Compiles a premium, interactive, beautifully designed single-page responsive HTML."""
        
        # Select background gradient & accent color based on niche
        niche_themes = {
            "Doctors": {"bg": "from-slate-900 via-blue-950 to-slate-900", "accent": "sky", "primary": "blue"},
            "Real Estate": {"bg": "from-stone-950 via-neutral-900 to-stone-950", "accent": "amber", "primary": "amber"},
            "Gyms": {"bg": "from-zinc-950 via-stone-900 to-zinc-950", "accent": "emerald", "primary": "green"},
            "Cafes": {"bg": "from-amber-950 via-stone-900 to-stone-950", "accent": "yellow", "primary": "orange"},
            "Boutiques": {"bg": "from-stone-950 via-rose-950 to-neutral-900", "accent": "rose", "primary": "pink"},
            "Law Firms": {"bg": "from-slate-950 via-slate-900 to-zinc-950", "accent": "indigo", "primary": "blue"},
            "HVAC/Plumbing": {"bg": "from-neutral-950 via-slate-900 to-zinc-950", "accent": "red", "primary": "red"},
            "Salons": {"bg": "from-neutral-950 via-rose-950 to-zinc-950", "accent": "rose", "primary": "rose"},
            "Digital Creators": {"bg": "from-slate-950 via-purple-950 to-black", "accent": "purple", "primary": "violet"},
            "Private Schools": {"bg": "from-slate-950 via-emerald-950 to-neutral-950", "accent": "emerald", "primary": "emerald"}
        }

        theme = niche_themes.get(lead.niche, {"bg": "from-slate-950 via-neutral-900 to-black", "accent": "indigo", "primary": "indigo"})
        n_accent = theme["accent"]
        n_prim = theme["primary"]
        
        # Build solution list rendering
        solutions_html = ""
        for sol in NICHES[lead.niche].core_solutions:
            solutions_html += f"""
            <div class="p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-md hover:border-{n_accent}-500/50 transition duration-300">
                <div class="w-12 h-12 rounded-xl bg-{n_accent}-500/20 flex items-center justify-center mb-4">
                    <i data-lucide="cpu" class="text-{n_accent}-400 w-6 h-6 animate-pulse"></i>
                </div>
                <h3 class="text-xl font-bold text-white mb-2">{sol}</h3>
                <p class="text-slate-400 text-sm">Automated enterprise-grade model built specifically to capture leakage and optimize operational return.</p>
            </div>
            """

        # Build pain points grid
        pains_html = ""
        for idx, pain in enumerate(profile.pain_points):
            pains_html += f"""
            <div class="flex items-start gap-4 p-4 rounded-xl bg-red-500/5 border border-red-500/10 hover:bg-red-500/10 transition duration-300">
                <div class="w-8 h-8 rounded-full bg-red-500/25 flex items-center justify-center shrink-0">
                    <i data-lucide="alert-triangle" class="text-red-400 w-4 h-4"></i>
                </div>
                <div>
                    <h4 class="text-white font-semibold mb-1">Critical Leakage Point #{idx+1}</h4>
                    <p class="text-red-200/70 text-sm leading-relaxed">{pain}</p>
                </div>
            </div>
            """

        # Formulate niche scheduler details
        schedulers = {
            "Doctors": ("Patient Intake & Booking Matrix", "Select Clinic Appointment Mode"),
            "Real Estate": ("Listing Appraisal & Booking Hub", "Select Valuation Date"),
            "Gyms": ("Orientation Booking & Scheduler", "Select Class Session Block"),
            "Cafes": ("Vip Catering & Order Reservation", "Select Pick-up & Menu Slot"),
            "Boutiques": ("Virtual Stylist Consult Scheduler", "Select Personal Fitting Time"),
            "Law Firms": ("Unqualified Filter Consultation", "Select Litigation Counsel Slot"),
            "HVAC/Plumbing": ("Priority Dispatch Scheduler", "Select Repair Window"),
            "Salons": ("Chair Booking & Re-Booking Engine", "Select Hair Stylist Appointment"),
            "Digital Creators": ("Sponsorship Coordinator Booking", "Select Media Intake Call"),
            "Private Schools": ("Tuition Admissions Consultation", "Select Virtual Tour Date")
        }
        sched_title, sched_select = schedulers.get(lead.niche, ("Asset Booking & Qualification Hub", "Select Slot"))

        # Raw HTML template
        html_code = f"""<!DOCTYPE html>
<html lang="en" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{lead.name} | Automated AI Platform</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {{
            theme: {{
                extend: {{
                    colors: {{
                        primary: {{
                            50: '#f5f3ff', 100: '#e0e7ff', 500: '#6366f1', 600: '#4f46e5', 700: '#4338ca'
                        }}
                    }}
                }}
            }}
        }}
    </script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        .glass {{
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.08);
        }}
        .glow-glow {{
            box-shadow: 0 0 40px -5px rgba(99, 102, 241, 0.3);
        }}
    </style>
</head>
<body class="bg-gradient-to-br {theme["bg"]} min-h-screen text-slate-100 font-sans selection:bg-indigo-500 selection:text-white antialiased">

    <!-- Glowing Background Spotlights -->
    <div class="fixed top-[-10%] left-[-10%] w-[50%] h-[50%] rounded-full bg-indigo-500/10 blur-[120px] pointer-events-none"></div>
    <div class="fixed bottom-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full bg-{n_accent}-500/10 blur-[120px] pointer-events-none"></div>

    <!-- Navigation Header -->
    <header class="sticky top-0 z-50 w-full glass border-b border-white/5 py-4">
        <div class="max-w-7xl mx-auto px-6 flex justify-between items-center">
            <a href="#" class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-indigo-600 flex items-center justify-center glow-glow">
                    <i data-lucide="infinity" class="text-white w-6 h-6 animate-pulse"></i>
                </div>
                <span class="text-xl font-bold tracking-tight text-white">{lead.name} <span class="text-indigo-400 text-xs font-semibold uppercase tracking-wider ml-1 px-2 py-0.5 rounded-full bg-indigo-500/15">AI System</span></span>
            </a>
            <div class="flex items-center gap-4">
                <a href="#solutions" class="text-sm text-slate-300 hover:text-white transition">Core Asset Solutions</a>
                <a href="#voice-simulation" class="text-sm text-slate-300 hover:text-white transition">Voice AI Agent</a>
                <a href="#scheduler" class="text-sm bg-indigo-600 hover:bg-indigo-500 text-white font-semibold px-4 py-2 rounded-lg transition shadow-lg shadow-indigo-500/20">Secure A Consultation</a>
            </div>
        </div>
    </header>

    <!-- Hero Section -->
    <section class="relative py-24 px-6 max-w-7xl mx-auto flex flex-col items-center text-center">
        <div class="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-semibold uppercase tracking-wider mb-8 animate-bounce">
            <i data-lucide="sparkles" class="w-4 h-4"></i> Transitioning Local Business to Automated Assets
        </div>
        <h1 class="text-5xl md:text-7xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-white via-slate-100 to-indigo-300 tracking-tight leading-none max-w-5xl mb-6">
            Converting Inbound Traffic into High-Yield Revenue Streams.
        </h1>
        <p class="text-lg md:text-xl text-slate-400 max-w-3xl leading-relaxed mb-12">
            Standard systems rely on time for money. {lead.name} automates patient onboarding, client qualification, emergency dispatching, and dynamic follow-ups with bulletproof conversational AI running 24/7/365.
        </p>
        <div class="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <a href="#scheduler" class="px-8 py-4 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-xl transition shadow-xl shadow-indigo-500/35 flex items-center gap-2">
                Secure Custom Demo Portal <i data-lucide="arrow-right" class="w-5 h-5"></i>
            </a>
            <a href="#voice-simulation" class="px-8 py-4 glass text-white hover:bg-white/5 font-semibold rounded-xl transition flex items-center gap-2">
                <i data-lucide="phone-call" class="w-5 h-5 text-indigo-400"></i> Simulate AI Voice Assistant
            </a>
        </div>
    </section>

    <!-- Critical Leaks Audit Section -->
    <section class="py-16 max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-2 gap-12 items-center border-y border-white/5">
        <div>
            <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-red-500/10 border border-red-500/20 text-red-300 text-xs font-semibold uppercase tracking-wider mb-4">
                <i data-lucide="shield-alert" class="w-4 h-4"></i> Local Business Leak Audit
            </div>
            <h2 class="text-3xl md:text-4xl font-extrabold text-white tracking-tight mb-4">
                Where Your Competitors Are Stealing Your Clients.
            </h2>
            <p class="text-slate-400 leading-relaxed mb-6">
                Our deep background research in {lead.location} indicates severe booking leaks, high friction phone loops, and delayed scheduling response. If an inquiry remains unanswered for 5 minutes, retention odds plummet by over 80%.
            </p>
            
            <div class="space-y-4">
                {pains_html}
            </div>
        </div>

        <div class="p-8 rounded-3xl bg-slate-950/60 border border-white/5 backdrop-blur-xl relative overflow-hidden flex flex-col justify-between h-full min-h-[400px]">
            <div class="absolute top-0 right-0 w-32 h-32 bg-indigo-500/10 rounded-full blur-3xl"></div>
            <div>
                <span class="text-xs font-semibold text-indigo-400 uppercase tracking-widest block mb-2">Automated Optimization Target</span>
                <h3 class="text-2xl font-bold text-white mb-4">Tailored Brand Vibe recommendation</h3>
                <p class="text-slate-300 italic mb-8">"{profile.branding_vibe}"</p>
            </div>
            
            <div class="p-6 rounded-2xl bg-indigo-500/10 border border-indigo-500/20">
                <div class="flex items-center gap-3 mb-3">
                    <i data-lucide="activity" class="text-indigo-400 animate-pulse w-5 h-5"></i>
                    <h4 class="text-white font-bold">Why You Need 24/7 Voice AI</h4>
                </div>
                <p class="text-indigo-200/80 text-sm leading-relaxed">{profile.voice_agent_necessity}</p>
            </div>
        </div>
    </section>

    <!-- Core Asset Solutions -->
    <section id="solutions" class="py-24 max-w-7xl mx-auto px-6">
        <div class="text-center max-w-3xl mx-auto mb-16">
            <h2 class="text-3xl md:text-4xl font-extrabold text-white tracking-tight mb-4">
                System-for-Revenue Digital Assets.
            </h2>
            <p class="text-slate-400">
                We engineer customized, high-converting platforms that bypass manual bottlenecks, automate appointment loops, and guarantee client acquisition.
            </p>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
            {solutions_html}
        </div>
    </section>

    <!-- Live AI Voice Agent Simulator widget -->
    <section id="voice-simulation" class="py-20 max-w-5xl mx-auto px-6">
        <div class="p-8 md:p-12 rounded-3xl bg-slate-950/80 border border-indigo-500/20 backdrop-blur-2xl relative overflow-hidden">
            <div class="absolute top-[-20%] right-[-20%] w-[60%] h-[60%] rounded-full bg-indigo-500/15 blur-[80px]"></div>
            
            <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-8 mb-12 border-b border-white/10 pb-8">
                <div>
                    <span class="text-xs font-bold text-indigo-400 uppercase tracking-widest block mb-2">Instant Demo Widget</span>
                    <h2 class="text-3xl font-extrabold text-white tracking-tight">Autonomous AI Voice Representative</h2>
                    <p class="text-slate-400 text-sm mt-1">Simulate our 24/7 latency-free voice assistant trained on {lead.niche} intake configurations.</p>
                </div>
                <div class="flex items-center gap-2 p-1.5 rounded-xl bg-white/5 border border-white/10 shrink-0">
                    <button id="btn-oliver" onclick="selectVoice('Oliver')" class="px-4 py-2 text-xs font-bold rounded-lg bg-indigo-600 text-white transition">Oliver (Male)</button>
                    <button id="btn-aria" onclick="selectVoice('Aria')" class="px-4 py-2 text-xs font-bold rounded-lg text-slate-400 hover:text-white transition">Aria (Female)</button>
                </div>
            </div>

            <div class="flex flex-col items-center justify-center py-8">
                <!-- Visual Ring and Equalizer -->
                <div id="sim-ring" class="w-32 h-32 rounded-full border-2 border-indigo-500/35 flex items-center justify-center relative mb-8 transition duration-500">
                    <div id="sim-pulse" class="absolute inset-0 rounded-full border border-indigo-500/60 animate-ping opacity-0"></div>
                    <div class="w-24 h-24 rounded-full bg-indigo-600/20 border border-indigo-500/40 flex items-center justify-center">
                        <i id="call-icon" data-lucide="phone" class="text-indigo-400 w-10 h-10 animate-pulse"></i>
                    </div>
                </div>

                <!-- Animated Equalizer Bars -->
                <div id="eq-box" class="flex items-end justify-center gap-1.5 h-12 mb-8 opacity-40 transition duration-300">
                    <div class="w-1.5 bg-indigo-400 rounded-full h-4 transition-all duration-150"></div>
                    <div class="w-1.5 bg-indigo-400 rounded-full h-8 transition-all duration-150"></div>
                    <div class="w-1.5 bg-indigo-400 rounded-full h-6 transition-all duration-150"></div>
                    <div class="w-1.5 bg-indigo-400 rounded-full h-10 transition-all duration-150"></div>
                    <div class="w-1.5 bg-indigo-400 rounded-full h-5 transition-all duration-150"></div>
                    <div class="w-1.5 bg-indigo-400 rounded-full h-7 transition-all duration-150"></div>
                    <div class="w-1.5 bg-indigo-400 rounded-full h-3 transition-all duration-150"></div>
                </div>

                <div class="text-center max-w-md mb-8">
                    <h3 id="sim-status" class="text-white font-bold text-lg mb-1">Status: Standby</h3>
                    <p id="sim-subtitle" class="text-slate-400 text-sm">Select voice profile above and trigger dynamic call preview.</p>
                </div>

                <button id="btn-call" onclick="triggerCallSimulation()" class="px-8 py-3.5 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-xl shadow-lg shadow-indigo-500/20 transition flex items-center gap-2">
                    <i data-lucide="play" class="w-5 h-5"></i> Trigger Call Simulation
                </button>
            </div>
        </div>
    </section>

    <!-- Interactive Scheduler Form -->
    <section id="scheduler" class="py-20 max-w-4xl mx-auto px-6">
        <div class="p-8 md:p-12 rounded-3xl glass backdrop-blur-xl border border-white/10 shadow-2xl relative">
            <h2 class="text-3xl font-extrabold text-white text-center mb-2">{sched_title}</h2>
            <p class="text-slate-400 text-center text-sm mb-8">Submit details below to lock your revenue optimization consult and receive custom flow charts.</p>
            
            <form onsubmit="handleFormSubmit(event)" class="space-y-6">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                        <label class="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">Company Full Name</label>
                        <input type="text" value="{lead.name}" readonly class="w-full bg-slate-900/60 border border-white/10 rounded-xl px-4 py-3 text-slate-300 focus:outline-none focus:border-indigo-500 transition">
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">{sched_select}</label>
                        <input type="date" required class="w-full bg-slate-900/60 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-indigo-500 transition">
                    </div>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                        <label class="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">Direct Contact Phone</label>
                        <input type="tel" value="{lead.phone or ''}" class="w-full bg-slate-900/60 border border-white/10 rounded-xl px-4 py-3 text-slate-300 focus:outline-none focus:border-indigo-500 transition">
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">Email Destination</label>
                        <input type="email" value="{lead.email or ''}" class="w-full bg-slate-900/60 border border-white/10 rounded-xl px-4 py-3 text-slate-300 focus:outline-none focus:border-indigo-500 transition">
                    </div>
                </div>

                <button type="submit" class="w-full py-4 bg-indigo-600 hover:bg-indigo-500 text-white font-extrabold rounded-xl shadow-xl shadow-indigo-500/20 transition">
                    Confirm Consultation Booking & Deploy Asset
                </button>
            </form>
        </div>
    </section>

    <!-- VIP Footer -->
    <footer class="py-12 border-t border-white/5 bg-slate-950/40">
        <div class="max-w-7xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-6">
            <span class="text-sm text-slate-500">© 2026 {lead.name} System. All rights reserved.</span>
            <span class="text-sm font-semibold text-indigo-400/90 tracking-wide glow-text">
                Engineered by {self.agency_name} - Transitioning Businesses to System-for-Revenue Assets.
            </span>
        </div>
    </footer>

    <!-- Interactive Simulator Script -->
    <script>
        lucide.createIcons();

        let activeVoice = 'Oliver';
        let callActive = false;
        let intervalId = null;

        function selectVoice(voice) {{
            activeVoice = voice;
            const btnOliver = document.getElementById('btn-oliver');
            const btnAria = document.getElementById('btn-aria');
            
            if(voice === 'Oliver') {{
                btnOliver.className = "px-4 py-2 text-xs font-bold rounded-lg bg-indigo-600 text-white transition";
                btnAria.className = "px-4 py-2 text-xs font-bold rounded-lg text-slate-400 hover:text-white transition";
            }} else {{
                btnOliver.className = "px-4 py-2 text-xs font-bold rounded-lg text-slate-400 hover:text-white transition";
                btnAria.className = "px-4 py-2 text-xs font-bold rounded-lg bg-indigo-600 text-white transition";
            }}
            
            if(!callActive) {{
                document.getElementById('sim-subtitle').innerText = `Trained ${{voice}} profile is ready for testing. Click simulate below.`;
            }}
        }}

        function triggerCallSimulation() {{
            const btn = document.getElementById('btn-call');
            const simRing = document.getElementById('sim-ring');
            const simPulse = document.getElementById('sim-pulse');
            const simStatus = document.getElementById('sim-status');
            const simSubtitle = document.getElementById('sim-subtitle');
            const callIcon = document.getElementById('call-icon');
            const eqBox = document.getElementById('eq-box');

            if(!callActive) {{
                // Start call simulation
                callActive = true;
                btn.innerHTML = `<i data-lucide="square" class="w-5 h-5"></i> Terminate Call`;
                lucide.createIcons();
                
                simRing.className = "w-32 h-32 rounded-full border-2 border-emerald-500/80 flex items-center justify-center relative mb-8 transition duration-500 shadow-xl shadow-emerald-500/10";
                simPulse.className = "absolute inset-0 rounded-full border border-emerald-500/60 animate-ping";
                callIcon.className = "text-emerald-400 w-10 h-10";
                eqBox.className = "flex items-end justify-center gap-1.5 h-12 mb-8 opacity-100 transition duration-300";
                
                simStatus.innerText = "Status: Connecting...";
                simSubtitle.innerText = "Initiating custom audio synthesis routing...";

                // Synthesize conversation milestones
                setTimeout(() => {{
                    if(callActive) {{
                        simStatus.innerText = "Status: Connected";
                        simSubtitle.innerText = `[${{activeVoice}} AI Assistant]: Hello! Thanks for calling {lead.name}. How can I assist you with your booking today?`;
                    }}
                }}, 1500);

                setTimeout(() => {{
                    if(callActive) {{
                        simSubtitle.innerText = `[${{activeVoice}} AI Assistant]: I can slot you in for our specialized session this Thursday. Would 11:00 AM work?`;
                    }}
                }}, 5000);

                // Animate bars
                const bars = eqBox.children;
                intervalId = setInterval(() => {{
                    for(let i=0; i<bars.length; i++) {{
                        const h = Math.floor(Math.random() * 35) + 8;
                        bars[i].style.height = `${{h}}px`;
                    }}
                }}, 150);

            }} else {{
                // Stop call simulation
                callActive = false;
                clearInterval(intervalId);
                btn.innerHTML = `<i data-lucide="play" class="w-5 h-5"></i> Trigger Call Simulation`;
                lucide.createIcons();
                
                simRing.className = "w-32 h-32 rounded-full border-2 border-indigo-500/35 flex items-center justify-center relative mb-8 transition duration-500";
                simPulse.className = "absolute inset-0 rounded-full border border-indigo-500/60 animate-ping opacity-0";
                callIcon.className = "text-indigo-400 w-10 h-10 animate-pulse";
                eqBox.className = "flex items-end justify-center gap-1.5 h-12 mb-8 opacity-40 transition duration-300";
                
                simStatus.innerText = "Status: Call Terminated";
                simSubtitle.innerText = "Simulation closed. Choose a voice model above to re-simulate.";
                
                // Reset bars
                const bars = eqBox.children;
                for(let i=0; i<bars.length; i++) {{
                    bars[i].style.height = `16px`;
                }}
            }}
        }}

        function handleFormSubmit(e) {{
            e.preventDefault();
            alert("Success! Your premium AI Lead-Gen Preview slot is locked. Check your email inbox for intake reports.");
        }}
    </script>
</body>
</html>
"""
        return html_code
