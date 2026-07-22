import React, { useState, useMemo } from 'react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { Play, TrendingDown, ArrowRight, MapPin } from 'lucide-react';
import { mockWards } from '../mock/data';

// Filter for actionable wards (AQI >= 200) and sort by severity
const actionableWards = mockWards.filter(w => w.aqi >= 200).sort((a, b) => b.aqi - a.aqi);

const interventionTypes = [
  { name: 'Multi-Agency Intervention', maxDrop: 0.45 },
  { name: 'Construction Ban', maxDrop: 0.35 },
  { name: 'Traffic Restrictions', maxDrop: 0.25 },
  { name: 'Anti-Smog Guns', maxDrop: 0.15 },
  { name: 'Water Sprinklers', maxDrop: 0.10 }
];

export const ScenarioSimulation: React.FC = () => {
  const [simulated, setSimulated] = useState(false);
  const [intensity, setIntensity] = useState(75);
  const [selectedWardId, setSelectedWardId] = useState(actionableWards[0].id);
  const [interventionType, setInterventionType] = useState(interventionTypes[0].name);

  const selectedWard = actionableWards.find(w => w.id === selectedWardId) || actionableWards[0];
  const selectedIntervention = interventionTypes.find(i => i.name === interventionType) || interventionTypes[0];

  // Dynamic baseline naturally dropping slightly
  const dynamicBaseline = useMemo(() => {
    return Array.from({ length: 7 }, (_, i) => ({
      hour: `${i * 4}h`,
      AQI: Math.max(0, Math.round(selectedWard.aqi - (i * 2)))
    }));
  }, [selectedWard.aqi]);

  // Dynamic intervention based on intensity, intervention type, and starting AQI
  const dynamicIntervention = useMemo(() => {
    const maxDropPercent = (intensity / 100) * selectedIntervention.maxDrop;
    const totalDrop = Math.round(selectedWard.aqi * maxDropPercent);
    return Array.from({ length: 7 }, (_, i) => ({
      hour: `${i * 4}h`,
      AQI: Math.max(0, Math.round(selectedWard.aqi - (i * (totalDrop / 6))))
    }));
  }, [selectedWard.aqi, intensity, selectedIntervention.maxDrop]);

  const peakAqi = dynamicBaseline[0].AQI;
  const targetBaselineAqi = dynamicBaseline[6].AQI;
  const targetInterventionAqi = dynamicIntervention[6].AQI;
  const reduction = peakAqi - targetInterventionAqi;
  
  // Calculate dynamic y-axis boundaries
  const yMin = Math.max(0, Math.floor((targetInterventionAqi - 30) / 10) * 10);
  const yMax = Math.ceil((peakAqi + 20) / 10) * 10;

  const handleWardChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedWardId(e.target.value);
    setSimulated(false); // Reset to ensure they have to execute simulation again for the new ward
  };

  const handleInterventionChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setInterventionType(e.target.value);
    setSimulated(false);
  };

  return (
    <div className="px-8 py-6 space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4 pb-4 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 mb-1">Predictive Scenario Simulator</h1>
          <p className="text-sm font-medium text-slate-500">Counterfactual atmospheric dispersion modelling and intervention curves</p>
        </div>
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2 bg-white border border-slate-200 rounded-xl px-3 py-1.5 shadow-sm">
            <MapPin className="w-4 h-4 text-slate-500" />
            <select 
              value={selectedWardId} 
              onChange={handleWardChange}
              className="bg-transparent text-sm font-semibold text-slate-800 focus:outline-none cursor-pointer max-w-[200px] truncate"
            >
              {actionableWards.map(w => (
                <option key={w.id} value={w.id}>
                  {w.name} ({w.aqi} AQI)
                </option>
              ))}
            </select>
          </div>
          <button
            onClick={() => setSimulated(true)}
            className="ui-button-primary shrink-0"
          >
            <Play className="h-4 w-4 fill-current" /> Execute Simulation
          </button>
        </div>
      </div>

      {/* Control Card */}
      <div className="ui-card space-y-4">
        <div className="flex flex-col sm:flex-row gap-8">
          <div className="flex-1 space-y-2">
            <label className="text-sm font-medium text-slate-700 block">Select Intervention Type:</label>
            <select
              value={interventionType}
              onChange={handleInterventionChange}
              className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm font-semibold text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer"
            >
              {interventionTypes.map(type => (
                <option key={type.name} value={type.name}>{type.name}</option>
              ))}
            </select>
          </div>
          <div className="flex-1 space-y-2">
            <div className="flex justify-between items-center text-sm font-medium text-slate-700">
              <span>Deployment Intensity:</span>
              <span className="text-blue-600 font-bold">{intensity}%</span>
            </div>
            <div className="pt-2">
              <input
                type="range"
                min="0"
                max="100"
                value={intensity}
                onChange={(e) => {
                  setIntensity(Number(e.target.value));
                  setSimulated(false);
                }}
                className="w-full accent-blue-600 bg-slate-200 rounded-lg cursor-pointer h-2"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Scenario Comparisons */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="ui-card space-y-3">
          <div className="flex justify-between items-center pb-2 border-b border-slate-200">
            <h2 className="text-sm font-semibold text-red-700 uppercase">Scenario A: Status Quo (No Action)</h2>
            <span className="text-xs font-semibold px-2.5 py-0.5 bg-red-50 text-red-700 rounded-full border border-red-200">{targetBaselineAqi} Target AQI</span>
          </div>
          <div className="h-60">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={dynamicBaseline}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                <XAxis dataKey="hour" stroke="#64748B" fontSize={12} />
                <YAxis stroke="#64748B" fontSize={12} domain={[yMin, yMax]} />
                <Tooltip contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#E2E8F0', borderRadius: '12px', color: '#0F172A' }} />
                <Line type="monotone" dataKey="AQI" stroke="#DC2626" strokeWidth={2.5} dot={{ fill: '#DC2626', r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="ui-card space-y-3">
          <div className="flex justify-between items-center pb-2 border-b border-slate-200">
            <h2 className="text-sm font-semibold text-emerald-700 uppercase">Scenario B: {interventionType}</h2>
            <span className="text-xs font-semibold px-2.5 py-0.5 bg-emerald-50 text-emerald-700 rounded-full border border-emerald-200">{targetInterventionAqi} Target AQI</span>
          </div>
          <div className="h-60">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={simulated ? dynamicIntervention : dynamicBaseline}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                <XAxis dataKey="hour" stroke="#64748B" fontSize={12} />
                <YAxis stroke="#64748B" fontSize={12} domain={[yMin, yMax]} />
                <Tooltip contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#E2E8F0', borderRadius: '12px', color: '#0F172A' }} />
                <Line type="monotone" dataKey="AQI" stroke="#16A34A" strokeWidth={2.5} dot={{ fill: '#16A34A', r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {simulated && (
        <div className="bg-emerald-50 border border-emerald-200 p-6 rounded-2xl flex items-center justify-between shadow-sm mt-6">
          <div className="flex items-center gap-4">
            <TrendingDown className="h-8 w-8 text-emerald-600" />
            <div>
              <div className="text-base font-bold text-emerald-900">PROJECTED REDUCTION: -{reduction} AQI POINTS</div>
              <p className="text-xs font-normal text-emerald-800 mt-0.5">
                {selectedWard.name} forecasted to improve significantly within 24 hours post-enforcement.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-sm font-semibold text-emerald-900">
            <span>{peakAqi} Peak</span> <ArrowRight className="h-4 w-4" /> <span>{targetInterventionAqi} Target</span>
          </div>
        </div>
      )}
    </div>
  );
};