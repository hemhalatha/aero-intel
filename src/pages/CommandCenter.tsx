import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip } from 'recharts';
import { AlertTriangle, WifiOff, Thermometer, Wind, ShieldAlert, Compass, Activity, ArrowRight, CheckCircle2 } from 'lucide-react';
import { motion } from 'framer-motion';
import { mockDashboardMetrics, mockStations, mockWards, mockTrendData } from '../mock/data';

export const CommandCenter: React.FC = () => {
  const [animatedAQI, setAnimatedAQI] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setAnimatedAQI((prev) => {
        if (prev < mockDashboardMetrics.cityAQI) return prev + 4;
        return mockDashboardMetrics.cityAQI;
      });
    }, 20);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="space-y-6">
      {/* Top Glassmorphic Metric Widgets */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <motion.div whileHover={{ y: -2 }} className="glass-panel p-4 rounded-xl relative overflow-hidden border-l-4 border-brand-amber shadow-lg">
          <div className="text-[10px] text-gray-400 font-mono tracking-wider">CITY-WIDE AVG AQI</div>
          <div className="text-4xl font-extrabold font-mono text-brand-amber mt-1 flex items-baseline gap-2">
            <span>{animatedAQI}</span>
            <span className="text-xs text-brand-amber/80 font-normal">PM2.5 / PM10</span>
          </div>
          <div className="text-xs text-brand-amber/90 mt-2 font-mono flex items-center gap-1.5">
            <AlertTriangle className="h-3.5 w-3.5" /> POOR / UNHEALTHY BAND
          </div>
          <div className="absolute right-3 top-3 p-2 bg-brand-amber/10 text-brand-amber rounded-lg">
            <Activity className="h-5 w-5" />
          </div>
        </motion.div>

        <motion.div whileHover={{ y: -2 }} className="glass-panel p-4 rounded-xl relative border-l-4 border-brand-red shadow-lg">
          <div className="text-[10px] text-gray-400 font-mono tracking-wider">ACTIVE HOTSPOTS</div>
          <div className="text-4xl font-extrabold font-mono text-brand-red mt-1">{mockDashboardMetrics.activeHotspots}</div>
          <div className="text-xs text-brand-red mt-2 font-mono flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-brand-red animate-ping"></span> Critical Interventions Dispatched
          </div>
          <div className="absolute right-3 top-3 p-2 bg-brand-red/10 text-brand-red rounded-lg">
            <ShieldAlert className="h-5 w-5" />
          </div>
        </motion.div>

        <motion.div whileHover={{ y: -2 }} className="glass-panel p-4 rounded-xl relative border-l-4 border-gray-600 shadow-lg">
          <div className="text-[10px] text-gray-400 font-mono tracking-wider">OFFLINE SENSORS</div>
          <div className="text-4xl font-extrabold font-mono text-gray-300 mt-1">{mockDashboardMetrics.offlineSensors}</div>
          <div className="text-xs text-gray-400 mt-2 font-mono flex items-center gap-1.5">
            <WifiOff className="h-3.5 w-3.5" /> Maintenance Team Assigned
          </div>
        </motion.div>

        <motion.div whileHover={{ y: -2 }} className="glass-panel p-4 rounded-xl relative border-l-4 border-brand-cyan shadow-lg">
          <div className="text-[10px] text-gray-400 font-mono tracking-wider">WORST IMPACTED WARD</div>
          <div className="text-lg font-bold font-mono text-brand-cyan mt-1 truncate">{mockDashboardMetrics.worstWard}</div>
          <div className="text-xs text-gray-400 mt-2 font-mono">Peak Reading: <span className="text-brand-red font-bold">390 AQI</span></div>
        </motion.div>
      </div>

      {/* Main Command Center Layout: 60% Map Viewport */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Map Container (3/5 = 60% width) */}
        <div className="lg:col-span-3 glass-panel-cyan rounded-xl p-4 flex flex-col h-[520px] relative">
          <div className="flex justify-between items-center mb-3">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-brand-cyan animate-pulse"></span>
              <h3 className="text-xs font-mono font-bold text-gray-200 tracking-wider">
                GEOSPATIAL AIR QUALITY & HOTSPOT MESH
              </h3>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 bg-brand-cyan/20 text-brand-cyan border border-brand-cyan/40 rounded">
              100M MESH RESOLUTION
            </span>
          </div>

          <div className="flex-1 rounded-lg overflow-hidden border border-dark-700 relative z-0">
            <MapContainer center={[28.6139, 77.2090]} zoom={11} className="h-full w-full">
              <TileLayer
                url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                attribution='&copy; CartoDB'
              />
              {mockStations.map((station) => (
                <React.Fragment key={station.id}>
                  <Marker position={[station.lat, station.lng]}>
                    <Popup>
                      <div className="p-1 font-mono text-xs">
                        <strong className="text-brand-cyan">{station.name}</strong><br />
                        AQI: <span className="text-brand-amber font-bold">{station.aqi || 'OFFLINE'}</span><br />
                        Status: {station.status}
                      </div>
                    </Popup>
                  </Marker>
                  {station.aqi > 0 && (
                    <Circle
                      center={[station.lat, station.lng]}
                      radius={2200}
                      pathOptions={{
                        color: station.aqi > 300 ? '#FF4D4D' : '#FFB800',
                        fillColor: station.aqi > 300 ? '#FF4D4D' : '#FFB800',
                        fillOpacity: 0.25,
                      }}
                    />
                  )}
                </React.Fragment>
              ))}
            </MapContainer>
          </div>
        </div>

        {/* Right Side Control Widgets (2/5 = 40% width) */}
        <div className="lg:col-span-2 space-y-6 flex flex-col justify-between">
          {/* Weather & Wind Vector Widget */}
          <div className="glass-panel rounded-xl p-4 space-y-3">
            <h3 className="text-xs font-mono text-gray-400 uppercase tracking-wider">Atmospheric & Wind Dispersion</h3>
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 bg-dark-900/80 rounded-lg border border-dark-700 flex items-center gap-3">
                <Thermometer className="h-5 w-5 text-brand-cyan" />
                <div>
                  <div className="text-[10px] text-gray-500 font-mono">TEMP</div>
                  <div className="text-sm font-bold font-mono text-white">{mockDashboardMetrics.weather.temp}</div>
                </div>
              </div>
              <div className="p-3 bg-dark-900/80 rounded-lg border border-dark-700 flex items-center gap-3">
                <Wind className="h-5 w-5 text-brand-cyan" />
                <div>
                  <div className="text-[10px] text-gray-500 font-mono">WIND VELOCITY</div>
                  <div className="text-sm font-bold font-mono text-white">{mockDashboardMetrics.weather.windSpeed}</div>
                </div>
              </div>
            </div>

            <div className="p-3 bg-dark-900/90 rounded-lg border border-dark-700 flex justify-between items-center font-mono text-xs">
              <div className="flex items-center gap-2 text-gray-300">
                <Compass className="h-4 w-4 text-brand-cyan animate-spin" style={{ animationDuration: '12s' }} />
                <span>Vector Angle:</span>
              </div>
              <span className="text-brand-cyan font-bold">{mockDashboardMetrics.weather.windDirection}</span>
            </div>
          </div>

          {/* Worst Impacted Wards Table */}
          <div className="glass-panel rounded-xl p-4 flex-1 flex flex-col justify-between">
            <h3 className="text-xs font-mono text-gray-400 uppercase tracking-wider mb-2">Ward Risk Rankings</h3>
            <div className="space-y-2">
              {mockWards.map((ward) => (
                <div key={ward.id} className="flex justify-between items-center p-2 bg-dark-900/80 rounded border border-dark-700/80 text-xs font-mono">
                  <span className="text-gray-300 font-medium">{ward.name}</span>
                  <span className={`px-2 py-0.5 rounded font-bold ${ward.aqi > 300 ? 'bg-brand-red/20 text-brand-red border border-brand-red/30' : 'bg-brand-amber/20 text-brand-amber border border-brand-amber/30'}`}>
                    AQI {ward.aqi}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* 24-Hour Trend Chart */}
      <div className="glass-panel p-5 rounded-xl">
        <h3 className="text-xs font-mono text-gray-400 uppercase tracking-wider mb-4">24-Hour Ward Diurnal Trend Comparison</h3>
        <div className="h-52">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={mockTrendData}>
              <XAxis dataKey="time" stroke="#6B7280" fontSize={11} />
              <YAxis stroke="#6B7280" fontSize={11} />
              <Tooltip contentStyle={{ backgroundColor: '#0B0F17', borderColor: '#1F2937', fontSize: '12px' }} />
              <Area type="monotone" dataKey="AQI" stroke="#FFB800" fill="#FFB800" fillOpacity={0.15} />
              <Area type="monotone" dataKey="PM25" stroke="#00F0FF" fill="#00F0FF" fillOpacity={0.1} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Bottom Live Mission Control Event Stream */}
      <div className="glass-panel p-4 rounded-xl font-mono text-xs">
        <div className="text-[10px] text-gray-500 uppercase tracking-widest mb-3">AUTOMATED EVENT DISPATCH STREAM</div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <div className="p-2.5 bg-dark-900/80 border-l-2 border-brand-red rounded flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-brand-red"></span>
            <div>
              <div className="text-white font-bold">17:30 - Hotspot Flagged</div>
              <div className="text-[10px] text-gray-400">Ward 17 AQI &gt; 390</div>
            </div>
          </div>
          <div className="p-2.5 bg-dark-900/80 border-l-2 border-brand-cyan rounded flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-brand-cyan"></span>
            <div>
              <div className="text-white font-bold">17:31 - Multi-Modal Scan</div>
              <div className="text-[10px] text-gray-400">Sentinel-2 & Traffic Sweep</div>
            </div>
          </div>
          <div className="p-2.5 bg-dark-900/80 border-l-2 border-brand-amber rounded flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-brand-amber"></span>
            <div>
              <div className="text-white font-bold">17:32 - Recommendation</div>
              <div className="text-[10px] text-gray-400">Water Sprinkling Directive</div>
            </div>
          </div>
          <div className="p-2.5 bg-dark-900/80 border-l-2 border-brand-green rounded flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-brand-green" />
            <div>
              <div className="text-white font-bold">17:35 - Task Dispatched</div>
              <div className="text-[10px] text-gray-400">Assigned to Municipality</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};