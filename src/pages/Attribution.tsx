import React from 'react';
import { PieChart as RePieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { Bot, FileText, CheckCircle } from 'lucide-react';
import { mockAttributionData } from '../mock/data';

export const Attribution: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pie Chart & Breakdown */}
        <div className="bg-dark-800 border border-dark-700 rounded-xl p-5">
          <h3 className="text-xs font-mono text-gray-400 uppercase tracking-wider mb-4">Fugitive Emission Attribution Breakdown</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <RePieChart>
                <Pie data={mockAttributionData} dataKey="percentage" nameKey="source" cx="50%" cy="50%" innerRadius={60} outerRadius={90} paddingAngle={5}>
                  {mockAttributionData.map((entry) => (
                    <Cell key={entry.source} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#111827', borderColor: '#374151' }} />
              </RePieChart>
            </ResponsiveContainer>
          </div>
          <div className="grid grid-cols-3 gap-2 mt-4 text-center">
            {mockAttributionData.map((item) => (
              <div key={item.source} className="p-2 bg-dark-900 border border-dark-700 rounded">
                <div className="text-[10px] text-gray-400 truncate">{item.source}</div>
                <div className="text-lg font-bold font-mono" style={{ color: item.color }}>{item.percentage}%</div>
              </div>
            ))}
          </div>
        </div>

        {/* AI Confidence & Explanation */}
        <div className="space-y-6">
          <div className="bg-dark-800 border border-dark-700 rounded-xl p-5">
            <h3 className="text-xs font-mono text-gray-400 uppercase tracking-wider mb-2">Attribution Confidence Index</h3>
            <div className="w-full bg-dark-900 h-4 rounded-full overflow-hidden border border-dark-700 relative">
              <div className="bg-brand-cyan h-full rounded-full transition-all duration-1000" style={{ width: '85%' }}></div>
            </div>
            <div className="flex justify-between text-xs font-mono mt-2">
              <span className="text-gray-400">Statistical Variance: ±3.2%</span>
              <span className="text-brand-cyan font-bold">85% HIGH CONFIDENCE</span>
            </div>
          </div>

          <div className="bg-dark-800 border border-dark-700 rounded-xl p-5 relative overflow-hidden">
            <div className="flex items-center gap-3 mb-3">
              <Bot className="h-6 w-6 text-brand-cyan" />
              <h3 className="text-sm font-bold font-mono text-white">AI DIAGNOSTIC EXPLANATION</h3>
            </div>
            <blockquote className="text-xs text-gray-300 leading-relaxed bg-dark-900 p-4 border-l-2 border-brand-cyan rounded-r-lg font-mono">
              "Unmitigated dust from 12,000 sq.m construction site at Permit #CNST-2026-8891 combined with 14 km/h SSW wind vector accounts for 85% of PM10 spike at Ward 17 sensor station. Vehicular freight idling contributes 10% secondary aerosol volume."
            </blockquote>
          </div>
        </div>
      </div>
    </div>
  );
};