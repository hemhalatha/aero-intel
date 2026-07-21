import React, { useState } from 'react';
import { Sparkles, Check } from 'lucide-react';
import { mockRecommendations } from '../mock/data';

export const Recommendations: React.FC = () => {
  const [recs, setRecs] = useState(mockRecommendations);

  const toggleApply = (id: string) => {
    setRecs((prev) => prev.map((r) => (r.id === id ? { ...r, applied: !r.applied } : r)));
  };

  return (
    <div className="px-8 py-6 space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="pb-4 border-b border-slate-200">
        <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2 mb-1">
          <Sparkles className="h-6 w-6 text-blue-600" /> Action Catalog & Recommendations
        </h1>
        <p className="text-sm font-medium text-slate-500">Evidence-backed municipal directives ranked by projected AQI reduction</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {recs.map((rec) => (
          <div
            key={rec.id}
            className={`ui-card flex flex-col justify-between ${
              rec.applied ? 'border-emerald-500 bg-emerald-50/20' : ''
            }`}
          >
            <div>
              <div className="flex justify-between items-center mb-4">
                <span className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${
                  rec.priority === 'HIGH' ? 'bg-red-50 text-red-700 border-red-200' : 'bg-amber-50 text-amber-700 border-amber-200'
                }`}>
                  {rec.priority} PRIORITY
                </span>
                <span className="text-sm font-bold text-blue-600">{rec.expectedReduction}</span>
              </div>
              <h2 className="text-base font-semibold text-slate-900 mb-2">{rec.title}</h2>
              <p className="text-xs font-normal text-slate-700 leading-relaxed mb-6">{rec.description}</p>
            </div>

            <div className="space-y-4 pt-4 border-t border-slate-200">
              <div className="flex justify-between text-xs font-medium text-slate-700">
                <span>Target Department:</span>
                <span className="font-semibold text-slate-900">{rec.department}</span>
              </div>
              <button
                onClick={() => toggleApply(rec.id)}
                className={`w-full ${rec.applied ? 'bg-emerald-600 hover:bg-emerald-700 text-white font-medium text-sm rounded-xl px-4 py-2 transition-colors duration-150 shadow-sm flex items-center justify-center gap-2' : 'ui-button-primary'}`}
              >
                {rec.applied ? <><Check className="h-4 w-4" /> Directive Applied</> : 'Apply Directive'}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};