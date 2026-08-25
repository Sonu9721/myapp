import { useCallback, useEffect, useMemo, useState } from 'react'
import { Activity, Bot, Building2, CheckCircle2, Database, Download, ExternalLink, Globe2, Loader2, MapPin, Pause, Play, RefreshCw, Rocket, Send, ShieldCheck, Sparkles } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { ParticleBackground } from './components/ParticleBackground'

type Tab = 'overview' | 'campaigns' | 'leads' | 'setup'
type Health = { status: string; version: string; model: string; openai_configured: boolean; google_places_configured: boolean; outreach_mode: string }
type PublicConfig = { niches: string[]; niche_keywords: Record<string, string[]>; total_keywords: number; india_location_count: number; model: string; max_campaign_tasks: number; max_results_per_query: number; outreach_mode: string }
type Stats = { leads: number; profiles: number; campaigns: number; drafts: number; sent: number }
type Campaign = { id: string; name: string; provider: string; status: string; outreach_approved: boolean; total_tasks: number; completed_tasks: number; leads_processed: number; sites_generated: number; drafts_prepared: number; sent_count: number; error_message?: string | null; created_at: string }
type Lead = { id: string; name: string; phone?: string | null; email?: string | null; website?: string | null; niche: string; location: string; status: string; source?: string | null; google_maps_uri?: string | null; rating?: number | null; review_count?: number | null; found_via_keyword?: string | null; data_quality_score?: number }
type CampaignLog = { id: number; stage: string; level: string; message: string; created_at: string }

const jsonHeaders = { 'Content-Type': 'application/json' }

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, options)
  const body = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(body.detail || `Request failed (${response.status})`)
  return body as T
}

function statusClass(status: string) {
  if (status === 'completed') return 'status success'
  if (status.includes('error') || status === 'failed' || status === 'blocked') return 'status danger'
  if (status === 'running' || status === 'starting') return 'status active'
  return 'status neutral'
}

