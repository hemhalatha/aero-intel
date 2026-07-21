import React from 'react';
import { ShieldAlert, Clock, Building2, AlertCircle, Send, FileText, ArrowUpRight, ChevronRight, TrendingUp } from 'lucide-react';
import { mockTasks } from '../mock/data';

export const Accountability: React.FC = () => {
  return (
    <div className="px-8 py-6 space-y-8 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4 pb-4 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 mb-1">Inter-Departmental Accountability & Audit Matrix</h1>
          <p className="text-sm font-medium text-slate-500">Automated non-compliance tracking, SLA escalation timelines, and legal notice dispatch log</p>
        </div>
        <div className="flex items-center gap-3">
          <button className="ui-button-secondary">
            <FileText className="h-4 w-4 text-slate-500" />
            <span>Export Audit Log</span>
          </button>
          <button className="ui-button-primary">
            <Send className="h-4 w-4" />
            <span>Issue Directives</span>
          </button>
        </div>
      </div>

      {/* KPI Overview Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="ui-card flex flex-col justify-between h-40">
          <div className="flex justify-between items-start">
            <span className="text-sm font-medium text-slate-500">Total Directives</span>
            <Building2 className="h-4 w-4 text-slate-400" />
          </div>
          <div>
            <div className="text-3xl font-bold text-slate-900 tracking-tight">24</div>
            <p className="text-xs font-medium text-slate-500 mt-0.5">Active Agency Orders</p>
          </div>
          <div className="flex items-center gap-1 text-xs font-medium text-emerald-600">
            <TrendingUp className="h-4 w-4" />
            <span>88% On-Time Execution</span>
          </div>
        </div>

        <div className="ui-card flex flex-col justify-between h-40">
          <div className="flex justify-between items-start">
            <span className="text-sm font-medium text-slate-500">Standard Warnings</span>
            <Clock className="h-4 w-4 text-amber-500" />
          </div>
          <div>
            <div className="text-3xl font-bold text-slate-900 tracking-tight">5</div>
            <p className="text-xs font-medium text-slate-500 mt-0.5">Pending SLA Flags</p>
          </div>
          <div className="flex items-center gap-1 text-xs font-medium text-amber-600">
            <AlertCircle className="h-4 w-4" />
            <span>Reminders Sent (&gt;24h)</span>
          </div>
        </div>

        <div className="ui-card flex flex-col justify-between h-40">
          <div className="flex justify-between items-start">
            <span className="text-sm font-medium text-slate-500">Escalated Directives</span>
            <ShieldAlert className="h-4 w-4 text-amber-600" />
          </div>
          <div>
            <div className="text-3xl font-bold text-slate-900 tracking-tight">2</div>
            <p className="text-xs font-medium text-slate-500 mt-0.5">Escalated to Nodal Officer</p>
          </div>
          <div className="flex items-center gap-1 text-xs font-medium text-amber-700">
            <ArrowUpRight className="h-4 w-4" />
            <span>Overdue (&gt;72h)</span>
          </div>
        </div>

        <div className="ui-card flex flex-col justify-between h-40">
          <div className="flex justify-between items-start">
            <span className="text-sm font-medium text-slate-500">Critical Violations</span>
            <ShieldAlert className="h-4 w-4 text-red-600" />
          </div>
          <div>
            <div className="text-3xl font-bold text-slate-900 tracking-tight">1</div>
            <p className="text-xs font-medium text-slate-500 mt-0.5">Section 31A Active Notice</p>
          </div>
          <div className="text-xs font-medium text-red-600">
            <span>Statutory Notice Active</span>
          </div>
        </div>
      </div>

      {/* Task Audit Table */}
      <div className="ui-card space-y-4">
        <div className="flex justify-between items-center pb-3 border-b border-slate-200">
          <div>
            <h2 className="text-base font-semibold text-slate-900 mb-1">Active Directives & Legal Compliance State</h2>
            <p className="text-xs font-medium text-slate-500">Real-time status of multi-agency municipal enforcement orders</p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-slate-500">Sort by:</span>
            <select className="text-xs bg-white border border-slate-200 text-slate-700 font-medium rounded-xl px-3 py-1.5 focus:outline-none">
              <option>Escalation Severity</option>
              <option>Age (Oldest First)</option>
              <option>Department</option>
            </select>
          </div>
        </div>

        <div className="divide-y divide-slate-200">
          {mockTasks.map((task) => (
            <div key={task.id} className="py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-semibold text-blue-600 bg-blue-50 px-2 py-0.5 rounded-md border border-blue-200/60">
                    {task.id}
                  </span>
                  <h3 className="text-sm font-semibold text-slate-900">{task.title}</h3>
                </div>
                <p className="text-xs font-normal text-slate-700">
                  Assigned to <span className="font-semibold text-slate-900">{task.department}</span> ({task.ward}) • Age: <span className="font-semibold text-slate-900">{task.ageDays} Days</span>
                </p>
              </div>

              <div className="flex items-center gap-4 shrink-0">
                {task.escalationStatus === 'NORMAL' && (
                  <span className="text-xs font-medium px-3 py-1 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
                    Standard Protocol
                  </span>
                )}
                {task.escalationStatus === 'REMINDER_SENT' && (
                  <span className="text-xs font-medium px-3 py-1 rounded-full bg-amber-50 text-amber-700 border border-amber-200">
                    Reminder Issued
                  </span>
                )}
                {task.escalationStatus === 'ESCALATED' && (
                  <span className="text-xs font-medium px-3 py-1 rounded-full bg-amber-50 text-amber-800 border border-amber-300 font-semibold">
                    Escalated to Nodal
                  </span>
                )}
                {task.escalationStatus === 'CRITICAL_ALERT' && (
                  <span className="text-xs font-medium px-3 py-1 rounded-full bg-red-50 text-red-700 border border-red-200 font-semibold">
                    Statutory Notice Active
                  </span>
                )}

                <button className="ui-button-secondary text-xs py-1.5">
                  <span>Issue Official Notice</span>
                  <ChevronRight className="h-3.5 w-3.5 text-slate-400" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};