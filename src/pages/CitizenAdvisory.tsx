import React, { useState } from 'react';
import { ShieldAlert, Heart, School, Building2 } from 'lucide-react';
import { mockAdvisories } from '../mock/data';

export const CitizenAdvisory: React.FC = () => {
  const [selectedLang, setSelectedLang] = useState('en');
  const activeAdvisory = mockAdvisories.find((a) => a.code === selectedLang) || mockAdvisories[0];

  return (
    <div className="space-y-6">
      <div className="glass-panel p-5 rounded-xl flex justify-between items-center">
        <div>
          <h2 className="text-lg font-mono font-bold text-white">PUBLIC HEALTH & CITIZEN BROADCAST DIRECTIVES</h2>
          <p className="text-xs text-gray-400 font-mono">Ward-Level Multilingual Alerts</p>
        </div>
        <div className="flex gap-2">
          {mockAdvisories.map((a) => (
            <button
              key={a.code}
              onClick={() => setSelectedLang(a.code)}
              className={`px-3 py-1.5 rounded font-mono text-xs font-bold transition ${
                selectedLang === a.code ? 'bg-brand-cyan text-dark-950 shadow-neon-cyan' : 'bg-dark-900 text-gray-400 border border-dark-700'
              }`}
            >
              {a.language}
            </button>
          ))}
        </div>
      </div>

      <div className="glass-panel p-6 rounded-xl border-l-4 border-brand-red">
        <div className="flex items-center gap-3 text-brand-red mb-3 font-mono">
          <ShieldAlert className="h-6 w-6" />
          <span className="text-sm font-bold uppercase">SEVERE AIR POLLUTION PUBLIC EMERGENCY BROADCAST</span>
        </div>
        <p className="text-base text-gray-100 font-mono leading-relaxed bg-dark-900/90 p-5 rounded-lg border border-dark-700">
          "{activeAdvisory.text}"
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-panel p-5 rounded-xl space-y-2">
          <School className="h-6 w-6 text-brand-amber" />
          <h3 className="font-bold text-white text-sm">Schools & Institutions</h3>
          <p className="text-xs text-gray-400">Suspend outdoor sports until AQI drops below 200 band.</p>
        </div>
        <div className="glass-panel p-5 rounded-xl space-y-2">
          <Heart className="h-6 w-6 text-brand-red" />
          <h3 className="font-bold text-white text-sm">Vulnerable Population</h3>
          <p className="text-xs text-gray-400">Elderly & respiratory patients should remain indoors with HEPA filters.</p>
        </div>
        <div className="glass-panel p-5 rounded-xl space-y-2">
          <Building2 className="h-6 w-6 text-brand-cyan" />
          <h3 className="font-bold text-white text-sm">Outdoor Workers</h3>
          <p className="text-xs text-gray-400">Mandatory N95 mask distribution enforced for municipal workers.</p>
        </div>
      </div>
    </div>
  );
};