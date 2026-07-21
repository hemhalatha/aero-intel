import React, { useState } from 'react';
import { Search, Plus, Building2, MapPin, ChevronRight } from 'lucide-react';
import { mockTasks } from '../mock/data';
import { Task } from '../types';

const columns: Task['status'][] = ['ASSIGNED', 'ACCEPTED', 'IN_PROGRESS', 'COMPLETED'];

export const TaskManagement: React.FC = () => {
  const [tasks, setTasks] = useState<Task[]>(mockTasks);
  const [searchTerm, setSearchTerm] = useState('');

  const moveTask = (id: string, nextStatus: Task['status']) => {
    setTasks((prev) => prev.map((t) => (t.id === id ? { ...t, status: nextStatus } : t)));
  };

  return (
    <div className="px-8 py-6 space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4 pb-4 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 mb-1">Inter-Agency Directive Tracker</h1>
          <p className="text-sm font-medium text-slate-500">Track real-time status and operational progress of active municipal enforcement orders</p>
        </div>

        <button className="ui-button-primary">
          <Plus className="h-4 w-4" />
          <span>New Action Directive</span>
        </button>
      </div>

      {/* Filter Bar */}
      <div className="flex items-center gap-3 bg-white border border-slate-200 p-2.5 rounded-2xl shadow-sm max-w-md">
        <Search className="h-4 w-4 text-slate-400 pl-0.5" />
        <input
          type="text"
          placeholder="Filter by title, ward, or department..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="bg-transparent border-none text-sm font-normal text-slate-700 placeholder-slate-400 focus:outline-none w-full"
        />
      </div>

      {/* Kanban Board Columns */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 overflow-x-auto">
        {columns.map((col) => {
          const colTasks = tasks.filter(
            (t) => t.status === col && t.title.toLowerCase().includes(searchTerm.toLowerCase())
          );

          return (
            <div key={col} className="bg-slate-100/80 border border-slate-200 rounded-2xl p-4 min-w-[260px] flex flex-col justify-between">
              <div>
                <div className="flex justify-between items-center mb-4 pb-2 border-b border-slate-200">
                  <h2 className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
                    {col.replace('_', ' ')}
                  </h2>
                  <span className="text-xs font-semibold px-2.5 py-0.5 bg-white border border-slate-200 text-slate-700 rounded-md">
                    {colTasks.length}
                  </span>
                </div>

                <div className="space-y-4">
                  {colTasks.map((task) => (
                    <div
                      key={task.id}
                      className="bg-white border border-slate-200 p-5 rounded-2xl shadow-sm hover:shadow-md transition-all duration-200 space-y-3"
                    >
                      <div className="flex justify-between items-center">
                        <span className="font-mono text-xs font-semibold text-blue-600 bg-blue-50 px-2 py-0.5 rounded-md border border-blue-200/60">
                          {task.id}
                        </span>
                        <span
                          className={`text-xs font-medium px-2 py-0.5 rounded-md border ${
                            task.priority === 'CRITICAL'
                              ? 'bg-red-50 text-red-700 border-red-200'
                              : 'bg-amber-50 text-amber-700 border-amber-200'
                          }`}
                        >
                          {task.priority}
                        </span>
                      </div>

                      <h3 className="text-sm font-semibold text-slate-900 leading-snug">
                        {task.title}
                      </h3>

                      <div className="space-y-1.5 text-xs text-slate-600 font-medium pt-1">
                        <div className="flex items-center gap-1.5 text-slate-700">
                          <Building2 className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                          <span className="truncate">{task.department}</span>
                        </div>
                        <div className="flex items-center gap-1.5 text-slate-500">
                          <MapPin className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                          <span>{task.ward}</span>
                        </div>
                      </div>

                      {col !== 'COMPLETED' && (
                        <div className="pt-2 border-t border-slate-100">
                          <button
                            onClick={() => moveTask(task.id, columns[columns.indexOf(col) + 1])}
                            className="w-full text-xs font-medium py-2 bg-slate-50 hover:bg-slate-100 text-slate-700 rounded-xl border border-slate-200 transition-colors flex items-center justify-center gap-1"
                          >
                            <span>Advance Status</span>
                            <ChevronRight className="h-3.5 w-3.5 text-slate-400" />
                          </button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};