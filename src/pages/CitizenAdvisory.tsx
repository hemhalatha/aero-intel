import React, { useState } from 'react';
import { ShieldAlert, Heart, School, Building2 } from 'lucide-react';
import { mockAdvisories } from '../mock/data';

export const CitizenAdvisory: React.FC = () => {
  const [selectedLang, setSelectedLang] = useState('en');
  const activeAdvisory = mockAdvisories.find((a) => a.code === selectedLang) || mockAdvisories[0];

  return (
    <div className="px-8 py-6 space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4 pb-4 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 mb-1">Public Health & Citizen Broadcast Directives</h1>
          <p className="text-sm font-medium text-slate-500">Automated ward-level multilingual advisories pushed to mobile & IVR systems</p>
        </div>
        <div className="flex items-center gap-2">
          {mockAdvisories.map((a) => (
            <button
              key={a.code}
              onClick={() => setSelectedLang(a.code)}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-colors border ${
                selectedLang === a.code 
                  ? 'bg-blue-600 text-white border-blue-600 shadow-sm font-semibold' 
                  : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
              }`}
            >
              {a.language}
            </button>
          ))}
        </div>
      </div>

      {/* Main Advisory Alert Banner */}
      <div className="ui-card border-l-4 border-l-red-600 space-y-3">
        <div className="flex items-center gap-2 text-red-700 text-xs font-semibold uppercase tracking-wider">
          <ShieldAlert className="h-4 w-4" />
          <span>Severe Air Pollution Emergency Public Broadcast</span>
        </div>
        <p className="text-base font-normal text-slate-900 leading-relaxed bg-slate-50 p-5 rounded-xl border border-slate-200">
          "{activeAdvisory.text}"
        </p>
      </div>

      {/* Target Demographic Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="ui-card space-y-3">
          <div className="w-10 h-10 rounded-xl bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-700">
            <School className="h-5 w-5" />
          </div>
          <h2 className="text-base font-semibold text-slate-900">Schools & Institutions</h2>
          <p className="text-xs font-normal text-slate-700 leading-relaxed">
            Suspend all outdoor physical sports, morning assemblies, and continuous outdoor activities until AQI drops below the 200 threshold.
          </p>
        </div>

        <div className="ui-card space-y-3">
          <div className="w-10 h-10 rounded-xl bg-red-50 border border-red-200 flex items-center justify-center text-red-700">
            <Heart className="h-5 w-5" />
          </div>
          <h2 className="text-base font-semibold text-slate-900">Vulnerable Population Groups</h2>
          <p className="text-xs font-normal text-slate-700 leading-relaxed">
            Elderly citizens, pregnant women, and asthma/respiratory patients must remain indoors with HEPA air purifiers active.
          </p>
        </div>

        <div className="ui-card space-y-3">
          <div className="w-10 h-10 rounded-xl bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-700">
            <Building2 className="h-5 w-5" />
          </div>
          <h2 className="text-base font-semibold text-slate-900">Outdoor & Sanitation Workers</h2>
          <p className="text-xs font-normal text-slate-700 leading-relaxed">
            Mandatory N95 respirator mask distribution enforced for all municipal sweepers, traffic officers, and site laborers.
          </p>
        </div>
      </div>
    </div>
  );
};