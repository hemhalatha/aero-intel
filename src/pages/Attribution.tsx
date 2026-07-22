import React, { useEffect, useState } from 'react';
import { PieChart as RePieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { Bot, RefreshCw, CheckCircle2 } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

type AttributionRanking = {
  source: string;
  score: number;
};

type AttributionApiResponse = {
  hotspot_id: string;
  primary_source: string;
  confidence: number;
  secondary_sources: AttributionRanking[];
  rankings: AttributionRanking[];
};

type EvidenceFactor = {
  label: string;
  contribution: number;
};

type ExplanationApiResponse = {
  hotspot_id: string;
  primary_source: string;
  confidence: number;
  headline: string;
  summary: string;
  evidence: (string | EvidenceFactor)[];
};

const SOURCE_COLORS: Record<string, string> = {
  'Construction Dust': '#FFB800',
  'Vehicular Emission': '#00F0FF',
  'Vehicular Pollution': '#00F0FF',
  'Industrial Emission': '#FF4D4D',
  'Industrial Stack': '#FF4D4D',
  'Road Dust': '#A855F7',
  'Biomass Burning': '#10B981',
};

const HOTSPOT_BUNDLES: Record<string, { name: string; ward: string; bundle: any }> = {
  'HS-801': {
    name: 'Okhla Phase II (Delhi NCR)',
    ward: 'W-17 (Delhi)',
    bundle: {
      hotspot_id: 801,
      traffic: { detected: true, confidence: 0.82 },
      construction: { detected: true, confidence: 0.95 },
      industry: { detected: false, confidence: 0.15 },
      satellite: { detected: true, confidence: 0.88 },
      wind_direction: 'NW',
      wind_speed: 14.0,
      pm25: 240.0,
    },
  },
  'HS-805': {
    name: 'Talkatora Industrial (Lucknow)',
    ward: 'LKO-W-04 (Lucknow)',
    bundle: {
      hotspot_id: 805,
      traffic: { detected: false, confidence: 0.30 },
      construction: { detected: false, confidence: 0.20 },
      industry: { detected: true, confidence: 0.92 },
      satellite: { detected: true, confidence: 0.75 },
      wind_direction: 'NE',
      wind_speed: 10.0,
      pm25: 210.0,
    },
  },
  'HS-802': {
    name: 'Anand Vihar Transport Hub (Delhi NCR)',
    ward: 'W-04 (Delhi)',
    bundle: {
      hotspot_id: 802,
      traffic: { detected: true, confidence: 0.96 },
      construction: { detected: true, confidence: 0.45 },
      industry: { detected: false, confidence: 0.10 },
      satellite: { detected: true, confidence: 0.80 },
      wind_direction: 'W',
      wind_speed: 12.0,
      pm25: 220.0,
    },
  },
  'HS-BLR-001': {
    name: 'Peenya Industrial Station (Bengaluru)',
    ward: 'BLR-W-003 (Bengaluru)',
    bundle: {
      hotspot_id: 1,
      traffic: { detected: true, confidence: 0.70 },
      construction: { detected: true, confidence: 0.90 },
      industry: { detected: true, confidence: 0.40 },
      satellite: { detected: true, confidence: 0.65 },
      wind_direction: 'SW',
      wind_speed: 12.5,
      pm25: 185.0,
    },
  },
  'HS-807': {
    name: 'Navi Mumbai Rabale (Mumbai MMR)',
    ward: 'BOM-W-09 (Mumbai)',
    bundle: {
      hotspot_id: 807,
      traffic: { detected: true, confidence: 0.78 },
      construction: { detected: true, confidence: 0.85 },
      industry: { detected: true, confidence: 0.88 },
      satellite: { detected: true, confidence: 0.72 },
      wind_direction: 'WNW',
      wind_speed: 16.0,
      pm25: 195.0,
    },
  },
  'HS-MAA-001': {
    name: 'Manali Industrial Zone (Chennai)',
    ward: 'MAA-W-01 (Chennai)',
    bundle: {
      hotspot_id: 809,
      traffic: { detected: false, confidence: 0.25 },
      construction: { detected: false, confidence: 0.15 },
      industry: { detected: true, confidence: 0.94 },
      satellite: { detected: true, confidence: 0.70 },
      wind_direction: 'ENE',
      wind_speed: 18.0,
      pm25: 175.0,
    },
  },
};

export const Attribution: React.FC = () => {
  const [selectedHotspotKey, setSelectedHotspotKey] = useState<string>('HS-801');
  const [attribution, setAttribution] = useState<AttributionApiResponse | null>(null);
  const [explanation, setExplanation] = useState<ExplanationApiResponse | null>(null);
  const [isLive, setIsLive] = useState(false);
  const [loading, setLoading] = useState(true);

  const loadAttributionData = async (hotspotKey: string) => {
    setLoading(true);
    const targetConfig = HOTSPOT_BUNDLES[hotspotKey] || HOTSPOT_BUNDLES['HS-801'];
    const sampleBundle = targetConfig.bundle;

    try {
      const [attrRes, expRes] = await Promise.all([
        fetch(`${API_BASE}/api/v1/attributions`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(sampleBundle),
        }),
        fetch(`${API_BASE}/api/v1/explanations`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(sampleBundle),
        }),
      ]);

      if (attrRes.ok && expRes.ok) {
        const attrData = await attrRes.json();
        const expData = await expRes.json();
        setAttribution(attrData);
        setExplanation(expData);
        setIsLive(true);
      } else {
        throw new Error(`API returned ${attrRes.status}`);
      }
    } catch {
      setIsLive(false);
      // Immediate rich fallback data tailored for selected hotspot
      const primary = targetConfig.name.includes('Okhla') || targetConfig.name.includes('Peenya')
        ? 'Construction Dust'
        : targetConfig.name.includes('Talkatora') || targetConfig.name.includes('Manali')
        ? 'Industrial Emission'
        : 'Vehicular Pollution';

      const fallbackRankings: AttributionRanking[] = primary === 'Construction Dust'
        ? [
            { source: 'Construction Dust', score: 85 },
            { source: 'Vehicular Pollution', score: 10 },
            { source: 'Industrial Emission', score: 5 },
          ]
        : primary === 'Industrial Emission'
        ? [
            { source: 'Industrial Emission', score: 78 },
            { source: 'Vehicular Pollution', score: 16 },
            { source: 'Construction Dust', score: 6 },
          ]
        : [
            { source: 'Vehicular Pollution', score: 74 },
            { source: 'Construction Dust', score: 18 },
            { source: 'Industrial Emission', score: 8 },
          ];

      setAttribution({
        hotspot_id: String(sampleBundle.hotspot_id),
        primary_source: primary,
        confidence: 0.92,
        secondary_sources: fallbackRankings.slice(1),
        rankings: fallbackRankings,
      });

      setExplanation({
        hotspot_id: String(sampleBundle.hotspot_id),
        primary_source: primary,
        confidence: 0.92,
        headline: `High Particulate Emission Surge Flagged in ${targetConfig.name}`,
        summary: `Multi-modal evidence scoring and Sentinel-2 satellite sweeps identified ${primary.toLowerCase()} as the primary driver of ambient air pollution in ${targetConfig.ward}.`,
        evidence: [
          `Sentinel-2 Optical Satellite: Surface reflectance signature of exposed unmitigated earth within 500m radius.`,
          `CPCB CAAQMS Station Feed: Multi-channel particulate concentration exceedance recorded over last 4 hours.`,
          `Urban Mobility Index: Heavy commercial transport idling and traffic congestion along arterial freight corridor.`,
        ],
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAttributionData(selectedHotspotKey);
  }, [selectedHotspotKey]);

  const chartData = attribution
    ? attribution.rankings
        .filter((r) => r.score > 0)
        .map((r) => ({
          source: r.source,
          percentage: Math.round(r.score),
          color: SOURCE_COLORS[r.source] || '#3B82F6',
        }))
    : [];

  return (
    <div className="px-8 py-6 space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 pb-4 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 mb-1">Geospatial Source Attribution Engine</h1>
          <p className="text-sm font-medium text-slate-500">
            Multi-modal evidence scoring & statistical apportionment across urban emission categories
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <select
            value={selectedHotspotKey}
            onChange={(e) => setSelectedHotspotKey(e.target.value)}
            className="px-3 py-1.5 rounded-xl border border-slate-300 text-xs font-semibold bg-white text-slate-800 shadow-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
          >
            {Object.entries(HOTSPOT_BUNDLES).map(([key, item]) => (
              <option key={key} value={key}>
                {item.name}
              </option>
            ))}
          </select>
          <span
            className={`inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-semibold ${
              isLive ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : 'border-amber-200 bg-amber-50 text-amber-700'
            }`}
          >
            <CheckCircle2 className="h-3.5 w-3.5" />
            {isLive ? 'Live FastAPI Connected (POST /api/v1/attributions)' : 'Seeded Standby Data'}
          </span>
          <button onClick={() => loadAttributionData(selectedHotspotKey)} className="ui-button-secondary">
            <RefreshCw className={`h-4 w-4 text-slate-500 ${loading ? 'animate-spin' : ''}`} />
            <span>Re-Run AI Attribution</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pie Chart Card */}
        <div className="ui-card space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-base font-semibold text-slate-900">Attributed Source Share</h2>
            {attribution && (
              <span className="text-xs font-bold text-blue-600 bg-blue-50 border border-blue-200 px-2.5 py-1 rounded-full">
                Primary: {attribution.primary_source}
              </span>
            )}
          </div>
          <div className="h-64 flex items-center justify-center">
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <RePieChart>
                  <Pie
                    data={chartData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={90}
                    paddingAngle={4}
                    dataKey="percentage"
                  >
                    {chartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} stroke="#FFFFFF" strokeWidth={2} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(val: number) => [`${val}%`, 'Apportionment Share']}
                    contentStyle={{
                      backgroundColor: '#FFFFFF',
                      borderColor: '#E2E8F0',
                      borderRadius: '12px',
                      boxShadow: '0 4px 12px rgba(0, 0, 0, 0.08)',
                      color: '#0F172A',
                    }}
                  />
                </RePieChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-xs text-slate-400 font-mono">Loading Attribution Data...</div>
            )}
          </div>
          <div className="grid grid-cols-3 gap-2 pt-2 border-t border-slate-100 text-xs font-medium">
            {chartData.map((item) => (
              <div key={item.source} className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: item.color }} />
                <span className="text-slate-600 truncate">{item.source}:</span>
                <span className="font-bold text-slate-900">{item.percentage}%</span>
              </div>
            ))}
          </div>
        </div>

        {/* AI Natural Explanation Card */}
        <div className="ui-card space-y-4 bg-slate-900 text-white relative overflow-hidden">
          <div className="absolute top-0 right-0 w-64 h-64 bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />
          <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
            <Bot className="h-5 w-5 text-blue-400" />
            <h2 className="text-base font-semibold text-white">Explainable AI (XAI) Natural Language Summary</h2>
          </div>

          {explanation ? (
            <div className="space-y-4">
              <div className="p-3.5 bg-slate-800/80 rounded-xl border border-slate-700/80">
                <span className="text-[10px] font-bold text-blue-400 uppercase tracking-wider block mb-1">
                  Automated Headline
                </span>
                <p className="text-sm font-bold text-white leading-snug">{explanation.headline}</p>
              </div>

              <div className="space-y-1.5">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                  Diagnostic Reasoning Summary
                </span>
                <p className="text-xs text-slate-300 leading-relaxed font-normal">{explanation.summary}</p>
              </div>

              <div className="space-y-2 pt-2 border-t border-slate-800">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                  Multi-Modal Supporting Evidence
                </span>
                <div className="space-y-1.5">
                  {explanation.evidence.map((ev, i) => (
                    <div key={i} className="text-xs text-slate-300 flex items-start gap-2 bg-slate-800/40 p-2 rounded-lg border border-slate-700/50">
                      <span className="text-blue-400 font-bold">•</span>
                      <span>{typeof ev === 'string' ? ev : ev.label}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="p-8 text-center text-xs font-mono text-slate-400">Loading AI Natural Explanation...</div>
          )}
        </div>
      </div>
    </div>
  );
};
