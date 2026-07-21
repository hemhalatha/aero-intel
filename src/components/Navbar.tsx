import React, { useState, useEffect } from 'react';
import { Activity, Bell, Shield, MapPin, Radio, Clock } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export const Navbar: React.FC = () => {
  const [time, setTime] = useState<string>('');
  const [notificationsOpen, setNotificationsOpen] = useState(false);

  useEffect(() => {
    const updateClock = () => {
      const now = new Date();
      setTime(now.toLocaleTimeString('en-US', { hour12: false }) + ' IST');
    };
    updateClock();
    const interval = setInterval(updateClock, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="h-16 border-b border-dark-700/80 bg-dark-900/90 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-50">
      {/* Brand & System Status */}
      <div className="flex items-center space-x-4">
        <motion.div 
          whileHover={{ scale: 1.05 }}
          className="p-2 bg-brand-cyan/10 border border-brand-cyan/40 rounded-lg text-brand-cyan shadow-neon-cyan"
        >
          <Activity className="h-5 w-5 animate-pulse" />
        </motion.div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="font-mono text-lg font-bold tracking-wider text-white">
              AEROINTEL <span className="text-xs px-2 py-0.5 bg-brand-cyan/20 text-brand-cyan border border-brand-cyan/40 rounded-md">GOTHAM-OS v2.4</span>
            </h1>
          </div>
          <p className="text-[11px] text-gray-400 font-mono flex items-center gap-2">
            <span>NASA/CPCB DIRECT SATELLITE STREAM</span>
            <span className="text-gray-600">•</span>
            <span className="text-brand-green flex items-center gap-1">
              <Radio className="h-3 w-3 animate-ping" /> 904 CAAQMS STATIONS ONLINE
            </span>
          </p>
        </div>
      </div>

      {/* Center Context Pill */}
      <div className="hidden lg:flex items-center space-x-3 px-4 py-1.5 glass-panel rounded-full text-xs font-mono">
        <div className="flex items-center gap-1.5 text-brand-cyan">
          <MapPin className="h-3.5 w-3.5" />
          <span className="font-bold">DELHI-NCR METRO ZONE</span>
        </div>
        <span className="text-gray-600">|</span>
        <div className="flex items-center gap-1.5 text-gray-300">
          <Clock className="h-3.5 w-3.5 text-brand-amber" />
          <span>{time || '19:30:00 IST'}</span>
        </div>
      </div>

      {/* Right Actions */}
      <div className="flex items-center space-x-4">
        {/* Notification Bell Dropdown */}
        <div className="relative">
          <motion.button 
            whileTap={{ scale: 0.95 }}
            onClick={() => setNotificationsOpen(!notificationsOpen)}
            className="p-2 text-gray-300 hover:text-white bg-dark-800/80 hover:bg-dark-700 rounded-lg border border-dark-700 relative transition-all"
          >
            <Bell className="h-4 w-4" />
            <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-brand-red rounded-full animate-pulse"></span>
          </motion.button>

          <AnimatePresence>
            {notificationsOpen && (
              <motion.div
                initial={{ opacity: 0, y: 10, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 10, scale: 0.95 }}
                className="absolute right-0 mt-2 w-80 glass-panel border border-dark-700 rounded-xl p-4 shadow-2xl z-50 font-mono text-xs"
              >
                <div className="flex justify-between items-center pb-2 border-b border-dark-700 mb-3">
                  <span className="font-bold text-white">LIVE SYSTEM ALERTS</span>
                  <span className="text-[10px] bg-brand-red/20 text-brand-red px-1.5 py-0.5 rounded">3 NEW</span>
                </div>
                <div className="space-y-2.5">
                  <div className="p-2 bg-dark-900/80 border-l-2 border-brand-red rounded">
                    <div className="text-brand-red font-bold">AQI Spike Alert</div>
                    <div className="text-gray-400 text-[11px]">Ward 17 crossed 390 AQI limit.</div>
                  </div>
                  <div className="p-2 bg-dark-900/80 border-l-2 border-brand-amber rounded">
                    <div className="text-brand-amber font-bold">Wind Shift Warning</div>
                    <div className="text-gray-400 text-[11px]">SSW vector spreading dust northeast.</div>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* User Profile */}
        <div className="flex items-center space-x-3 border-l border-dark-700/80 pl-4">
          <div className="w-8 h-8 rounded-lg bg-brand-cyan/20 border border-brand-cyan/50 flex items-center justify-center text-brand-cyan font-mono font-bold text-xs shadow-neon-cyan">
            CMD
          </div>
          <div className="hidden sm:block text-left text-xs font-mono">
            <div className="font-semibold text-gray-200">Director General</div>
            <div className="text-brand-cyan text-[10px]">Command Level 1</div>
          </div>
        </div>
      </div>
    </header>
  );
};