import React, { useState } from 'react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { Play, TrendingDown, ArrowRight } from 'lucide-react';
import { mockScenarioBaseline, mockScenarioIntervention } from '../mock/data';

export const ScenarioSimulation: React.FC = () => {
  const [simulated, setSimulated] = useState(false);
  const [intensity, setIntensity] = useState(75);

  return (
    <div className="px-8 py-6 space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4 pb-4 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 mb-1">Predictive Scenario Simulator</h1>
          <p className="text-sm font-medium text-slate-500">Counterfactual atmospheric dispersion modelling and intervention curves</p>
        </div>
        <button
          onClick={() => setSimulated(true)}
          className="ui-button-primary"
        >
          <Play className="h-4 w-4 fill-current" /> Execute Simulation
        </button>
      </div>

      {/* Control Card */}
      <div className="ui-card space-y-3">
        <div className="flex justify-between items-center text-sm font-medium text-slate-700">
          <span>Anti-Smog Sprinkler Deployment Intensity:</span>
          <span className="text-blue-600 font-bold">{intensity}% Operational Rate</span>
        </div>
        <input
          type="range"
          min="0"
          max="100"
          value={intensity}
          onChange={(e) => setIntensity(Number(e.target.value))}
          className="w-full accent-blue-600 bg-slate-200 rounded-lg cursor-pointer h-2"
        />
      </div>

      {/* Scenario Comparisons */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="ui-card space-y-3">
          <div className="flex justify-between items-center pb-2 border-b border-slate-200">
            <h2 className="text-sm font-semibold text-red-700 uppercase">Scenario A: Status Quo (No Action)</h2>
            <span className="text-xs font-semibold px-2.5 py-0.5 bg-red-50 text-red-700 rounded-full border border-red-200">340 Target AQI</span>
          </div>
          <div className="h-60">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={mockScenarioBaseline}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                <XAxis dataKey="hour" stroke="#64748B" fontSize={12} />
                <YAxis stroke="#64748B" fontSize={12} domain={[200, 400]} />
                <Tooltip contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#E2E8F0', borderRadius: '12px', color: '#0F172A' }} />
                <Line type="monotone" dataKey="AQI" stroke="#DC2626" strokeWidth={2.5} dot={{ fill: '#DC2626', r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="ui-card space-y-3">
          <div className="flex justify-between items-center pb-2 border-b border-slate-200">
            <h2 className="text-sm font-semibold text-emerald-700 uppercase">Scenario B: Multi-Agency Intervention</h2>
            <span className="text-xs font-semibold px-2.5 py-0.5 bg-emerald-50 text-emerald-700 rounded-full border border-emerald-200">250 Target AQI</span>
          </div>
          <div className="h-60">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={simulated ? mockScenarioIntervention : mockScenarioBaseline}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                <XAxis dataKey="hour" stroke="#64748B" fontSize={12} />
                <YAxis stroke="#64748B" fontSize={12} domain={[200, 400]} />
                <Tooltip contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#E2E8F0', borderRadius: '12px', color: '#0F172A' }} />
                <Line type="monotone" dataKey="AQI" stroke="#16A34A" strokeWidth={2.5} dot={{ fill: '#16A34A', r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {simulated && (
        <div className="bg-emerald-50 border border-emerald-200 p-6 rounded-2xl flex items-center justify-between shadow-sm">
          <div className="flex items-center gap-4">
            <TrendingDown className="h-8 w-8 text-emerald-600" />
            <div>
              <div className="text-base font-bold text-emerald-900">PROJECTED REDUCTION: -130 AQI POINTS</div>
              <p className="text-xs font-normal text-emerald-800 mt-0.5">Ward 17 forecasted to exit Severe category within 16 hours post-enforcement.</p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-sm font-semibold text-emerald-900">
            <span>380 Peak</span> <ArrowRight className="h-4 w-4" /> <span>250 Target</span>
          </div>
        </div>
      )}
    </div>
  );
};