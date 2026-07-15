import React, { useState } from 'react'
import { createRoot } from 'react-dom/client'
import './styles.css'

const sampleEvidence = {
  hotspot_id: 101,
  traffic: { detected: true, confidence: 0.82 },
  construction: { detected: true, confidence: 0.91 },
  industry: { detected: false, confidence: 0.2 },
  satellite: { detected: true, confidence: 0.74 },
  road_dust: { detected: true, confidence: 0.62 },
  wind_direction: 'North', wind_speed: 18,
  historical_patterns: { construction_match: 0.88, traffic_match: 0.63, road_dust_match: 0.58 }
}
const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

function App() {
  const [result, setResult] = useState(null)
  const [explanation, setExplanation] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  async function runAttribution() {
    setLoading(true); setError('')
    try {
      const options = { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(sampleEvidence) }
      const [attributionResponse, explanationResponse] = await Promise.all([
        fetch(`${apiBase}/api/v1/attributions`, options),
        fetch(`${apiBase}/api/v1/explanations`, options)
      ])
      if (!attributionResponse.ok || !explanationResponse.ok) throw new Error('The decision-support API did not return a result.')
      setResult(await attributionResponse.json())
      setExplanation(await explanationResponse.json())
    } catch (err) { setError(err.message) } finally { setLoading(false) }
  }
  return <main className="min-h-screen bg-slate-950 p-6 text-slate-100 md:p-12">
    <section className="mx-auto max-w-5xl">
      <p className="text-sm font-semibold uppercase tracking-[.2em] text-cyan-400">AI Urban Air Quality Command Center</p>
      <h1 className="mt-2 text-3xl font-bold md:text-5xl">Pollution source attribution</h1>
      <p className="mt-3 max-w-2xl text-slate-400">Rank likely pollution sources from Member 1’s evidence bundle using transparent weighted rules.</p>
      <div className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-6">
        <div className="flex flex-wrap items-center justify-between gap-4"><div><p className="text-sm text-slate-400">Evidence bundle</p><p className="font-semibold">Hotspot #{sampleEvidence.hotspot_id} · Wind north at 18 km/h</p></div><button onClick={runAttribution} disabled={loading} className="rounded-lg bg-cyan-500 px-5 py-3 font-bold text-slate-950 hover:bg-cyan-400 disabled:opacity-60">{loading ? 'Analyzing…' : 'Run attribution'}</button></div>
      </div>
      {error && <p className="mt-5 rounded-lg bg-red-950 p-4 text-red-200">{error}</p>}
      {result && <section className="mt-6 grid gap-6 md:grid-cols-3">
        <article className="rounded-2xl border border-cyan-500/40 bg-cyan-950/30 p-6"><p className="text-sm text-cyan-300">Primary source</p><h2 className="mt-2 text-2xl font-bold">{result.primary_source}</h2><p className="mt-3 text-5xl font-bold text-cyan-300">{result.confidence}%</p><p className="mt-2 text-sm text-slate-400">Attribution confidence</p></article>
        <article className="rounded-2xl border border-slate-800 bg-slate-900 p-6 md:col-span-2"><h2 className="font-bold">All source scores</h2><div className="mt-5 space-y-4">{result.rankings.map(item => <div key={item.source}><div className="mb-1 flex justify-between text-sm"><span>{item.source}</span><span className="font-semibold">{item.score}%</span></div><div className="h-3 overflow-hidden rounded-full bg-slate-800"><div className="h-full rounded-full bg-cyan-400" style={{width: `${item.score}%`}} /></div></div>)}</div></article>
        <article className="rounded-2xl border border-slate-800 bg-slate-900 p-6 md:col-span-3"><h2 className="font-bold">Evidence supporting {result.primary_source}</h2><ul className="mt-4 grid gap-3 md:grid-cols-2">{result.rankings[0].evidence.map(factor => <li key={factor.label} className="rounded-lg bg-slate-800 px-4 py-3 text-sm">✓ {factor.label}<span className="float-right font-semibold text-cyan-300">+{factor.contribution}</span></li>)}</ul></article>
        {explanation && <article className="rounded-2xl border border-violet-500/30 bg-violet-950/20 p-6 md:col-span-3"><p className="text-sm font-semibold uppercase tracking-wider text-violet-300">AI explanation</p><h2 className="mt-2 text-xl font-bold">{explanation.headline}</h2><p className="mt-3 max-w-3xl leading-7 text-slate-300">{explanation.summary}</p></article>}
      </section>}
    </section>
  </main>
}
createRoot(document.getElementById('root')).render(<App />)
