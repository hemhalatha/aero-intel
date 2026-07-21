import React from 'react';
import { PieChart as RePieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { Bot } from 'lucide-react';
import { mockAttributionData } from '../mock/data';

export const Attribution: React.FC = () => {
  return (
    <div className="px-8 py-6 space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="pb-4 border-b border-slate-200">
        <h1 className="text-2xl font-bold text-slate-900 mb-1">Source Attribution Engine</h1>
        <p className="text-sm font-medium text-slate-500">
          Statistical apportionment of fugitive emissions by source category using wind dispersion vectors
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pie Chart Card */}
        <div className="ui-card space-y-4">
          <h2 className="text-base font-semibold text-slate-900">Pollution Source Share</h2>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <RePieChart>
                <Pie
                  data={mockAttributionData}
                  dataKey="percentage"
                  nameKey="source"
                  cx="50%"
                  cy="50%"
                  innerRadius={65}
                  outerRadius={95}
                  paddingAngle={4}
                >
                  {mockAttributionData.map((entry) => (
                    <Cell key={entry.source} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#FFFFFF',
                    borderColor: '#E2E8F0',
                    borderRadius: '12px',
                    color: '#0F172A',
                    fontWeight: 600,
                  }}
                />
              </RePieChart>
            </ResponsiveContainer>
          </div>

          <div className="grid grid-cols-3 gap-3 pt-2">
            {mockAttributionData.map((item) => (
              <div key={item.source} className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-center">
                <div className="text-xs font-medium text-slate-500 truncate">{item.source}</div>
                <div className="text-2xl font-bold mt-1" style={{ color: item.color }}>
                  {item.percentage}%
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* AI Explanation & Confidence */}
        <div className="space-y-6">
          <div className="ui-card space-y-3">
            <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Confidence Metric</h2>
            <div className="w-full bg-slate-100 h-3.5 rounded-full overflow-hidden border border-slate-200">
              <div className="bg-blue-600 h-full rounded-full" style={{ width: '85%' }}></div>
            </div>
            <div className="flex justify-between text-xs font-semibold text-slate-700">
              <span>Statistical Variance: ±3.2%</span>
              <span className="text-blue-600 font-bold">85% High Confidence</span>
            </div>
          </div>

          <div className="ui-card space-y-3">
            <div className="flex items-center gap-2">
              <Bot className="h-5 w-5 text-blue-600" />
              <h2 className="text-base font-semibold text-slate-900">AI Diagnostic Summary</h2>
            </div>
            <p className="text-sm font-normal text-slate-700 leading-relaxed bg-slate-50 p-4 border border-slate-200 rounded-xl">
              Unmitigated dust from 12,000 sq.m construction site at Permit #CNST-2026-8891 combined with 14 km/h SSW wind vector accounts for 85% of PM10 spike at Ward 17 sensor station. Vehicular freight idling contributes 10% secondary aerosol volume.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
