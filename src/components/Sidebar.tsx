import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, Search, PieChart, LineChart, Lightbulb, 
  CheckSquare, ShieldAlert, Users, ChevronLeft, ChevronRight 
} from 'lucide-react';
import { motion } from 'framer-motion';

const navigation = [
  { name: 'Command Center', href: '/', icon: LayoutDashboard },
  { name: 'Investigation', href: '/investigation', icon: Search },
  { name: 'Attribution', href: '/attribution', icon: PieChart },
  { name: 'Scenario Simulation', href: '/simulation', icon: LineChart },
  { name: 'Recommendations', href: '/recommendations', icon: Lightbulb },
  { name: 'Task Management', href: '/tasks', icon: CheckSquare },
  { name: 'Accountability', href: '/accountability', icon: ShieldAlert },
  { name: 'Citizen Advisory', href: '/advisory', icon: Users },
];

export const Sidebar: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <motion.aside
      animate={{ width: collapsed ? 72 : 256 }}
      transition={{ duration: 0.25, ease: 'easeInOut' }}
      className="border-r border-dark-700/80 bg-dark-900/95 flex flex-col justify-between shrink-0 h-[calc(100vh-4rem)] relative z-40 backdrop-blur-md"
    >
      {/* Navigation Items */}
      <nav className="p-3 space-y-1.5 overflow-y-auto overflow-x-hidden">
        <div className="flex justify-between items-center px-2 mb-3">
          {!collapsed && (
            <span className="text-[10px] font-mono text-gray-500 uppercase tracking-widest">
              OPERATIONAL MATRIX
            </span>
          )}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="p-1 hover:bg-dark-800 rounded text-gray-400 hover:text-white transition"
          >
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </button>
        </div>

        {navigation.map((item) => (
          <NavLink
            key={item.name}
            to={item.href}
            className={({ isActive }) =>
              `flex items-center space-x-3 px-3 py-2.5 rounded-lg text-xs font-mono font-medium transition-all group relative ${
                isActive
                  ? 'bg-brand-cyan/15 text-brand-cyan border border-brand-cyan/30 shadow-neon-cyan'
                  : 'text-gray-400 hover:text-gray-100 hover:bg-dark-800/60'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <item.icon className={`h-4 w-4 shrink-0 ${isActive ? 'text-brand-cyan' : 'group-hover:text-brand-cyan'}`} />
                {!collapsed && <span className="truncate">{item.name}</span>}
                {isActive && (
                  <motion.div
                    layoutId="activeGlow"
                    className="absolute left-0 top-0 bottom-0 w-1 bg-brand-cyan rounded-r"
                  />
                )}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Footer System Spec */}
      {!collapsed && (
        <div className="p-4 border-t border-dark-700/80 text-[10px] text-gray-500 font-mono space-y-1 bg-dark-950/40">
          <div className="flex justify-between">
            <span>GRID: 100M MESH</span>
            <span className="text-brand-cyan font-bold">READY</span>
          </div>
          <div className="flex justify-between">
            <span>LATENCY: 14MS</span>
            <span className="text-brand-green">OPTIMAL</span>
          </div>
        </div>
      )}
    </motion.aside>
  );
};