import React from 'react';
import { ShieldAlert } from 'lucide-react';
import { mockTasks } from '../mock/data';

export const Accountability: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="glass-panel p-5 rounded-xl">
        <h2 className="text-lg font-mono font-bold text-white mb-1">INTER-DEPARTMENTAL COMPLIANCE & ESCALATION MATRIX</h2>
        <p className="text-xs text-gray-400 font-mono">Automated Non-Compliance Escalation Logs</p>
      </div>

      <div className="glass-panel p-5 rounded-xl space-y-4">
        {mockTasks.map((task) => (
          <div key={task.id} className="p-4 bg-dark-900/90 border border-dark-700 rounded-xl flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono text-brand-cyan font-bold">{task.id}</span>
                <span className="text-xs font-semibold text-white">{task.title}</span>
              </div>
              <div className="text-xs text-gray-400 mt-1 font-mono">
                Assigned to: <strong className="text-gray-200">{task.department}</strong> ({task.ward}) | Age: {task.ageDays} Days
              </div>
            </div>

            <div className="flex items-center gap-3">
              <span className={`text-xs font-mono px-3 py-1 rounded-full font-bold border ${
                task.escalationStatus === 'CRITICAL_ALERT' ? 'bg-brand-red/20 text-brand-red border-brand-red/40 animate-pulse' :
                task.escalationStatus === 'ESCALATED' ? 'bg-brand-amber/20 text-brand-amber border-brand-amber/40' :
                'bg-dark-800 text-gray-400 border-dark-700'
              }`}>
                {task.escalationStatus.replace('_', ' ')}
              </span>
              <button className="px-3 py-1 bg-brand-red/20 hover:bg-brand-red/30 text-brand-red font-mono text-xs rounded border border-brand-red/40 transition">
                ISSUE NOTICE
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};