import React, { useState } from 'react';
import { ShieldCheck, Check, Sparkles } from 'lucide-react';
import { mockRecommendations } from '../mock/data';

export const Recommendations: React.FC = () => {
  const [recs, setRecs] = useState(mockRecommendations);

  const toggleApply = (id: string) => {
    setRecs((prev) => prev.map((r) => (r.id === id ? { ...r, applied: !r.applied } : r)));
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-lg font-mono font-bold text-white flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-brand-cyan" /> AI-RECOMMENDED DISPATCH PROTOCOLS
          </h2>
          <p className="text-xs text-gray-400">Evidence-Backed Municipal Action Directives</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {recs.map((rec) => (
          <div key={rec.id} className={`bg-dark-800 border rounded-xl p-5 flex flex-col justify-between transition-all ${rec.applied ? 'border-brand-green bg-brand-green/5' : 'border-dark-700'}`}>
            <div>
              <div className="flex justify-between items-start mb-3">
                <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold ${rec.priority === 'HIGH' ? 'bg-brand-red/20 text-brand-red' : 'bg-brand-amber/20 text-brand-amber'}`}>
                  {rec.priority} PRIORITY
                </span>
                <span className="text-xs font-mono text-brand-cyan font-bold">{rec.expectedReduction}</span>
              </div>
              <h3 className="text-sm font-bold text-white mb-2">{rec.title}</h3>
              <p className="text-xs text-gray-400 mb-4 leading-relaxed">{rec.description}</p>
            </div>

            <div className="space-y-3 pt-3 border-t border-dark-700">
              <div className="flex justify-between text-xs font-mono">
                <span className="text-gray-500">Target Dept:</span>
                <span className="text-gray-300 font-semibold">{rec.department}</span>
              </div>
              <button
                onClick={() => toggleApply(rec.id)}
                className={`w-full py-2 rounded-lg font-mono text-xs font-bold flex items-center justify-center gap-2 transition ${
                  rec.applied ? 'bg-brand-green text-dark-900' : 'bg-brand-cyan/20 text-brand-cyan border border-brand-cyan/40 hover:bg-brand-cyan/30'
                }`}
              >
                {rec.applied ? <><Check className="h-4 w-4" /> DISPATCHED</> : 'APPLY DIRECTIVE'}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};