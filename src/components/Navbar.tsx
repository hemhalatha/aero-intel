import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bell, MapPin, Clock, Search, User, AlertTriangle, ShieldAlert, X, ChevronDown } from 'lucide-react';


const REGIONS = [
  { id: 'INDIA', name: '🇮🇳 All India (National View)', label: 'All India' },
  { id: 'NCR', name: '🏛️ Delhi NCR Region', label: 'Delhi NCR' },
  { id: 'BLR', name: '🌳 Bengaluru Metro', label: 'Bengaluru' },
  { id: 'BOM', name: '🌊 Mumbai MMR Region', label: 'Mumbai MMR' },
  { id: 'CCU', name: '🏛️ Kolkata Metro', label: 'Kolkata' },
  { id: 'MAA', name: '🌴 Chennai Metro', label: 'Chennai' },
  { id: 'HYD', name: '🏰 Hyderabad Metro', label: 'Hyderabad' },
];

const SEARCHABLE_STATIONS = [
  { id: 'ST-05', name: 'Okhla Phase II Corridor', ward: 'W-17 (Delhi)', aqi: 390, status: 'CRITICAL HOTSPOT' },
  { id: 'LKO-TAL-AQ', name: 'Talkatora Industrial', ward: 'LKO-W-04 (Lucknow)', aqi: 365, status: 'CRITICAL HOTSPOT' },
  { id: 'ST-01', name: 'Anand Vihar Transport Hub', ward: 'W-04 (Delhi)', aqi: 342, status: 'HOTSPOT' },
  { id: 'AMD-MAN-AQ', name: 'Maninagar Station', ward: 'AMD-W-12 (Ahmedabad)', aqi: 330, status: 'CRITICAL HOTSPOT' },
  { id: 'BLR-PEE-AQ', name: 'Peenya Industrial Station', ward: 'BLR-W-003 (Bengaluru)', aqi: 315, status: 'CRITICAL HOTSPOT' },
  { id: 'BOM-NAV-AQ', name: 'Navi Mumbai Rabale', ward: 'BOM-W-09 (Mumbai)', aqi: 310, status: 'CRITICAL HOTSPOT' },
  { id: 'CCU-BAL-AQ', name: 'Ballygunge Station', ward: 'CCU-W-02 (Kolkata)', aqi: 305, status: 'CRITICAL HOTSPOT' },
  { id: 'BLR-IND-AQ', name: 'Indiranagar Station', ward: 'BLR-W-002 (Bengaluru)', aqi: 240, status: 'DEGRADED' },
  { id: 'BLR-CBD-AQ', name: 'CBD Station', ward: 'BLR-W-001 (Bengaluru)', aqi: 110, status: 'ONLINE' },
];

