import React, { useState } from 'react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip } from 'recharts';
import { Play, TrendingDown, ArrowRight, Sliders } from 'lucide-react';
import { motion } from 'framer-motion';
import { mockScenarioBaseline, mockScenarioIntervention } from '../mock/data';

export const ScenarioSimulation: React.FC = () => {
  const [simulated, setSimulated] = useState(false);
  const [sprinklerIntensity, setSprinklerIntensity] = useState(75);

  return (
    <div className="space-y-6">
      <div className="glass-panel p-5 rounded-xl flex justify-between items-center">
        <div>
          <h2 className="text-lg font-mono font-bold text-white flex items-center gap-2">
            <Sliders className="h-5 w-5 text-brand-cyan" /> PREDICTIVE SCENARIO SIMULATOR
          </h2>
          <p className="text-xs text-gray-400">Counterfactual Atmospheric Dispersion Curves</p>
        </div>
        <button
          onClick={() => setSimulated(true)}
          className="flex items-center gap-2 px-5 py-2.5 bg-brand-cyan hover:bg-cyan-400 text-dark-950 font-mono text-xs font-bold rounded-lg shadow-neon-cyan transition"
        >
          <Play className="h-4 w-4 fill-current" /> EXECUTE SIMULATION ENGINE
        </button>
      </div>

      {/* Slider Controls */}
      <div className="glass-panel p-4 rounded-xl font-mono text-xs space-y-3">
        <div className="flex justify-between">
          <span className="text-gray-400">Anti-Smog Sprinkler Deployment Intensity:</span>
          <span className="text-brand-cyan font-bold">{sprinklerIntensity}% Operational Rate</span>
        </div>
        <input
          type="range"
          min="0"
          max="100"
          value={sprinklerIntensity}
          onChange={(e) => setSprinklerIntensity(Number(e.target.value))}
          className="w-full accent-brand-cyan bg-dark-900 rounded-lg cursor-pointer"
        />
      </div>

      {/* Side-by-Side Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="glass-panel p-5 rounded-xl border-t-2 border-brand-red">
          <h3 className="text-xs font-mono font-bold text-brand-red uppercase mb-4">Scenario A: Status Quo (No Action)</h3>
          <div className="h-60">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={mockScenarioBaseline}>
                <XAxis dataKey="hour" stroke="#6B7280" fontSize={11} />
                <YAxis stroke="#6B7280" fontSize={11} domain={[200, 400]} />
                <Tooltip contentStyle={{ backgroundColor: '#0B0F17', borderColor: '#1F2937' }} />
                <Line type="monotone" dataKey="AQI" stroke="#FF4D4D" strokeWidth={3} dot={{ fill: '#FF4D4D' }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="glass-panel p-5 rounded-xl border-t-2 border-brand-green">
          <h3 className="text-xs font-mono font-bold text-brand-green uppercase mb-4">Scenario B: Multi-Agency Intervention</h3>
          <div className="h-60">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={simulated ? mockScenarioIntervention : mockScenarioBaseline}>
                <XAxis dataKey="hour" stroke="#6B7280" fontSize={11} />
                <YAxis stroke="#6B7280" fontSize={11} domain={[200, 400]} />
                <Tooltip contentStyle={{ backgroundColor: '#0B0F17', borderColor: '#1F2937' }} />
                <Line type="monotone" dataKey="AQI" stroke="#00E676" strokeWidth={3} dot={{ fill: '#00E676' }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {simulated && (
        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          className="glass-panel-cyan p-4 rounded-xl flex items-center justify-between"
        >
          <div className="flex items-center gap-3">
            <TrendingDown className="h-8 w-8 text-brand-green" />
            <div>
              <div className="text-sm font-bold font-mono text-brand-green">PROJECTED REDUCTION: -130 AQI POINTS</div>
              <div className="text-xs text-gray-300 font-mono">Ward 17 exits Severe band within 16 hours post-enforcement.</div>
            </div>
          </div>
          <div className="flex items-center gap-2 text-xs font-mono text-brand-green font-bold">
            <span>380 Peak</span> <ArrowRight className="h-4 w-4" /> <span>250 Target</span>
          </div>
        </motion.div>
      )}
    </div>
  );
};