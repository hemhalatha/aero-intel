import React, { useState, useMemo } from 'react';
import { Search, Plus, Building2, MapPin, ChevronRight, X, ShieldAlert, Timer, CheckCircle2 } from 'lucide-react';
import { mockTasks, mockHotspots } from '../mock/data';
import { Task } from '../types';
import { generateEvidenceForHotspot } from '../utils/investigationEngine';

const columns: Task['status'][] = ['ASSIGNED', 'ACCEPTED', 'IN_PROGRESS', 'COMPLETED'];

const columnPercentages: Record<Task['status'], number> = {
  'ASSIGNED': 0,
  'ACCEPTED': 25,
  'IN_PROGRESS': 60,
  'COMPLETED': 100,
};

export const TaskManagement: React.FC = () => {
  const [tasks, setTasks] = useState<Task[]>(mockTasks);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterWard, setFilterWard] = useState('ALL');
  
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newDirective, setNewDirective] = useState({
    title: '',
    wardId: mockHotspots[0].id,
    department: 'Municipality',
    priority: 'HIGH',
    expectedReduction: '-20 AQI Points',
    estimatedTime: '24 Hours',
    evidence: ''
  });

  const selectedHotspotForModal = mockHotspots.find(h => h.id === newDirective.wardId) || mockHotspots[0];
  const dynamicModalEvidence = useMemo(() => {
    return generateEvidenceForHotspot(selectedHotspotForModal);
  }, [selectedHotspotForModal]);

  const moveTask = (id: string, nextStatus: Task['status']) => {
    setTasks((prev) => prev.map((t) => {
      if (t.id === id) {
        return { ...t, status: nextStatus, completionPercentage: columnPercentages[nextStatus] };
      }
      return t;
    }));
  };

  const handleCreateDirective = (e: React.FormEvent) => {
    e.preventDefault();
    const newTask: Task = {
      id: `TSK-${Math.floor(Math.random() * 9000) + 1000}`,
      title: newDirective.title,
      department: newDirective.department,
      priority: newDirective.priority,
      status: 'ASSIGNED',
      ward: selectedHotspotForModal.ward,
      assignedDate: new Date().toISOString().split('T')[0] + ' ' + new Date().toLocaleTimeString().slice(0,5),
      ageDays: 0,
      escalationStatus: 'NORMAL',
      expectedReduction: newDirective.expectedReduction,
      estimatedTime: newDirective.estimatedTime,
      evidence: newDirective.evidence,
      completionPercentage: 0
    };
    
    // Also push to mockTasks so it persists across local navigations in this session
    mockTasks.unshift(newTask);
    setTasks([newTask, ...tasks]);
    setIsModalOpen(false);
    setNewDirective({ ...newDirective, title: '', evidence: '' });
  };

  // Derive unique wards from all available tasks + mockHotspots for filtering
  const allWards = Array.from(new Set([...mockTasks.map(t => t.ward), ...mockHotspots.map(h => h.ward)])).sort();

  return (
    <div className="px-8 py-6 space-y-8 max-w-7xl mx-auto relative">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4 pb-4 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 mb-1">Inter-Agency Directive Tracker</h1>
          <p className="text-sm font-medium text-slate-500">Track real-time status and operational progress of active municipal enforcement orders</p>
        </div>

        <button 
          onClick={() => setIsModalOpen(true)}
          className="ui-button-primary"
        >
          <Plus className="h-4 w-4" />
          <span>New Action Directive</span>
        </button>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-wrap items-center gap-4">
        <div className="flex items-center gap-3 bg-white border border-slate-200 p-2.5 rounded-xl shadow-sm flex-1 max-w-md">
          <Search className="h-4 w-4 text-slate-400 pl-0.5" />
          <input
            type="text"
            placeholder="Filter by title or department..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="bg-transparent border-none text-sm font-semibold text-slate-700 placeholder-slate-400 focus:outline-none w-full"
          />
        </div>
        <div className="flex items-center gap-2 bg-white border border-slate-200 p-2.5 rounded-xl shadow-sm">
          <MapPin className="h-4 w-4 text-slate-500" />
          <select 
            value={filterWard}
            onChange={(e) => setFilterWard(e.target.value)}
            className="bg-transparent text-sm font-semibold text-slate-700 focus:outline-none cursor-pointer max-w-[200px]"
          >
            <option value="ALL">All Wards / Hubs</option>
            {allWards.map(w => (
              <option key={w} value={w}>{w}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Kanban Board Columns */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 overflow-x-auto min-h-[600px] items-start">
        {columns.map((col) => {
          const colTasks = tasks.filter(
            (t) => t.status === col && 
                   t.title.toLowerCase().includes(searchTerm.toLowerCase()) &&
                   (filterWard === 'ALL' || t.ward === filterWard)
          );

          return (
            <div key={col} className="bg-slate-50 border border-slate-200 rounded-2xl p-4 flex flex-col gap-4">
              <div className="flex justify-between items-center pb-2 border-b border-slate-200">
                <h2 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                  {col.replace('_', ' ')}
                </h2>
                <span className="text-xs font-bold px-2 py-0.5 bg-white border border-slate-200 text-slate-700 rounded-lg">
                  {colTasks.length}
                </span>
              </div>

              <div className="space-y-4">
                {colTasks.map((task) => {
                  const percent = task.completionPercentage ?? columnPercentages[task.status];
                  return (
                    <div
                      key={task.id}
                      className="bg-white border border-slate-200 p-4 rounded-2xl shadow-sm hover:shadow-md transition-all duration-200 space-y-3"
                    >
                      <div className="flex justify-between items-start mb-1">
                        <span className="font-mono text-[10px] font-bold text-blue-600 bg-blue-50 px-2 py-1 rounded-md border border-blue-200/60">
                          {task.id}
                        </span>
                        <span
                          className={`text-[10px] font-bold px-2 py-1 rounded-md border ${
                            task.priority === 'CRITICAL' || task.priority === 'HIGH'
                              ? 'bg-red-50 text-red-700 border-red-200'
                              : 'bg-amber-50 text-amber-700 border-amber-200'
                          }`}
                        >
                          {task.priority}
                        </span>
                      </div>

                      <h3 className="text-sm font-bold text-slate-900 leading-snug">
                        {task.title}
                      </h3>

                      {task.expectedReduction && (
                        <div className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-lg text-xs font-bold">
                          <ShieldAlert className="w-3.5 h-3.5" />
                          {task.expectedReduction}
                        </div>
                      )}

                      <div className="space-y-2 text-[11px] text-slate-600 font-semibold pt-1">
                        <div className="flex items-center gap-2">
                          <Building2 className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                          <span className="truncate">{task.department}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <MapPin className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                          <span className="truncate">{task.ward}</span>
                        </div>
                        {task.estimatedTime && (
                          <div className="flex items-center gap-2">
                            <Timer className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                            <span>{task.estimatedTime}</span>
                          </div>
                        )}
                        {task.evidence && (
                          <div className="flex items-start gap-2 pt-1">
                            <div className="w-1.5 h-1.5 rounded-full bg-purple-400 mt-1 shrink-0"></div>
                            <span className="text-slate-500 italic line-clamp-2">Linked: {task.evidence}</span>
                          </div>
                        )}
                      </div>

                      {/* Progress Bar */}
                      <div className="pt-2">
                        <div className="flex justify-between items-center text-[10px] font-bold text-slate-500 mb-1.5">
                          <span>Progress</span>
                          <span className={percent === 100 ? 'text-emerald-600' : ''}>{percent}%</span>
                        </div>
                        <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                          <div 
                            className={`h-full transition-all duration-500 ${percent === 100 ? 'bg-emerald-500' : 'bg-blue-500'}`}
                            style={{ width: `${percent}%` }}
                          />
                        </div>
                      </div>

                      {col !== 'COMPLETED' && (
                        <div className="pt-2 border-t border-slate-100 mt-2">
                          <button
                            onClick={() => moveTask(task.id, columns[columns.indexOf(col) + 1])}
                            className="w-full text-xs font-bold py-2 bg-slate-50 hover:bg-blue-50 text-slate-600 hover:text-blue-600 rounded-xl border border-slate-200 hover:border-blue-200 transition-colors flex items-center justify-center gap-1"
                          >
                            <span>Advance to {columns[columns.indexOf(col) + 1].replace('_', ' ')}</span>
                            <ChevronRight className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      )}
                      
                      {col === 'COMPLETED' && (
                        <div className="pt-2 border-t border-slate-100 mt-2 flex justify-center">
                          <span className="text-xs font-bold text-emerald-600 flex items-center gap-1">
                            <CheckCircle2 className="w-4 h-4" /> Task Verified
                          </span>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>

      {/* New Directive Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm">
          <div className="bg-white rounded-3xl shadow-xl w-full max-w-2xl overflow-hidden border border-slate-200">
            <div className="flex justify-between items-center p-6 border-b border-slate-100">
              <div>
                <h2 className="text-xl font-bold text-slate-900">Create Action Directive</h2>
                <p className="text-xs font-medium text-slate-500 mt-1">Manually issue a mitigation task to a municipal department</p>
              </div>
              <button onClick={() => setIsModalOpen(false)} className="p-2 hover:bg-slate-100 rounded-full text-slate-400 transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateDirective} className="p-6 space-y-6">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label className="text-xs font-bold text-slate-700">Target Ward / Hotspot</label>
                  <select
                    required
                    value={newDirective.wardId}
                    onChange={(e) => setNewDirective({ ...newDirective, wardId: e.target.value, evidence: '' })}
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-sm font-semibold text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {mockHotspots.map(h => (
                      <option key={h.id} value={h.id}>{h.ward}</option>
                    ))}
                  </select>
                </div>
                
                <div className="space-y-2">
                  <label className="text-xs font-bold text-slate-700">Directive Title</label>
                  <input
                    required
                    type="text"
                    placeholder="e.g., Deploy Water Sprinklers"
                    value={newDirective.title}
                    onChange={(e) => setNewDirective({ ...newDirective, title: e.target.value })}
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-sm font-semibold text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-xs font-bold text-slate-700">Target Department</label>
                  <select
                    value={newDirective.department}
                    onChange={(e) => setNewDirective({ ...newDirective, department: e.target.value })}
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-sm font-semibold text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option>Municipality</option>
                    <option>Traffic Police</option>
                    <option>Pollution Control Board</option>
                    <option>Public Works</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <label className="text-xs font-bold text-slate-700">Priority Level</label>
                  <select
                    value={newDirective.priority}
                    onChange={(e) => setNewDirective({ ...newDirective, priority: e.target.value })}
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-sm font-semibold text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option>LOW</option>
                    <option>MEDIUM</option>
                    <option>HIGH</option>
                    <option>CRITICAL</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <label className="text-xs font-bold text-slate-700">Expected AQI Reduction</label>
                  <input
                    type="text"
                    placeholder="e.g., -25 AQI Points"
                    value={newDirective.expectedReduction}
                    onChange={(e) => setNewDirective({ ...newDirective, expectedReduction: e.target.value })}
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-sm font-semibold text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-xs font-bold text-slate-700">Estimated Time</label>
                  <input
                    type="text"
                    placeholder="e.g., 24 Hours"
                    value={newDirective.estimatedTime}
                    onChange={(e) => setNewDirective({ ...newDirective, estimatedTime: e.target.value })}
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-sm font-semibold text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                <div className="space-y-2 sm:col-span-2">
                  <label className="text-xs font-bold text-slate-700">Link AI Hotspot Evidence (Optional)</label>
                  <select
                    value={newDirective.evidence}
                    onChange={(e) => setNewDirective({ ...newDirective, evidence: e.target.value })}
                    className="w-full bg-purple-50 border border-purple-200 rounded-xl px-3 py-2 text-sm font-semibold text-purple-900 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  >
                    <option value="">-- Select supporting evidence from AI investigation --</option>
                    {dynamicModalEvidence.map(ev => (
                      <option key={ev.id} value={ev.title}>{ev.title} ({ev.type})</option>
                    ))}
                  </select>
                  <p className="text-[11px] font-medium text-slate-500 ml-1">Auto-generated based on selected Ward's active investigation profile.</p>
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-6 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-5 py-2.5 text-sm font-bold text-slate-600 bg-white border border-slate-200 rounded-xl hover:bg-slate-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="ui-button-primary"
                >
                  Create & Assign Task
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};