export const Navbar: React.FC = () => {
  const [time, setTime] = useState<string>('');
  const [notificationsOpen, setNotificationsOpen] = useState<boolean>(false);
  const [regionMenuOpen, setRegionMenuOpen] = useState<boolean>(false);
  const [selectedRegion, setSelectedRegion] = useState(REGIONS[0]);
  const [globalSearch, setGlobalSearch] = useState('');
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const updateClock = () => {
      const now = new Date();
      setTime(now.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }) + ' IST');
    };
    updateClock();
    const interval = setInterval(updateClock, 1000);
    return () => clearInterval(interval);
  }, []);

  const filtered = globalSearch.trim()
    ? SEARCHABLE_STATIONS.filter(
        (s) =>
          s.id.toLowerCase().includes(globalSearch.toLowerCase()) ||
          s.name.toLowerCase().includes(globalSearch.toLowerCase()) ||
          s.ward.toLowerCase().includes(globalSearch.toLowerCase())
      )
    : [];

  const handleSelectStation = (stationId: string) => {
    setGlobalSearch('');
    setIsDropdownOpen(false);
    navigate(`/?search=${encodeURIComponent(stationId)}`);
  };

  const handleSelectRegion = (reg: typeof REGIONS[0]) => {
    setSelectedRegion(reg);
    setRegionMenuOpen(false);
    navigate(`/?region=${reg.id}`);
  };

  return (
    <header className="h-16 border-b border-slate-200 bg-white sticky top-0 z-50 flex items-center justify-between px-8 shadow-sm">
      {/* Brand */}
      <div className="flex items-center space-x-3 cursor-pointer" onClick={() => navigate('/')}>
        <div className="w-9 h-9 rounded-xl bg-blue-600 flex items-center justify-center text-white font-bold text-sm shadow-sm">
          AI
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-bold text-slate-900 text-base tracking-tight">AeroIntel</span>
            <span className="text-xs px-2 py-0.5 bg-blue-50 text-blue-700 rounded-md font-semibold border border-blue-200">
              All India National Platform
            </span>
          </div>
          <p className="text-xs font-medium text-slate-500">National Air Quality Intelligence & CPCB Network</p>
        </div>
      </div>

      {/* Global Search */}
      <div className="relative hidden md:block">
        <div className="flex items-center space-x-2 bg-slate-100/80 border border-slate-200 px-3.5 py-2 rounded-xl w-80 text-xs focus-within:ring-2 focus-within:ring-blue-500 focus-within:bg-white transition-all">
          <Search className="h-4 w-4 text-slate-400 shrink-0" />
          <input
            type="text"
            value={globalSearch}
            onChange={(e) => {
              setGlobalSearch(e.target.value);
              setIsDropdownOpen(true);
            }}
            onFocus={() => setIsDropdownOpen(true)}
            placeholder="Search stations (e.g. Okhla, Peenya, BKC)..."
            className="bg-transparent border-none text-slate-800 font-normal placeholder-slate-400 focus:outline-none w-full text-xs"
          />
          {globalSearch && (
            <button onClick={() => setGlobalSearch('')} className="text-slate-400 hover:text-slate-600">
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>

        {/* Live Search Auto-Complete Dropdown */}
        {isDropdownOpen && filtered.length > 0 && (
          <div className="absolute left-0 mt-1.5 w-80 bg-white border border-slate-200 rounded-2xl shadow-xl z-50 p-2 space-y-1">
            <div className="px-3 py-1.5 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
              National Stations & Wards
            </div>
            {filtered.map((st) => (
              <button
                key={st.id}
                onClick={() => handleSelectStation(st.id)}
                className="w-full text-left px-3 py-2 rounded-xl hover:bg-blue-50 transition-colors flex items-center justify-between text-xs"
              >
                <div>
                  <div className="font-semibold text-slate-900">{st.name}</div>
                  <div className="text-[11px] text-slate-500">{st.id} ({st.ward})</div>
                </div>
                <span
                  className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                    st.aqi > 300
                      ? 'bg-red-50 text-red-700 border-red-200'
                      : st.aqi > 200
                      ? 'bg-amber-50 text-amber-700 border-amber-200'
                      : 'bg-emerald-50 text-emerald-700 border-emerald-200'
                  }`}
                >
                  {st.aqi} AQI
                </span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Right Tools & User Info */}
      <div className="flex items-center space-x-4">
        {/* Interactive All-India Region Selector */}
        <div className="relative">
          <button
            onClick={() => setRegionMenuOpen(!regionMenuOpen)}
            className="flex items-center gap-2 bg-slate-100 hover:bg-slate-200/80 px-3 py-1.5 rounded-xl border border-slate-200 text-xs font-semibold text-slate-800 transition-colors"
          >
            <MapPin className="h-3.5 w-3.5 text-blue-600" />
            <span>{selectedRegion.label}</span>
            <ChevronDown className="h-3.5 w-3.5 text-slate-500" />
          </button>

          {regionMenuOpen && (
            <div className="absolute right-0 mt-2 w-64 bg-white border border-slate-200 rounded-2xl shadow-xl p-2 z-50 text-xs space-y-1">
              <div className="px-3 py-1 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                Select Monitoring Region
              </div>
              {REGIONS.map((reg) => (
                <button
                  key={reg.id}
                  onClick={() => handleSelectRegion(reg)}
                  className={`w-full text-left px-3 py-2 rounded-xl transition-colors font-medium flex items-center justify-between ${
                    selectedRegion.id === reg.id ? 'bg-blue-50 text-blue-700 font-bold' : 'hover:bg-slate-50 text-slate-700'
                  }`}
                >
                  <span>{reg.name}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="hidden lg:flex items-center space-x-3 text-xs text-slate-600 border-r border-slate-200 pr-4 font-medium">
          <div className="flex items-center gap-1.5 font-mono text-slate-500">
            <Clock className="h-3.5 w-3.5" />
            <span>{time || '19:30:00 IST'}</span>
          </div>
        </div>

        {/* System Status */}
        <div className="flex items-center gap-2 text-xs font-semibold text-emerald-700 bg-emerald-50 px-3 py-1.5 rounded-lg border border-emerald-200">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span className="hidden sm:inline">CPCB All-India Feed Active</span>
        </div>

        {/* Notifications Bell */}
        <div className="relative">
          <button
            onClick={() => setNotificationsOpen(!notificationsOpen)}
            className="p-2 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-xl border border-slate-200 relative transition-colors focus:outline-none"
            title="System Notifications"
          >
            <Bell className="h-4 w-4" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-blue-600 rounded-full"></span>
          </button>

          {notificationsOpen && (
            <div className="absolute right-0 mt-2 w-80 bg-white border border-slate-200 rounded-2xl shadow-lg p-4 z-50 text-xs">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-slate-900">National System Alerts</span>
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
                    Okhla Phase II (Delhi) crossed 390 AQI; Talkatora (Lucknow) crossed 365 AQI.
                  </p>
                </div>

                <div className="p-3 bg-amber-50/60 border border-amber-200/80 rounded-xl space-y-1">
                  <div className="flex items-center gap-1.5 font-semibold text-amber-800">
                    <AlertTriangle className="h-3.5 w-3.5 text-amber-600" />
                    <span>Industrial Hotspot Alert</span>
                  </div>
                  <p className="text-slate-600 text-[11px] font-normal leading-relaxed">
                    Peenya Industrial Zone (Bengaluru) flagged 315 AQI with PM10 dominance.
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
            <div className="text-slate-500 font-medium text-[11px] mt-0.5">Central Pollution Control Board</div>
          </div>
        </div>
      </div>
    </header>
  );
};