export default function App() {
  const [tab, setTab] = useState<Tab>('overview')
  const [health, setHealth] = useState<Health | null>(null)
  const [config, setConfig] = useState<PublicConfig | null>(null)
  const [stats, setStats] = useState<Stats>({ leads: 0, profiles: 0, campaigns: 0, drafts: 0, sent: 0 })
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [leads, setLeads] = useState<Lead[]>([])
  const [logs, setLogs] = useState<CampaignLog[]>([])
  const [selectedCampaign, setSelectedCampaign] = useState<string>('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const [name, setName] = useState('Noida OPC pilot')
  const [provider, setProvider] = useState<'mock' | 'google_places'>('mock')
  const [selectedNiches, setSelectedNiches] = useState<string[]>(['Real Estate'])
  const [locationsText, setLocationsText] = useState('Noida, Uttar Pradesh, India')
  const [resultsPerQuery, setResultsPerQuery] = useState(5)
  const [analyseBusinesses, setAnalyseBusinesses] = useState(false)
  const [generateSites, setGenerateSites] = useState(false)
  const [prepareOutreach, setPrepareOutreach] = useState(false)
  const [approveOutreach, setApproveOutreach] = useState(false)

  const refresh = useCallback(async () => {
    try {
      const [nextHealth, nextConfig, nextStats, nextCampaigns, nextLeads] = await Promise.all([
        request<Health>('/api/health'), request<PublicConfig>('/api/config'), request<Stats>('/api/stats'),
        request<Campaign[]>('/api/campaigns'), request<Lead[]>('/api/leads?limit=200'),
      ])
      setHealth(nextHealth); setConfig(nextConfig); setStats(nextStats); setCampaigns(nextCampaigns); setLeads(nextLeads)
      if (!selectedCampaign && nextCampaigns[0]) setSelectedCampaign(nextCampaigns[0].id)
      setError('')
    } catch (err) { setError(err instanceof Error ? err.message : 'Could not reach the backend') }
  }, [selectedCampaign])

  useEffect(() => { refresh() }, [refresh])
  useEffect(() => {
    const timer = window.setInterval(refresh, 4000)
    return () => window.clearInterval(timer)
  }, [refresh])
  useEffect(() => {
    if (!selectedCampaign) return
    request<CampaignLog[]>(`/api/campaigns/${selectedCampaign}/logs`).then(setLogs).catch(() => setLogs([]))
  }, [selectedCampaign, campaigns])

  const activeCampaign = campaigns.find(item => item.id === selectedCampaign)
  const activeCount = campaigns.filter(item => item.status === 'running').length
  const setupReady = Boolean(health?.openai_configured && health?.google_places_configured)
  const progress = activeCampaign?.total_tasks ? Math.round((activeCampaign.completed_tasks / activeCampaign.total_tasks) * 100) : 0
  const metricItems: Array<{ label: string; value: number; Icon: LucideIcon }> = [
    { label: 'Businesses', value: stats.leads, Icon: Database },
    { label: 'Analysed', value: stats.profiles, Icon: Bot },
    { label: 'Campaigns', value: stats.campaigns, Icon: Rocket },
    { label: 'Drafts', value: stats.drafts, Icon: Send },
    { label: 'Sent', value: stats.sent, Icon: CheckCircle2 },
  ]

  const locations = useMemo(() => locationsText.split('\n').map(line => line.trim()).filter(Boolean).map(line => {
    const [city = '', state = '', country = 'India'] = line.split(',').map(value => value.trim())
    return { city, state: state || city, country: country || 'India' }
  }), [locationsText])
  const keywordCount = selectedNiches.reduce((total, niche) => total + (config?.niche_keywords[niche]?.length || 0), 0)
  const selectedJobCount = keywordCount * locations.length

  function toggleNiche(niche: string) {
    setSelectedNiches(current => current.includes(niche) ? current.filter(item => item !== niche) : [...current, niche])
  }

  async function createAndRun(allIndia = false) {
    setBusy(true); setError('')
    try {
      const payload = { name, niches: selectedNiches, provider, results_per_query: resultsPerQuery, analyse_businesses: analyseBusinesses, generate_sites: generateSites, prepare_outreach: prepareOutreach, outreach_approved: approveOutreach }
      const campaign = allIndia
        ? await request<Campaign>('/api/campaigns/india', { method: 'POST', headers: jsonHeaders, body: JSON.stringify(payload) })
        : await request<Campaign>('/api/campaigns', { method: 'POST', headers: jsonHeaders, body: JSON.stringify({ ...payload, locations }) })
      setSelectedCampaign(campaign.id)
      await request(`/api/campaigns/${campaign.id}/run`, { method: 'POST' })
      setTab('campaigns')
      await refresh()
    } catch (err) { setError(err instanceof Error ? err.message : 'Campaign could not be created') }
    finally { setBusy(false) }
  }

  async function campaignAction(id: string, action: 'run' | 'pause') {
    setBusy(true)
    try { await request(`/api/campaigns/${id}/${action}`, { method: 'POST' }); await refresh() }
    catch (err) { setError(err instanceof Error ? err.message : 'Action failed') }
    finally { setBusy(false) }
  }

  return <div className="app-shell">
    <ParticleBackground />
    <aside className="sidebar">
      <div className="brand"><span className="brand-mark"><Sparkles size={22}/></span><div><strong>CinemaOS</strong><small>AI OPC Engine</small></div></div>
      <nav>
        {([['overview', Activity, 'Overview'], ['campaigns', Rocket, 'Campaigns'], ['leads', Building2, 'Businesses'], ['setup', ShieldCheck, 'Setup & safety']] as const).map(([id, Icon, label]) =>
          <button key={id} className={tab === id ? 'nav-active' : ''} onClick={() => setTab(id)}><Icon size={18}/>{label}</button>)}
      </nav>
      <div className="sidebar-foot"><span className={health?.status === 'ok' ? 'dot online' : 'dot'}></span><div><strong>{health?.status === 'ok' ? 'Backend online' : 'Backend offline'}</strong><small>{health?.model || 'Connecting…'}</small></div></div>
    </aside>

    <main className="main">
      <header><div><span className="eyebrow">One-person company control plane</span><h1>{tab === 'overview' ? 'Operating overview' : tab === 'campaigns' ? 'Campaign automation' : tab === 'leads' ? 'Business pipeline' : 'Configuration & guardrails'}</h1></div><button className="icon-button" onClick={refresh}><RefreshCw size={18}/></button></header>
      {error && <div className="alert danger"><strong>Action needed:</strong> {error}</div>}

      {tab === 'overview' && <>
        <section className="hero-card"><div><span className="eyebrow">Real automation, controlled execution</span><h2>Discover → analyse → build → draft → approve</h2><p>Every niche and location is handled as a separate resumable task. Duplicate businesses are reused, failures are logged, and outreach remains draft-only until two approvals are present.</p></div><div className="readiness"><div className={health?.openai_configured ? 'ready' : ''}><Bot size={18}/><span>GPT‑5.6 Sol</span><strong>{health?.openai_configured ? 'Ready' : 'Key needed'}</strong></div><div className={health?.google_places_configured ? 'ready' : ''}><MapPin size={18}/><span>Google Places</span><strong>{health?.google_places_configured ? 'Ready' : 'Key needed'}</strong></div></div></section>
        <section className="metric-grid">
          {metricItems.map(({ label, value, Icon }) => <article className="metric" key={label}><Icon size={20}/><span>{label}</span><strong>{value}</strong></article>)}
        </section>
        <section className="two-col"><article className="panel"><div className="panel-title"><h3>Current activity</h3><span className="status active">{activeCount} running</span></div>{campaigns.slice(0, 5).map(item => <button className="campaign-row" key={item.id} onClick={() => { setSelectedCampaign(item.id); setTab('campaigns') }}><div><strong>{item.name}</strong><small>{item.completed_tasks}/{item.total_tasks} location-niche jobs · {item.leads_processed} businesses</small></div><span className={statusClass(item.status)}>{item.status}</span></button>)}{!campaigns.length && <p className="empty">No campaigns yet. Create a safe mock pilot first.</p>}</article><article className="panel"><h3>Production readiness</h3><ul className="checklist"><li className={health?.openai_configured ? 'done' : ''}>OpenAI API key on the server</li><li className={health?.google_places_configured ? 'done' : ''}>Google Places API key on the server</li><li className={health?.outreach_mode === 'approved' ? 'done' : ''}>Outbound delivery explicitly enabled</li><li className={setupReady ? 'done' : ''}>Core discovery and AI services ready</li></ul></article></section>
      </>}

      {tab === 'campaigns' && <section className="campaign-layout">
        <article className="panel form-panel"><div className="panel-title"><div><span className="eyebrow">New campaign</span><h3>Process locations one by one</h3></div></div>
          <label>Campaign name<input value={name} onChange={e => setName(e.target.value)}/></label>
          <div className="field-grid"><label>Data provider<select value={provider} onChange={e => setProvider(e.target.value as 'mock' | 'google_places')}><option value="mock">Safe mock data</option><option value="google_places">Google Places API</option></select></label><label>Results per keyword<input type="number" min="1" max={config?.max_results_per_query || 20} value={resultsPerQuery} onChange={e => setResultsPerQuery(Number(e.target.value))}/></label></div>
          <fieldset><legend>Business types</legend><div className="actions compact"><button type="button" className="secondary" onClick={() => setSelectedNiches(config?.niches || [])}>Select all niches</button><button type="button" className="secondary" onClick={() => setSelectedNiches([])}>Clear</button></div><div className="chip-grid">{config?.niches.map(niche => <button type="button" key={niche} className={selectedNiches.includes(niche) ? 'chip selected' : 'chip'} onClick={() => toggleNiche(niche)}>{niche}<small>{config.niche_keywords[niche]?.length || 0} keywords</small></button>)}</div></fieldset>
          <label>Locations <small>One per line: City, State, Country</small><textarea rows={4} value={locationsText} onChange={e => setLocationsText(e.target.value)}/></label>
          <div className="job-estimate"><strong>{selectedJobCount}</strong><span>resumable keyword jobs · up to {selectedJobCount * resultsPerQuery} raw matches</span></div>
          <div className="toggle-list"><label><input type="checkbox" checked={analyseBusinesses} onChange={e => setAnalyseBusinesses(e.target.checked)}/>Analyse each new business with GPT‑5.6 Sol</label><label><input type="checkbox" checked={generateSites} onChange={e => setGenerateSites(e.target.checked)}/>Generate concept websites (also enables analysis)</label><label><input type="checkbox" checked={prepareOutreach} onChange={e => setPrepareOutreach(e.target.checked)}/>Prepare outreach drafts (also enables analysis)</label><label className="warning-toggle"><input type="checkbox" checked={approveOutreach} onChange={e => setApproveOutreach(e.target.checked)}/>Approve sending for verified contacts (server approval is also required)</label></div>
          <div className="actions"><button className="primary" disabled={busy || !selectedNiches.length || !locations.length} onClick={() => createAndRun(false)}>{busy ? <Loader2 className="spin" size={18}/> : <Play size={18}/>}Run selected locations</button><button className="secondary" disabled={busy || !selectedNiches.length} onClick={() => createAndRun(true)}><Globe2 size={18}/>Run India starter queue</button></div>
          <p className="fine-print">Machine order: location → niche → keyword. Every keyword is checkpointed, retries up to three times, and duplicate Place IDs are merged. India queue: {config?.india_location_count || 36} representative locations. Start scrape-only; enable AI stages after checking data and cost.</p>
        </article>

        <article className="panel execution-panel"><div className="panel-title"><h3>Execution</h3>{activeCampaign && <span className={statusClass(activeCampaign.status)}>{activeCampaign.status}</span>}</div>
          <select value={selectedCampaign} onChange={e => setSelectedCampaign(e.target.value)}><option value="">Select campaign</option>{campaigns.map(item => <option value={item.id} key={item.id}>{item.name}</option>)}</select>
          {activeCampaign ? <><div className="progress"><div style={{width: `${progress}%`}}></div></div><div className="progress-label"><span>{activeCampaign.completed_tasks}/{activeCampaign.total_tasks} keyword jobs</span><strong>{progress}%</strong></div><div className="mini-metrics"><span><strong>{activeCampaign.leads_processed}</strong> unique leads</span><span><strong>{activeCampaign.sites_generated}</strong> sites</span><span><strong>{activeCampaign.drafts_prepared}</strong> drafts</span><span><strong>{activeCampaign.sent_count}</strong> sent</span></div><div className="actions"><button className="secondary" disabled={busy || activeCampaign.status === 'running'} onClick={() => campaignAction(activeCampaign.id, 'run')}><Play size={16}/>Run / resume</button><button className="secondary" disabled={busy || activeCampaign.status !== 'running'} onClick={() => campaignAction(activeCampaign.id, 'pause')}><Pause size={16}/>Pause safely</button><a className="secondary" href={`/api/campaigns/${activeCampaign.id}/export.csv`}><Download size={16}/>Download CSV</a></div>{activeCampaign.error_message && <div className="alert danger">{activeCampaign.error_message}</div>}<div className="log-stream">{logs.map(log => <p className={log.level === 'error' ? 'log-error' : ''} key={log.id}><time>{new Date(log.created_at).toLocaleTimeString()}</time><b>{log.stage}</b>{log.message}</p>)}{!logs.length && <p className="empty">Logs appear here when the campaign starts.</p>}</div></> : <p className="empty">Create or select a campaign to see progress.</p>}
        </article>
      </section>}

      {tab === 'leads' && <section className="panel"><div className="panel-title"><div><span className="eyebrow">Deduplicated pipeline</span><h3>{leads.length} recent businesses</h3></div></div><div className="table-wrap"><table><thead><tr><th>Business</th><th>Niche, location & keyword</th><th>Contact</th><th>Status</th><th>Evidence</th></tr></thead><tbody>{leads.map(lead => <tr key={lead.id}><td><strong>{lead.name}</strong><small>{lead.source || 'legacy'}</small></td><td>{lead.niche}<small>{lead.location}</small><small>Found via: {lead.found_via_keyword || '—'}</small></td><td>{lead.email || lead.phone || 'Not publicly found'}{lead.website && <a href={lead.website} target="_blank" rel="noreferrer"><ExternalLink size={13}/>Website</a>}</td><td><span className="status neutral">{lead.status}</span><small>Quality {lead.data_quality_score ?? 0}/100</small></td><td>{lead.rating ? `${lead.rating} (${lead.review_count || 0})` : '—'}{lead.google_maps_uri && <a href={lead.google_maps_uri} target="_blank" rel="noreferrer"><MapPin size={13}/>Google Maps</a>}</td></tr>)}</tbody></table></div></section>}

      {tab === 'setup' && <section className="setup-grid"><article className="panel"><span className="eyebrow">Server configuration</span><h3>Secrets stay out of the browser</h3><p>Copy <code>.env.example</code> to <code>.env</code> in the project root and add keys there. Restart the backend after changing it.</p><div className="setup-status"><div><Bot/><span>OpenAI / {health?.model}</span><strong>{health?.openai_configured ? 'Configured' : 'Missing OPENAI_API_KEY'}</strong></div><div><MapPin/><span>Google Places API</span><strong>{health?.google_places_configured ? 'Configured' : 'Missing GOOGLE_PLACES_API_KEY'}</strong></div><div><Send/><span>Outreach delivery</span><strong>{health?.outreach_mode === 'approved' ? 'Server approved' : 'Draft only'}</strong></div></div></article><article className="panel"><span className="eyebrow">Safety model</span><h3>Two-key outbound approval</h3><ol className="numbered"><li>Set <code>OUTREACH_MODE=approved</code> on the server.</li><li>Approve the individual campaign in this dashboard.</li><li>The recipient must not be on the do-not-contact list.</li><li>The run-level delivery cap must not be exceeded.</li></ol><div className="alert">Start with mock mode, then a single city and one niche. Review drafts and data quality before increasing scope.</div></article><article className="panel full"><span className="eyebrow">Google data notice</span><h3>Authorized API use, not Google-page scraping</h3><p>The system uses Places API Text Search and displays Google Maps source links. Google result pages are not scraped. Places data has attribution, storage and caching rules; review them before production and keep the configured source-cache expiry short.</p></article></section>}
    </main>
  </div>
}
