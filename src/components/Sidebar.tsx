import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard, Search, PieChart, LineChart, Lightbulb,
  CheckSquare, ShieldAlert, Users, PanelLeftClose, PanelLeftOpen
} from 'lucide-react';

const navigation = [
  { name: 'Overview', href: '/', icon: LayoutDashboard },
  { name: 'Source Attribution', href: '/attribution', icon: PieChart },
  { name: 'Hotspot Investigation', href: '/investigation', icon: Search },
  { name: 'Predictive Scenarios', href: '/simulation', icon: LineChart },
  { name: 'Action Catalog', href: '/recommendations', icon: Lightbulb },
  { name: 'Task Tracker', href: '/tasks', icon: CheckSquare },
  { name: 'Accountability & Audit', href: '/accountability', icon: ShieldAlert },
  { name: 'Citizen Advisories', href: '/advisory', icon: Users },
];

export const Sidebar: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={`border-r border-slate-200 bg-white flex flex-col shrink-0 h-[calc(100vh-4rem)] transition-all duration-200 ${
        collapsed ? 'w-16' : 'w-60'
      }`}
    >
      {/* Navigation Options */}
      <div className="p-3">
        <div className="flex items-center justify-between px-2 mb-4">
          {!collapsed && (
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              Navigation
            </span>
          )}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="p-1 hover:bg-slate-100 rounded text-slate-400 hover:text-slate-600 transition-colors ml-auto"
            title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {collapsed ? <PanelLeftOpen className="h-4 w-4" /> : <PanelLeftClose className="h-4 w-4" />}
          </button>
        </div>

        <nav className="space-y-1">
          {navigation.map((item) => (
            <NavLink
              key={item.name}
              to={item.href}
              className={({ isActive }) =>
                `flex items-center space-x-3 px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
                  isActive
                    ? 'bg-blue-50 text-blue-700 font-semibold'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/80'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <item.icon className={`h-4 w-4 shrink-0 ${isActive ? 'text-blue-600' : 'text-slate-400'}`} />
                  {!collapsed && <span className="truncate">{item.name}</span>}
                </>
              )}
            </NavLink>
          ))}
        </nav>
      </div>


    </aside>
  );
};