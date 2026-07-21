import React, { useState } from 'react';
import { Search, Plus, CheckSquare } from 'lucide-react';
import { motion } from 'framer-motion';
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
    <div className="space-y-6">
      <div className="flex justify-between items-center gap-4">
        <div className="flex items-center gap-3 glass-panel px-3 py-2 rounded-lg flex-1 max-w-md">
          <Search className="h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search tasks or departments..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="bg-transparent border-none text-xs text-white focus:outline-none w-full font-mono"
          />
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-brand-cyan text-dark-950 font-mono text-xs font-bold rounded-lg shadow-neon-cyan">
          <Plus className="h-4 w-4" /> CREATE DIRECTIVE
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 overflow-x-auto">
        {columns.map((col) => (
          <div key={col} className="glass-panel rounded-xl p-3 min-w-[250px]">
            <div className="flex justify-between items-center mb-3 pb-2 border-b border-dark-700/80">
              <h3 className="text-xs font-mono font-bold text-gray-300 uppercase">{col.replace('_', ' ')}</h3>
              <span className="text-[10px] font-mono px-2 py-0.5 bg-dark-900 text-brand-cyan rounded">
                {tasks.filter((t) => t.status === col).length}
              </span>
            </div>

            <div className="space-y-3">
              {tasks
                .filter((t) => t.status === col && t.title.toLowerCase().includes(searchTerm.toLowerCase()))
                .map((task) => (
                  <motion.div
                    key={task.id}
                    layout
                    className="bg-dark-900/90 border border-dark-700 p-3 rounded-lg space-y-2 hover:border-brand-cyan/40 transition"
                  >
                    <div className="flex justify-between items-center">
                      <span className="text-[10px] font-mono text-gray-500">{task.id}</span>
                      <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded ${task.priority === 'CRITICAL' ? 'bg-brand-red/20 text-brand-red' : 'bg-brand-amber/20 text-brand-amber'}`}>
                        {task.priority}
                      </span>
                    </div>
                    <div className="text-xs font-semibold text-gray-200">{task.title}</div>
                    <div className="text-[10px] font-mono text-gray-400">{task.department} • {task.ward}</div>
                    <div className="pt-2 flex justify-between gap-1 border-t border-dark-800">
                      {col !== 'COMPLETED' && (
                        <button
                          onClick={() => moveTask(task.id, columns[columns.indexOf(col) + 1])}
                          className="w-full text-[10px] font-mono py-1 bg-dark-800 hover:bg-dark-700 text-brand-cyan rounded border border-dark-700 transition"
                        >
                          ADVANCE STATUS →
                        </button>
                      )}
                    </div>
                  </motion.div>
                ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};