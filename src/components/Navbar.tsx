import React, { useState, useEffect } from 'react';
import { Bell, MapPin, Clock, Search, User, AlertTriangle, ShieldAlert, Info, X } from 'lucide-react';

export const Navbar: React.FC = () => {
  const [time, setTime] = useState<string>('');
  const [notificationsOpen, setNotificationsOpen] = useState<boolean>(false);

  useEffect(() => {
    const updateClock = () => {
      const now = new Date();
      setTime(now.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }) + ' IST');
    };
    updateClock();
    const interval = setInterval(updateClock, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="h-16 border-b border-slate-200 bg-white sticky top-0 z-50 flex items-center justify-between px-8 shadow-sm">
      {/* Brand */}
      <div className="flex items-center space-x-3">
        <div className="w-9 h-9 rounded-xl bg-blue-600 flex items-center justify-center text-white font-bold text-sm shadow-sm">
          AI
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-bold text-slate-900 text-base tracking-tight">AeroIntel</span>
            <span className="text-xs px-2 py-0.5 bg-slate-100 text-slate-600 rounded-md font-semibold border border-slate-200">
              Enterprise
            </span>
          </div>
          <p className="text-xs font-medium text-slate-500">National Air Quality Intelligence Platform</p>
        </div>
      </div>

      {/* Global Search */}
      <div className="hidden md:flex items-center space-x-2 bg-slate-100/80 border border-slate-200 px-3.5 py-2 rounded-xl w-80 text-xs">
        <Search className="h-4 w-4 text-slate-400 shrink-0" />
        <input
          type="text"
          placeholder="Search wards, sensors, or station IDs..."
          className="bg-transparent border-none text-slate-800 font-normal placeholder-slate-400 focus:outline-none w-full text-xs"
        />
        <kbd className="hidden sm:inline-block px-2 py-0.5 text-[10px] font-mono text-slate-400 bg-white border border-slate-200 rounded-md">
          ⌘K
        </kbd>
      </div>

      {/* Right Tools & User Info */}
      <div className="flex items-center space-x-4">
        <div className="hidden lg:flex items-center space-x-3 text-xs text-slate-600 border-r border-slate-200 pr-4 font-medium">
          <div className="flex items-center gap-1.5 bg-slate-100 px-3 py-1.5 rounded-lg border border-slate-200">
            <MapPin className="h-3.5 w-3.5 text-slate-500" />
            <span>NCR Region</span>
          </div>
          <div className="flex items-center gap-1.5 font-mono text-slate-500">
            <Clock className="h-3.5 w-3.5" />
            <span>{time || '19:30:00 IST'}</span>
          </div>
        </div>

        {/* System Status */}
        <div className="flex items-center gap-2 text-xs font-semibold text-emerald-700 bg-emerald-50 px-3 py-1.5 rounded-lg border border-emerald-200">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span className="hidden sm:inline">CPCB Feed Active</span>
        </div>

        {/* Interactive Notifications Bell */}
        <div className="relative">
          <button
            onClick={() => setNotificationsOpen(!notificationsOpen)}
            className="p-2 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-xl border border-slate-200 relative transition-colors focus:outline-none"
            title="System Notifications"
          >
            <Bell className="h-4 w-4" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-blue-600 rounded-full"></span>
          </button>

          {/* Notifications Dropdown Panel */}
          {notificationsOpen && (
            <div className="absolute right-0 mt-2 w-80 bg-white border border-slate-200 rounded-2xl shadow-lg p-4 z-50 text-xs">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-slate-900">System Alerts</span>
                  <span className="px-2 py-0.5 bg-blue-50 text-blue-700 text-[10px] font-semibold rounded-full border border-blue-200">
                    3 New
                  </span>
                </div>
                <button
                  onClick={() => setNotificationsOpen(false)}
                  className="p-1 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition-colors"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              </div>

              <div className="mt-3 space-y-2.5">
                <div className="p-3 bg-red-50/60 border border-red-200/80 rounded-xl space-y-1">
                  <div className="flex items-center gap-1.5 font-semibold text-red-700">
                    <ShieldAlert className="h-3.5 w-3.5 text-red-600" />
                    <span>Severe AQI Spike Flagged</span>
                  </div>
                  <p className="text-slate-600 text-[11px] font-normal leading-relaxed">
                    Ward 17 (Okhla Phase II) crossed the 390 AQI threshold. Immediate intervention required.
                  </p>
                </div>

                <div className="p-3 bg-amber-50/60 border border-amber-200/80 rounded-xl space-y-1">
                  <div className="flex items-center gap-1.5 font-semibold text-amber-800">
                    <AlertTriangle className="h-3.5 w-3.5 text-amber-600" />
                    <span>Unmitigated Dust Source</span>
                  </div>
                  <p className="text-slate-600 text-[11px] font-normal leading-relaxed">
                    Sentinel-2 satellite sweep detected uncovered excavation at Permit #CNST-2026-8891.
                  </p>
                </div>

                <div className="p-3 bg-blue-50/60 border border-blue-200/80 rounded-xl space-y-1">
                  <div className="flex items-center gap-1.5 font-semibold text-blue-700">
                    <Info className="h-3.5 w-3.5 text-blue-600" />
                    <span>Directive Dispatched</span>
                  </div>
                  <p className="text-slate-600 text-[11px] font-normal leading-relaxed">
                    Water sprinkling directive #REC-01 assigned to Municipal Public Health Division.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* User Profile */}
        <div className="flex items-center space-x-3 pl-2">
          <div className="w-9 h-9 rounded-xl bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-700 font-bold text-xs">
            <User className="h-4 w-4" />
          </div>
          <div className="hidden sm:block text-left text-xs">
            <div className="font-semibold text-slate-900 leading-none">Member Secretary</div>
            <div className="text-slate-500 font-medium text-[11px] mt-0.5">Pollution Control Board</div>
          </div>
        </div>
      </div>
    </header>
  );
};