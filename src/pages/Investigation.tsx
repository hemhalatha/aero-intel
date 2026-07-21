import React from 'react';
import { Truck, HardHat, Factory } from 'lucide-react';
import { mockEvidenceItems } from '../mock/data';

export const Investigation: React.FC = () => {
  return (
    <div className="px-8 py-6 space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 bg-red-50 text-red-700 border border-red-200 text-xs font-semibold rounded-full">
              Active Case File
            </span>
            <span className="text-xs font-medium text-slate-500">Incident #HS-801</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900">Hotspot Investigation: Ward 17</h1>
          <p className="text-sm font-medium text-slate-500 mt-0.5">
            Cross-referencing satellite aerosol feeds, traffic density indices, and municipal registries
          </p>
        </div>
        <div className="text-right">
          <span className="text-xs font-medium text-slate-500">Confidence Score</span>
          <div className="text-3xl font-bold text-slate-900">92.4%</div>
        </div>
      </div>

      {/* Evidence Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {mockEvidenceItems.map((item) => (
          <div key={item.id} className="ui-card flex flex-col justify-between">
            <div>
              <div className="flex justify-between items-start mb-4">
                <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-slate-700">
                  {item.type === 'CONSTRUCTION' && <HardHat className="h-6 w-6 text-amber-600" />}
                  {item.type === 'TRAFFIC' && <Truck className="h-6 w-6 text-blue-600" />}
                  {item.type === 'INDUSTRIAL' && <Factory className="h-6 w-6 text-red-600" />}
                </div>
                <span className="text-xs font-semibold px-2.5 py-1 bg-slate-100 text-slate-700 rounded-lg border border-slate-200">
                  {(item.confidence * 100).toFixed(0)}% Confidence
                </span>
              </div>
              <h2 className="text-base font-semibold text-slate-900 mb-2">{item.title}</h2>
              <p className="text-xs font-normal text-slate-700 leading-relaxed mb-6">{item.description}</p>
            </div>

            <div className="border-t border-slate-200 pt-4 space-y-2 text-xs">
              {Object.entries(item.metadata).map(([key, value]) => (
                <div key={key} className="flex justify-between items-center">
                  <span className="font-medium text-slate-500">{key}:</span>
                  <span className="font-semibold text-slate-900">{value}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Investigation Activity Log */}
      <div className="ui-card space-y-4">
        <div className="flex justify-between items-center pb-3 border-b border-slate-200">
          <div>
            <h2 className="text-base font-semibold text-slate-900 mb-1">Evidence Gathering Audit Trail</h2>
            <p className="text-xs font-medium text-slate-500">Sequential sensor triggers and satellite sweep logs</p>
          </div>
          <span className="text-xs font-medium text-slate-500">3 Logs Recorded</span>
        </div>

        <div className="space-y-3">
          {mockEvidenceItems.map((item, idx) => (
            <div key={item.id} className="p-4 bg-slate-50/80 border border-slate-200 rounded-xl flex items-start gap-4">
              <div className="w-8 h-8 rounded-xl bg-white border border-slate-200 flex items-center justify-center text-xs font-bold text-slate-700 shrink-0">
                {idx + 1}
              </div>
              <div className="flex-1 text-xs space-y-1">
                <div className="flex justify-between font-medium">
                  <span className="text-slate-500">{item.timestamp}</span>
                  <span className="text-blue-600 font-semibold">{item.type} DETECTED</span>
                </div>
                <div className="text-sm font-semibold text-slate-900">{item.title}</div>
                <p className="text-slate-700 font-normal">{item.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
