import React, { useState, useEffect } from 'react';
import { 
  Play, Pause, RefreshCw, Cpu, Layers, HardDrive, PhoneCall, Mail, 
  MessageSquare, User, Users, Settings, CreditCard, LayoutDashboard, 
  Share2, ArrowRight, CheckCircle2, AlertTriangle, Terminal, Eye, 
  Plus, Trash2, Shield, Zap, Sparkles, FolderOpen, Image, FileText, Check
} from 'lucide-react';
import { ParticleBackground } from './components/ParticleBackground';

// Define structures
interface Agent {
  name: string;
  role: string;
  status: 'Idle' | 'Thinking' | 'Working';
  goal: string;
  permissions: {
    write: boolean;
    outbound: boolean;
  };
}

interface WorkflowNode {
  id: string;
  name: string;
  type: 'trigger' | 'action';
  status: 'pending' | 'active' | 'completed';
  description: string;
}

export default function App() {
  const [activeTab, setActiveTab] = useState<'landing' | 'dashboard' | 'agents' | 'workflow' | 'workspace' | 'media' | 'console' | 'settings' | 'billing' | 'team'>('landing');
  const [selectedNiche, setSelectedNiche] = useState<string>('Real Estate');
  const [selectedLocation, setSelectedLocation] = useState<string>('Noida');
  const [logs, setLogs] = useState<string[]>([]);
  const [campaignRunning, setCampaignRunning] = useState<boolean>(false);
  const [currentStep, setCurrentStep] = useState<number>(0);
  const [showNotification, setShowNotification] = useState<string | null>(null);
  
  // Scraped Leads State
  const [leads, setLeads] = useState([
    { id: '1', name: 'Apex Realty Partners', phone: '+91 98101 54312', email: 'info@apexrealty.in', website: 'https://apexrealty.in', status: 'Pitched', preview: 'apexrealty' },
    { id: '2', name: 'Noida Luxury Living Solutions', phone: '+91 98102 54322', email: 'contact@noidaluxury.in', website: null, status: 'Audited', preview: 'noidaluxury' }
  ]);

  // Settings State
  const [apiKeys, setApiKeys] = useState({
    groq: '••••••••••••••••••••',
    gemini: '••••••••••••••••••••',
    tavily: '••••••••••••••••••••',
    firecrawl: '••••••••••••••••••••'
  });

  // 15 Specialized Agents List
  const [agents, setAgents] = useState<Agent[]>([
    { name: 'Cinematic Director Agent', role: 'Swarm Supervisor', status: 'Idle', goal: 'Coordinates specialized subagents to deliver cinematic video assets.', permissions: { write: true, outbound: false } },
    { name: 'Script Writer Agent', role: 'Copywriting', status: 'Idle', goal: 'Drafts emotional, high-conversion narratives based on niche pain points.', permissions: { write: true, outbound: false } },
    { name: 'Storyboard Agent', role: 'Scene Visualizer', status: 'Idle', goal: 'Maps script blocks to visual storyboard prompts and transition maps.', permissions: { write: true, outbound: false } },
    { name: 'Prompt Engineering Agent', role: 'Asset Creator', status: 'Idle', goal: 'Writes optimized prompt arrays for Stability, Midjourney, and Runway.', permissions: { write: false, outbound: false } },
    { name: 'Dialogue Agent', role: 'Copywriting', status: 'Idle', goal: 'Writes sharp conversational voice-over scripts.', permissions: { write: true, outbound: false } },
    { name: 'Character Consistency Agent', role: 'Image QA', status: 'Idle', goal: 'Validates facial vectors across generated visuals for character continuity.', permissions: { write: false, outbound: false } },
    { name: 'Voice/Music Agent', role: 'Audio Synth', status: 'Idle', goal: 'Orchestrates ElevenLabs voices and Suno backing track mixing.', permissions: { write: true, outbound: false } },
    { name: 'Video Editor Agent', role: 'VFX Assembly', status: 'Idle', goal: 'Combines video blocks with transitions and matches subtitles.', permissions: { write: true, outbound: true } },
    { name: 'QA Agent', role: 'Quality Control', status: 'Idle', goal: 'Evaluates video responsiveness, subtitle alignment, and visual glitches.', permissions: { write: false, outbound: false } },
    { name: 'Social Media Export Agent', role: 'Distributor', status: 'Idle', goal: 'Packages video and metadata for Instagram Reels, YouTube Shorts, and TikTok.', permissions: { write: false, outbound: true } },
    { name: 'SEO Agent', role: 'Copywriting', status: 'Idle', goal: 'Optimizes titles, tags, descriptions, and thumbnails for local indexing.', permissions: { write: true, outbound: false } },
    { name: 'Automation Agent', role: 'Pipeline Builder', status: 'Idle', goal: 'Manages API hooks and outbound Twilio posts.', permissions: { write: true, outbound: true } },
    { name: 'Research Agent', role: 'Data Mining', status: 'Idle', goal: 'Scrapes local directories and mines competitor website components.', permissions: { write: true, outbound: false } },
    { name: 'Trend Analysis Agent', role: 'Strategy Planner', status: 'Idle', goal: 'Gathers local Google Search volumes to target high-intent keywords.', permissions: { write: false, outbound: false } },
    { name: 'Thumbnail Agent', role: 'Graphics Designer', status: 'Idle', goal: 'Generates sleek, high-CTR visual banners with text overlays.', permissions: { write: true, outbound: false } }
  ]);

  // Workflow builder nodes
  const [workflowNodes, setWorkflowNodes] = useState<WorkflowNode[]>([
    { id: 'node_1', name: 'Scrape Target Geo-Niche', type: 'trigger', status: 'completed', description: 'Scrapes local leads using base Outscraper/Tavily models' },
    { id: 'node_2', name: 'Deep Audit (Firecrawl/Tavily)', type: 'action', status: 'completed', description: 'Scrapes raw DOM structures and pulls top 3 competitors' },
    { id: 'node_3', name: 'Llama 3.3 Dynamic Profiler', type: 'action', status: 'completed', description: 'Enriches operational bottlenecks and pitches AI voice agent solutions' },
    { id: 'node_4', name: 'Gemini 3.5 HTML Page Generator', type: 'action', status: 'active', description: 'Writes clean, high-performance HTML/Tailwind preview files' },
    { id: 'node_5', name: 'B2B Outreach (Email & WhatsApp)', type: 'action', status: 'pending', description: 'Fires cold emails and twilio posts pointing to preview link' }
  ]);

  // Append logs function
  const triggerLog = (msg: string) => {
    setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] ${msg}`]);
  };

  // Launch pipeline simulator
  const runWorkflowPipeline = () => {
    if (campaignRunning) return;
    setCampaignRunning(true);
    setCurrentStep(1);
    setLogs([]);
    
    triggerLog(`Orchestrator launched campaign: target='${selectedNiche}' in location='${selectedLocation}'`);
    triggerLog(`Loading Central Niche Configurations...`);
  };

  useEffect(() => {
    if (!campaignRunning) return;

    const timer = setInterval(() => {
      setCurrentStep(prev => {
        if (prev === 1) {
          triggerLog(`[STEP 1] Mining ${selectedNiche} leads in ${selectedLocation}...`);
          triggerLog(`[STEP 1] Found 2 target leads. Storing in database.`);
          return 2;
        } else if (prev === 2) {
          triggerLog(`[STEP 2] Launching parallel background audits...`);
          triggerLog(`[STEP 2] Apex Realty website found. Running Firecrawl UI/UX audits...`);
          triggerLog(`[STEP 2] Noida Luxury website missing. Querying Tavily for top 3 geo-competitors...`);
          triggerLog(`[STEP 2] Executing Llama 3.3 70B Groq profiling...`);
          return 3;
        } else if (prev === 3) {
          triggerLog(`[STEP 3] Triggering Gemini 3.5 programmatic React/HTML single-page build...`);
          triggerLog(`[STEP 3] Writing index.html directly to builds/lead_real_1/index.html`);
          triggerLog(`[STEP 3] Webhook deployed preview staging: https://preview.cinemaos.agency/deployments/lead_real_1/index.html`);
          return 4;
        } else if (prev === 4) {
          triggerLog(`[STEP 4] Compiling cold email stack and Twilio WhatsApp drafts...`);
          triggerLog(`[STEP 4] Subject: 'Quick question about missed inquiries at Apex Realty?'`);
          triggerLog(`[STEP 4] WhatsApp: 'Hey! Mapped a critical inquiry leak at Apex Realty...'`);
          triggerLog(`[STEP 4] Outreach successfully dispatched. Moving Lead status to 'Pitched'`);
          
          // Complete
          setCampaignRunning(false);
          setShowNotification("Programmatic Campaign Completed Successfully! Visual live previews deployed & pitches sent.");
          return 5;
        }
        return prev;
      });
    }, 3000);

    return () => clearInterval(timer);
  }, [campaignRunning, selectedNiche, selectedLocation]);

  return (
    <div className="relative min-h-screen bg-[#030712] text-slate-100 flex overflow-hidden">
      <ParticleBackground />

      {/* Top Banner Notification */}
      {showNotification && (
        <div className="fixed top-6 right-6 z-50 p-4 rounded-xl bg-indigo-950/80 border border-indigo-500/50 backdrop-blur-xl flex items-center gap-3 animate-bounce">
          <Sparkles className="text-indigo-400 w-5 h-5 animate-pulse" />
          <span className="text-sm font-semibold text-white">{showNotification}</span>
          <button onClick={() => setShowNotification(null)} className="text-slate-400 hover:text-white ml-2 text-xs font-bold bg-white/10 px-2 py-1 rounded">Dismiss</button>
        </div>
      )}

      {/* LEFT SIDEBAR NAVIGATION */}
      <aside className="relative z-10 w-64 bg-space-950/80 border-r border-white/5 backdrop-blur-2xl flex flex-col justify-between shrink-0">
        <div>
          {/* Glowing Brand Logo */}
          <div className="h-20 flex items-center gap-3 px-6 border-b border-white/5">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-rose-600 flex items-center justify-center shadow-lg shadow-indigo-500/25">
              <Cpu className="text-white w-6 h-6 animate-pulse" />
            </div>
            <div>
              <span className="text-lg font-black tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-slate-100 to-indigo-300">CinemaOS</span>
              <span className="block text-[9px] font-bold text-indigo-400 tracking-widest uppercase">Multi-Agent System</span>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="p-4 space-y-1">
            <button 
              onClick={() => setActiveTab('landing')} 
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition ${activeTab === 'landing' ? 'bg-indigo-600 text-white font-semibold shadow-lg shadow-indigo-600/25' : 'text-slate-400 hover:bg-white/5 hover:text-white'}`}
            >
              <Sparkles className="w-5 h-5" /> Landing Page
            </button>
            <button 
              onClick={() => setActiveTab('dashboard')} 
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition ${activeTab === 'dashboard' ? 'bg-indigo-600 text-white font-semibold shadow-lg shadow-indigo-600/25' : 'text-slate-400 hover:bg-white/5 hover:text-white'}`}
            >
              <LayoutDashboard className="w-5 h-5" /> Dashboard
            </button>
            <button 
              onClick={() => setActiveTab('workspace')} 
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition ${activeTab === 'workspace' ? 'bg-indigo-600 text-white font-semibold shadow-lg shadow-indigo-600/25' : 'text-slate-400 hover:bg-white/5 hover:text-white'}`}
            >
              <FolderOpen className="w-5 h-5" /> Project Workspace
            </button>
            <button 
              onClick={() => setActiveTab('agents')} 
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition ${activeTab === 'agents' ? 'bg-indigo-600 text-white font-semibold shadow-lg shadow-indigo-600/25' : 'text-slate-400 hover:bg-white/5 hover:text-white'}`}
            >
              <Users className="w-5 h-5" /> Agent Manager
            </button>
            <button 
              onClick={() => setActiveTab('workflow')} 
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition ${activeTab === 'workflow' ? 'bg-indigo-600 text-white font-semibold shadow-lg shadow-indigo-600/25' : 'text-slate-400 hover:bg-white/5 hover:text-white'}`}
            >
              <Layers className="w-5 h-5" /> Workflow Builder
            </button>
            <button 
              onClick={() => setActiveTab('media')} 
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition ${activeTab === 'media' ? 'bg-indigo-600 text-white font-semibold shadow-lg shadow-indigo-600/25' : 'text-slate-400 hover:bg-white/5 hover:text-white'}`}
            >
              <Image className="w-5 h-5" /> Media Library
            </button>
            <button 
              onClick={() => setActiveTab('console')} 
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition ${activeTab === 'console' ? 'bg-indigo-600 text-white font-semibold shadow-lg shadow-indigo-600/25' : 'text-slate-400 hover:bg-white/5 hover:text-white'}`}
            >
              <Terminal className="w-5 h-5" /> Live Execution
            </button>
          </nav>
        </div>

        {/* Bottom Utility Menu */}
        <div className="p-4 border-t border-white/5 space-y-1">
          <button 
            onClick={() => setActiveTab('settings')} 
            className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition ${activeTab === 'settings' ? 'bg-indigo-600/20 text-indigo-300' : 'text-slate-400 hover:text-white'}`}
          >
            <Settings className="w-4 h-4" /> System Settings
          </button>
          <button 
            onClick={() => setActiveTab('billing')} 
            className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition ${activeTab === 'billing' ? 'bg-indigo-600/20 text-indigo-300' : 'text-slate-400 hover:text-white'}`}
          >
            <CreditCard className="w-4 h-4" /> Billing & Usage
          </button>
          <button 
            onClick={() => setActiveTab('team')} 
            className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition ${activeTab === 'team' ? 'bg-indigo-600/20 text-indigo-300' : 'text-slate-400 hover:text-white'}`}
          >
            <User className="w-4 h-4" /> Team Collaboration
          </button>
        </div>
      </aside>

      {/* MAIN CONTENT AREA */}
      <main className="relative z-10 flex-1 flex flex-col min-w-0 overflow-y-auto">
        
        {/* TOPBAR */}
        <header className="h-20 bg-space-950/20 border-b border-white/5 backdrop-blur-md flex items-center justify-between px-8 shrink-0">
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-bold capitalize tracking-wide text-white">
              {activeTab === 'landing' ? 'System Overview' : `${activeTab} Workspace`}
            </h1>
            {campaignRunning && (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold uppercase tracking-wider animate-pulse">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping"></span> Swarm Running
              </span>
            )}
          </div>

          {/* Quick Metrics */}
          <div className="flex items-center gap-6">
            <div className="text-right">
              <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Pitched Revenue Assets</span>
              <span className="text-sm font-black text-indigo-300">1,824 Leads Mapped</span>
            </div>
            <div className="w-px h-8 bg-white/10"></div>
            <div className="text-right">
              <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">API Credit Pools</span>
              <span className="text-sm font-black text-teal-300">98.4% Active</span>
            </div>
          </div>
        </header>

        {/* DYNAMIC SCENE MANAGER COMPONENT */}
        <div className="flex-1 p-8">
          
          {/* =========================================================
              TAB: LANDING PAGE (CINEMATIC SALES SYSTEM)
              ========================================================= */}
          {activeTab === 'landing' && (
            <div className="max-w-6xl mx-auto space-y-16">
              {/* Cinematic Hero */}
              <div className="text-center py-16 space-y-6 relative overflow-hidden rounded-3xl bg-slate-950/40 border border-white/5 p-8">
                <div className="absolute inset-0 bg-gradient-to-tr from-indigo-500/5 via-transparent to-rose-500/5 pointer-events-none"></div>
                <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-semibold uppercase tracking-wider">
                  <Sparkles className="w-4 h-4 animate-spin-slow" /> Autonomous AI Multi-Agent Swarms
                </div>
                <h1 className="text-5xl md:text-7xl font-black tracking-tight leading-none text-transparent bg-clip-text bg-gradient-to-r from-white via-slate-100 to-indigo-300">
                  Transition Local Leaks to System-for-Revenue Assets.
                </h1>
                <p className="text-lg md:text-xl text-slate-400 max-w-3xl mx-auto leading-relaxed">
                  Stop charging for hours. Package autonomous pipelines consisting of scrapers, Firecrawl site-auditors, Llama 3.3 profilers, Gemini page builders, and Twilio WhatsApp outbounds.
                </p>
                <div className="pt-8 flex justify-center gap-4">
                  <button onClick={() => setActiveTab('workspace')} className="px-8 py-4 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-xl transition shadow-xl shadow-indigo-600/30 flex items-center gap-2">
                    Enter Orchestration Console <ArrowRight className="w-5 h-5" />
                  </button>
                  <button onClick={() => setActiveTab('workflow')} className="px-8 py-4 glass-card hover:bg-white/5 text-white font-bold rounded-xl transition flex items-center gap-2">
                    <Layers className="w-5 h-5 text-indigo-400 animate-pulse" /> Launch Workflow Nodes
                  </button>
                </div>
              </div>

              {/* $480B Content Economy Highlight */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                <div className="p-8 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-xl">
                  <div className="w-12 h-12 rounded-xl bg-indigo-600/25 flex items-center justify-center mb-6">
                    <Cpu className="text-indigo-400 w-6 h-6 animate-pulse" />
                  </div>
                  <h3 className="text-xl font-bold text-white mb-2">Multi-Agent Swarms</h3>
                  <p className="text-slate-400 text-sm leading-relaxed">Orchestrate 15 specialized agents including Script Writer, Storyboard visualizers, dialogue directors, and QA coordinators autonomously.</p>
                </div>
                <div className="p-8 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-xl">
                  <div className="w-12 h-12 rounded-xl bg-teal-600/25 flex items-center justify-center mb-6">
                    <PhoneCall className="text-teal-400 w-6 h-6 animate-pulse" />
                  </div>
                  <h3 className="text-xl font-bold text-white mb-2">Autonomous Voice AI</h3>
                  <p className="text-slate-400 text-sm leading-relaxed">Frictionless natural language call reception powered by Llama 3.3 and Groq with ultra-low latency, running 24/7/365 with perfect database memory.</p>
                </div>
                <div className="p-8 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-xl">
                  <div className="w-12 h-12 rounded-xl bg-rose-600/25 flex items-center justify-center mb-6">
                    <Layers className="text-rose-400 w-6 h-6 animate-pulse" />
                  </div>
                  <h3 className="text-xl font-bold text-white mb-2">Programmatic Web Gen</h3>
                  <p className="text-slate-400 text-sm leading-relaxed">Gemini 3.5 Flash programmatically generates customized luxury landing pages addressing client specific local leaks instantly, ready to deploy.</p>
                </div>
              </div>
            </div>
          )}

          {/* =========================================================
              TAB: EXECUTIVE DASHBOARD
              ========================================================= */}
          {activeTab === 'dashboard' && (
            <div className="space-y-8 max-w-6xl mx-auto">
              
              {/* KPI Cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div className="p-6 rounded-2xl bg-white/5 border border-white/10">
                  <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Leads Scraped</span>
                  <span className="block text-3xl font-black text-white mt-1">1,481</span>
                  <span className="text-[10px] text-emerald-400 font-semibold block mt-1">+12% this week</span>
                </div>
                <div className="p-6 rounded-2xl bg-white/5 border border-white/10">
                  <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Enriched Profiles</span>
                  <span className="block text-3xl font-black text-white mt-1">984</span>
                  <span className="text-[10px] text-indigo-400 font-semibold block mt-1">Llama 3.3 Processed</span>
                </div>
                <div className="p-6 rounded-2xl bg-white/5 border border-white/10">
                  <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Previews Built</span>
                  <span className="block text-3xl font-black text-white mt-1">642</span>
                  <span className="text-[10px] text-teal-400 font-semibold block mt-1">Gemini 3.5 Generated</span>
                </div>
                <div className="p-6 rounded-2xl bg-white/5 border border-white/10">
                  <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Outbound Pitched</span>
                  <span className="block text-3xl font-black text-white mt-1">421</span>
                  <span className="text-[10px] text-rose-400 font-semibold block mt-1">Pitched Status in DB</span>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                
                {/* Timeline and Logs */}
                <div className="lg:col-span-2 space-y-6">
                  <div className="p-6 rounded-2xl bg-slate-950/40 border border-white/5">
                    <h3 className="text-lg font-bold text-white mb-6 flex items-center gap-2">
                      <Terminal className="text-indigo-400 w-5 h-5 animate-pulse" /> Live Execution Stream
                    </h3>
                    <div className="h-60 bg-black/60 rounded-xl p-4 font-mono text-xs text-indigo-300 space-y-2 overflow-y-auto border border-white/5">
                      {logs.length === 0 ? (
                        <p className="text-slate-600 italic">No execution swarms running currently. Launch one in Workspace.</p>
                      ) : (
                        logs.map((log, i) => <p key={i}>{log}</p>)
                      )}
                    </div>
                  </div>
                </div>

                {/* Agent Swarm Status */}
                <div className="p-6 rounded-2xl bg-slate-950/40 border border-white/5 h-full">
                  <h3 className="text-lg font-bold text-white mb-6 flex items-center gap-2">
                    <Cpu className="text-rose-400 w-5 h-5 animate-pulse" /> Active Agent swarms
                  </h3>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center p-3.5 rounded-xl bg-white/5 border border-white/5">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-indigo-500/20 flex items-center justify-center">
                          <Zap className="text-indigo-400 w-4 h-4 animate-pulse" />
                        </div>
                        <div>
                          <span className="text-sm font-bold text-white block">Script Writer Agent</span>
                          <span className="text-[10px] text-slate-500">Writing emotional hooks</span>
                        </div>
                      </div>
                      <span className="text-xs font-semibold text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded-full">Thinking</span>
                    </div>

                    <div className="flex justify-between items-center p-3.5 rounded-xl bg-white/5 border border-white/5">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-emerald-500/20 flex items-center justify-center">
                          <Check className="text-emerald-400 w-4 h-4" />
                        </div>
                        <div>
                          <span className="text-sm font-bold text-white block">Research Agent</span>
                          <span className="text-[10px] text-slate-500">Mining target contacts</span>
                        </div>
                      </div>
                      <span className="text-xs font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full">Idle</span>
                    </div>

                    <div className="flex justify-between items-center p-3.5 rounded-xl bg-white/5 border border-white/5">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-teal-500/20 flex items-center justify-center">
                          <Zap className="text-teal-400 w-4 h-4 animate-pulse" />
                        </div>
                        <div>
                          <span className="text-sm font-bold text-white block">Cinematic Director Agent</span>
                          <span className="text-[10px] text-slate-500">Supervising prompt arrays</span>
                        </div>
                      </div>
                      <span className="text-xs font-semibold text-teal-400 bg-teal-500/10 px-2 py-0.5 rounded-full">Working</span>
                    </div>
                  </div>
                </div>

              </div>

            </div>
          )}

          {/* =========================================================
              TAB: PROJECT WORKSPACE
              ========================================================= */}
          {activeTab === 'workspace' && (
            <div className="max-w-4xl mx-auto space-y-8">
              
              <div className="p-8 rounded-2xl bg-slate-950/40 border border-white/5 space-y-6">
                <h3 className="text-xl font-bold text-white">Programmatic Campaign Orchestrator</h3>
                <p className="text-slate-400 text-sm leading-relaxed">
                  Select your target geo-location and local business niche. Once triggered, the multi-agent system scrapes leads, executes parallel Firecrawl UX audits, queries local competitors, triggers Gemini 3.5 to programmatically build a response website with active voice mock widgets, and dispatches outbound B2B pitches.
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">Target Business Niche</label>
                    <select 
                      value={selectedNiche}
                      onChange={(e) => setSelectedNiche(e.target.value)}
                      className="w-full bg-slate-900 border border-white/10 rounded-xl px-4 py-3.5 text-white focus:outline-none focus:border-indigo-500 transition"
                    >
                      <option value="Doctors">Doctors</option>
                      <option value="Real Estate">Real Estate</option>
                      <option value="Gyms">Gyms</option>
                      <option value="Cafes">Cafes</option>
                      <option value="Boutiques">Boutiques</option>
                      <option value="Law Firms">Law Firms</option>
                      <option value="HVAC/Plumbing">HVAC/Plumbing</option>
                      <option value="Salons">Salons</option>
                      <option value="Digital Creators">Digital Creators</option>
                      <option value="Private Schools">Private Schools</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">Geographic Location</label>
                    <input 
                      type="text" 
                      value={selectedLocation}
                      onChange={(e) => setSelectedLocation(e.target.value)}
                      placeholder="e.g. Noida, Delhi, New York"
                      className="w-full bg-slate-900 border border-white/10 rounded-xl px-4 py-3.5 text-white focus:outline-none focus:border-indigo-500 transition"
                    />
                  </div>
                </div>

                <div className="pt-4 flex justify-between items-center">
                  <div className="flex gap-2">
                    <span className="px-3 py-1 rounded-md bg-white/5 border border-white/5 text-xs text-slate-400">Database Checkpoints: SQLite Active</span>
                    <span className="px-3 py-1 rounded-md bg-white/5 border border-white/5 text-xs text-slate-400">Outreach: SMTP / Twilio Mocked</span>
                  </div>
                  
                  <button 
                    onClick={runWorkflowPipeline}
                    disabled={campaignRunning}
                    className="px-8 py-4 bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-800 text-white font-bold rounded-xl shadow-xl shadow-indigo-600/30 flex items-center gap-2 transition"
                  >
                    {campaignRunning ? <RefreshCw className="w-5 h-5 animate-spin" /> : <Play className="w-5 h-5" />} 
                    {campaignRunning ? "Pipeline Running..." : "Launch Programmatic Swarm"}
                  </button>
                </div>
              </div>

              {/* Leads Status Table */}
              <div className="p-6 rounded-2xl bg-slate-950/40 border border-white/5">
                <h3 className="text-lg font-bold text-white mb-6">Database Leads Checker</h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm text-slate-400">
                    <thead className="text-xs uppercase tracking-wider text-slate-500 border-b border-white/5">
                      <tr>
                        <th className="pb-3 font-semibold">Business Name</th>
                        <th className="pb-3 font-semibold">Location</th>
                        <th className="pb-3 font-semibold">Niche</th>
                        <th className="pb-3 font-semibold">Pipeline Status</th>
                        <th className="pb-3 font-semibold text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                      {leads.map((lead) => (
                        <tr key={lead.id} className="hover:bg-white/5 transition">
                          <td className="py-4 font-bold text-white">{lead.name}</td>
                          <td className="py-4">{selectedLocation}</td>
                          <td className="py-4">{selectedNiche}</td>
                          <td className="py-4">
                            <span className={`px-2.5 py-0.5 text-xs font-semibold rounded-full ${lead.status === 'Pitched' ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' : 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20'}`}>
                              {lead.status}
                            </span>
                          </td>
                          <td className="py-4 text-right">
                            <button onClick={() => setActiveTab('media')} className="p-2 rounded-lg bg-white/5 border border-white/5 text-slate-300 hover:bg-indigo-600 hover:text-white transition">
                              <Eye className="w-4 h-4" />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

            </div>
          )}

          {/* =========================================================
              TAB: AGENT MANAGER (15 SPECIALIZED AGENTS CONTROL)
              ========================================================= */}
          {activeTab === 'agents' && (
            <div className="max-w-6xl mx-auto space-y-8">
              
              <div className="flex justify-between items-center">
                <div>
                  <h3 className="text-xl font-bold text-white">Agentic Swarms Configuration</h3>
                  <p className="text-slate-400 text-sm">Assign custom prompts, verify active goals, and configure permissions across 15 target agents.</p>
                </div>
                <button className="px-5 py-2.5 bg-white/5 hover:bg-white/10 text-white font-bold rounded-xl border border-white/10 flex items-center gap-2 text-sm transition">
                  <Plus className="w-4 h-4" /> Custom Agent Node
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {agents.map((agent, i) => (
                  <div key={i} className="p-6 rounded-2xl bg-slate-950/40 border border-white/5 hover:border-indigo-500/30 transition duration-300 flex flex-col justify-between min-h-[220px]">
                    <div>
                      <div className="flex justify-between items-start mb-4">
                        <span className="text-xs font-bold text-indigo-400 uppercase tracking-widest bg-indigo-500/10 px-2 py-0.5 rounded">{agent.role}</span>
                        <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
                      </div>
                      <h4 className="text-lg font-bold text-white mb-2">{agent.name}</h4>
                      <p className="text-slate-400 text-xs leading-relaxed">{agent.goal}</p>
                    </div>

                    <div className="pt-6 border-t border-white/5 flex justify-between items-center">
                      <div className="flex gap-2">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${agent.permissions.write ? 'bg-emerald-500/10 text-emerald-400' : 'bg-slate-500/10 text-slate-500'}`}>Write FS</span>
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${agent.permissions.outbound ? 'bg-rose-500/10 text-rose-400' : 'bg-slate-500/10 text-slate-500'}`}>Outbound API</span>
                      </div>
                      
                      <button className="text-[10px] text-slate-400 hover:text-white font-bold uppercase transition">Configure Prompts</button>
                    </div>
                  </div>
                ))}
              </div>

            </div>
          )}

          {/* =========================================================
              TAB: WORKFLOW BUILDER (N8N STYLE CANVAS MOCK)
              ========================================================= */}
          {activeTab === 'workflow' && (
            <div className="max-w-5xl mx-auto space-y-8">
              
              <div className="p-6 rounded-2xl bg-slate-950/40 border border-white/5 flex justify-between items-center">
                <div>
                  <h3 className="text-lg font-bold text-white">Autonomous Flow Graph Designer</h3>
                  <p className="text-slate-400 text-sm">Visual drag-and-drop orchestration chart capturing sequential states and logic conditions.</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-indigo-400 font-semibold bg-indigo-500/10 px-3 py-1.5 rounded-xl border border-indigo-500/20">Saved State Validated</span>
                </div>
              </div>

              {/* Visual Flow chart */}
              <div className="p-8 rounded-3xl bg-[#090d16] border border-white/5 min-h-[400px] flex flex-col items-center justify-center relative overflow-hidden">
                <div className="absolute inset-0 bg-[linear-gradient(to_right,#0e1526_1px,transparent_1px),linear-gradient(to_bottom,#0e1526_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_50%,#000_70%,transparent_100%)]"></div>

                <div className="relative z-10 flex flex-col md:flex-row items-center justify-center gap-8 w-full max-w-4xl">
                  {workflowNodes.map((node, i) => (
                    <React.Fragment key={node.id}>
                      <div className="p-5 rounded-2xl glass-card text-center max-w-[180px] hover:border-indigo-500/60 shadow-lg relative group">
                        <div className="absolute top-[-10px] left-[50%] translate-x-[-50%] px-2 py-0.5 rounded bg-indigo-600 text-[8px] font-bold text-white uppercase tracking-wider">
                          {node.type}
                        </div>
                        <h4 className="text-sm font-bold text-white mb-2">{node.name}</h4>
                        <p className="text-[10px] text-slate-500 leading-relaxed">{node.description}</p>
                        
                        <div className="mt-4 flex items-center justify-center gap-1.5">
                          <span className={`w-2 h-2 rounded-full ${node.status === 'completed' ? 'bg-emerald-500' : node.status === 'active' ? 'bg-indigo-500 animate-ping' : 'bg-slate-700'}`}></span>
                          <span className="text-[9px] font-bold uppercase tracking-widest text-slate-400">{node.status}</span>
                        </div>
                      </div>

                      {i < workflowNodes.length - 1 && (
                        <div className="flex flex-col items-center justify-center text-indigo-500/40 animate-pulse shrink-0">
                          <ArrowRight className="w-6 h-6 rotate-90 md:rotate-0" />
                        </div>
                      )}
                    </React.Fragment>
                  ))}
                </div>
              </div>

            </div>
          )}

          {/* =========================================================
              TAB: MEDIA LIBRARY (IFRAME SANDBOX PREVIEW)
              ========================================================= */}
          {activeTab === 'media' && (
            <div className="max-w-6xl mx-auto space-y-8">
              
              <div>
                <h3 className="text-xl font-bold text-white">Visual Stage Sandbox</h3>
                <p className="text-slate-400 text-sm">Preview programmatically written single-page HTML client templates and deployed lead landing sites.</p>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                
                {/* Deployed leads list */}
                <div className="space-y-4">
                  <div className="p-4 rounded-xl bg-indigo-600/10 border border-indigo-500/25 flex justify-between items-center">
                    <div>
                      <h4 className="text-white font-bold text-sm">Apex Realty Noida</h4>
                      <span className="text-[10px] text-indigo-300">Live Preview Generated</span>
                    </div>
                    <span className="text-xs font-bold text-white bg-indigo-600 px-2.5 py-1 rounded-md cursor-pointer flex items-center gap-1">
                      Active <Eye className="w-3 h-3" />
                    </span>
                  </div>

                  <div className="p-4 rounded-xl bg-white/5 border border-white/5 flex justify-between items-center opacity-60">
                    <div>
                      <h4 className="text-white font-bold text-sm">Noida Luxury Living</h4>
                      <span className="text-[10px] text-slate-500">Website Auditing Phase</span>
                    </div>
                    <span className="text-xs font-bold text-slate-400 bg-white/5 px-2.5 py-1 rounded-md">
                      Queued
                    </span>
                  </div>
                </div>

                {/* Iframe Live Browser Sandbox */}
                <div className="lg:col-span-2 p-6 rounded-3xl bg-slate-950/80 border border-white/10 backdrop-blur-2xl overflow-hidden flex flex-col min-h-[600px]">
                  <div className="h-10 border-b border-white/10 flex items-center gap-2 px-4 shrink-0">
                    <span className="w-3 h-3 rounded-full bg-rose-500"></span>
                    <span className="w-3 h-3 rounded-full bg-yellow-500"></span>
                    <span className="w-3 h-3 rounded-full bg-emerald-500"></span>
                    <span className="ml-4 text-xs font-mono text-slate-500 flex-1 truncate bg-black/45 px-3 py-1 rounded border border-white/5">https://preview.cinemaos.agency/deployments/lead_real_1/index.html</span>
                  </div>
                  
                  {/* Sandbox Frame */}
                  <div className="flex-1 rounded-b-2xl overflow-hidden bg-slate-900 flex flex-col items-center justify-center p-6 text-center">
                    <div className="max-w-md space-y-4">
                      <div className="w-16 h-16 rounded-full bg-indigo-600/10 border border-indigo-500/20 flex items-center justify-center mx-auto">
                        <Sparkles className="text-indigo-400 w-8 h-8 animate-pulse" />
                      </div>
                      <h4 className="text-lg font-bold text-white">Live Site Sandbox Sandbox</h4>
                      <p className="text-slate-400 text-xs leading-relaxed">
                        To guarantee perfect preview testing, open the generated file locally at <code className="text-indigo-300 font-mono">backend/builds/lead_real_1/index.html</code> in your browser. This sandbox shows where the AWS/Vercel preview dashboard binds instantly once launched.
                      </p>
                    </div>
                  </div>
                </div>

              </div>

            </div>
          )}

          {/* =========================================================
              TAB: SETTINGS (KEYS SETUP)
              ========================================================= */}
          {activeTab === 'settings' && (
            <div className="max-w-2xl mx-auto space-y-8">
              
              <div className="p-8 rounded-2xl bg-slate-950/40 border border-white/5 space-y-6">
                <div>
                  <h3 className="text-lg font-bold text-white mb-2 flex items-center gap-2"><Settings className="text-indigo-400 w-5 h-5" /> Orchestration Keychains</h3>
                  <p className="text-slate-400 text-xs">Enter your external third-party credential vaults below to activate production scraping, audits, and LLM page designs.</p>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">Groq Llama 3.3 API Key</label>
                    <input 
                      type="password" 
                      value={apiKeys.groq}
                      onChange={(e) => setApiKeys({...apiKeys, groq: e.target.value})}
                      className="w-full bg-slate-900 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:indigo-500 transition font-mono text-sm"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">Google Gemini 3.5 API Key</label>
                    <input 
                      type="password" 
                      value={apiKeys.gemini}
                      onChange={(e) => setApiKeys({...apiKeys, gemini: e.target.value})}
                      className="w-full bg-slate-900 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:indigo-500 transition font-mono text-sm"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">Tavily API Key</label>
                      <input 
                        type="password" 
                        value={apiKeys.tavily}
                        onChange={(e) => setApiKeys({...apiKeys, tavily: e.target.value})}
                        className="w-full bg-slate-900 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:indigo-500 transition font-mono text-sm"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">Firecrawl Scrape API Key</label>
                      <input 
                        type="password" 
                        value={apiKeys.firecrawl}
                        onChange={(e) => setApiKeys({...apiKeys, firecrawl: e.target.value})}
                        className="w-full bg-slate-900 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:indigo-500 transition font-mono text-sm"
                      />
                    </div>
                  </div>
                </div>

                <div className="pt-4 border-t border-white/5 flex justify-end">
                  <button className="px-6 py-3 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-xl transition text-sm">Save Encryption Keys</button>
                </div>
              </div>

            </div>
          )}

          {/* =========================================================
              TAB: BILLING
              ========================================================= */}
          {activeTab === 'billing' && (
            <div className="max-w-4xl mx-auto space-y-8">
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="p-6 rounded-2xl bg-slate-950/40 border border-white/5 flex flex-col justify-between min-h-[300px]">
                  <div>
                    <span className="text-xs text-slate-500 font-bold uppercase tracking-widest">Asset Builder</span>
                    <span className="block text-3xl font-black text-white mt-2">$99<span className="text-xs text-slate-500 font-normal">/mo</span></span>
                    <p className="text-slate-400 text-xs mt-4">Ideal for agencies launching local B2B lead generation crawls on a budget.</p>
                  </div>
                  <button className="w-full py-3 bg-white/5 hover:bg-white/10 border border-white/10 text-white font-bold rounded-xl text-sm transition">Activate Starter</button>
                </div>

                <div className="p-6 rounded-2xl bg-indigo-950/20 border border-indigo-500/30 flex flex-col justify-between min-h-[300px] relative overflow-hidden">
                  <div className="absolute top-0 right-0 bg-indigo-600 text-white font-bold uppercase tracking-widest text-[8px] px-3 py-1 rounded-bl">Popular</div>
                  <div>
                    <span className="text-xs text-indigo-400 font-bold uppercase tracking-widest">Swarm Orchestrator</span>
                    <span className="block text-3xl font-black text-white mt-2">$299<span className="text-xs text-slate-500 font-normal">/mo</span></span>
                    <p className="text-indigo-200/70 text-xs mt-4">15 specialized agents active, parallel Firecrawl scans, custom Llama profiling.</p>
                  </div>
                  <button className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-xl text-sm transition shadow-lg shadow-indigo-600/25">Deploy Swarms</button>
                </div>

                <div className="p-6 rounded-2xl bg-slate-950/40 border border-white/5 flex flex-col justify-between min-h-[300px]">
                  <div>
                    <span className="text-xs text-slate-500 font-bold uppercase tracking-widest">Enterprise Automator</span>
                    <span className="block text-3xl font-black text-white mt-2">$999<span className="text-xs text-slate-500 font-normal">/mo</span></span>
                    <p className="text-slate-400 text-xs mt-4">API credit loops dynamically refilled, custom PG vector database mappings.</p>
                  </div>
                  <button className="w-full py-3 bg-white/5 hover:bg-white/10 border border-white/10 text-white font-bold rounded-xl text-sm transition">Contact Architect</button>
                </div>
              </div>

            </div>
          )}

          {/* =========================================================
              TAB: TEAM COLLABORATION
              ========================================================= */}
          {activeTab === 'team' && (
            <div className="max-w-3xl mx-auto space-y-8">
              
              <div className="p-6 rounded-2xl bg-slate-950/40 border border-white/5 space-y-6">
                <div className="flex justify-between items-center border-b border-white/5 pb-4">
                  <div>
                    <h3 className="text-lg font-bold text-white">Agency Team Members</h3>
                    <p className="text-slate-500 text-xs">Manage seat licenses, campaign invite tokens, and roles.</p>
                  </div>
                  <button className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-xl text-xs transition">Invite Lead Gen Architect</button>
                </div>

                <div className="space-y-4">
                  <div className="flex justify-between items-center p-3.5 rounded-xl bg-white/5 border border-white/5">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-full bg-indigo-600/30 flex items-center justify-center font-bold text-indigo-400 text-sm">GA</div>
                      <div>
                        <span className="text-sm font-bold text-white block">Growth Architect (You)</span>
                        <span className="text-[10px] text-slate-500">owner@systemforrevenue.com</span>
                      </div>
                    </div>
                    <span className="text-xs font-semibold text-slate-400 bg-white/5 px-2.5 py-0.5 rounded-full border border-white/5">Owner Role</span>
                  </div>

                  <div className="flex justify-between items-center p-3.5 rounded-xl bg-white/5 border border-white/5 opacity-70">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-full bg-slate-700/30 flex items-center justify-center font-bold text-slate-400 text-sm">JD</div>
                      <div>
                        <span className="text-sm font-bold text-white block">Junior Developer</span>
                        <span className="text-[10px] text-slate-500">support@cinemaos.agency</span>
                      </div>
                    </div>
                    <span className="text-xs font-semibold text-slate-400 bg-white/5 px-2.5 py-0.5 rounded-full border border-white/5">Editor Access</span>
                  </div>
                </div>
              </div>

            </div>
          )}

        </div>
      </main>
    </div>
  );
}
