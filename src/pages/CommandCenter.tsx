import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { AlertTriangle, WifiOff, Wind, ShieldAlert, ArrowUpRight, Layers, Filter } from 'lucide-react';
import { mockDashboardMetrics, mockStations, mockWards, mockTrendData } from '../mock/data';

export const CommandCenter: React.FC = () => {
  const [animatedAQI, setAnimatedAQI] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setAnimatedAQI((prev) => {
        if (prev < mockDashboardMetrics.cityAQI) return prev + 6;
        return mockDashboardMetrics.cityAQI;
      });
    }, 15);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="px-8 py-6 space-y-8 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 pb-4 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 mb-1">Executive Air Quality Dashboard</h1>
          <p className="text-sm font-medium text-slate-500">Real-time geospatial monitoring and multi-agency response metrics</p>
        </div>
        <div className="flex items-center gap-3">
          <button className="ui-button-secondary">
            <Filter className="h-4 w-4 text-slate-500" />
            <span>Filter Wards</span>
          </button>
          <button className="ui-button-primary">
            <span>Export Report</span>
          </button>
        </div>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="ui-card flex flex-col justify-between h-40">
          <div className="flex justify-between items-start">
            <span className="text-sm font-medium text-slate-500">Average City AQI</span>
            <span className="px-2.5 py-1 bg-amber-50 text-amber-700 border border-amber-200 text-xs font-semibold rounded-full">
              Poor
            </span>
          </div>
          <div>
            <div className="text-3xl font-bold text-slate-900 tracking-tight">{animatedAQI}</div>
            <p className="text-xs font-medium text-slate-500 mt-0.5">PM2.5 / PM10 Concentration</p>
          </div>
          <div className="flex items-center gap-1 text-xs font-medium text-amber-700">
            <ArrowUpRight className="h-4 w-4" />
            <span>+12 pts vs yesterday</span>
          </div>
        </div>

        <div className="ui-card flex flex-col justify-between h-40">
          <div className="flex justify-between items-start">
            <span className="text-sm font-medium text-slate-500">Active Hotspots</span>
            <span className="px-2.5 py-1 bg-red-50 text-red-700 border border-red-200 text-xs font-semibold rounded-full">
              Critical
            </span>
          </div>
          <div>
            <div className="text-3xl font-bold text-slate-900 tracking-tight">{mockDashboardMetrics.activeHotspots}</div>
            <p className="text-xs font-medium text-slate-500 mt-0.5">Wards Exceeding Limits</p>
          </div>
          <div className="flex items-center gap-1 text-xs font-medium text-red-600">
            <ShieldAlert className="h-4 w-4" />
            <span>Intervention Required</span>
          </div>
        </div>

        <div className="ui-card flex flex-col justify-between h-40">
          <div className="flex justify-between items-start">
            <span className="text-sm font-medium text-slate-500">Offline Sensors</span>
            <span className="px-2.5 py-1 bg-slate-100 text-slate-700 border border-slate-200 text-xs font-semibold rounded-full">
              Maintenance
            </span>
          </div>
          <div>
            <div className="text-3xl font-bold text-slate-900 tracking-tight">{mockDashboardMetrics.offlineSensors}</div>
            <p className="text-xs font-medium text-slate-500 mt-0.5">Out of 904 Station Network</p>
          </div>
          <div className="flex items-center gap-1 text-xs font-medium text-slate-500">
            <WifiOff className="h-4 w-4 text-slate-400" />
            <span>Field teams dispatched</span>
          </div>
        </div>

        <div className="ui-card flex flex-col justify-between h-40">
          <div className="flex justify-between items-start">
            <span className="text-sm font-medium text-slate-500">Worst Impacted Ward</span>
            <span className="px-2.5 py-1 bg-red-50 text-red-700 border border-red-200 text-xs font-semibold rounded-full">
              Severe
            </span>
          </div>
          <div>
            <div className="text-lg font-bold text-slate-900 truncate">{mockDashboardMetrics.worstWard}</div>
            <p className="text-xs font-medium text-slate-500 mt-0.5">Peak Station Reading: 390 AQI</p>
          </div>
          <div className="text-xs font-medium text-slate-700">
            <span>Primary Contributor: PM10</span>
          </div>
        </div>
      </div>

      {/* Main Map & Side Panels */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 ui-card flex flex-col h-[500px]">
          <div className="flex justify-between items-center mb-4">
            <div className="flex items-center gap-2">
              <Layers className="h-5 w-5 text-blue-600" />
              <h2 className="text-base font-semibold text-slate-900">Geospatial AQI Monitoring Layer</h2>
            </div>
            <span className="text-xs font-medium text-slate-600 bg-slate-100 px-3 py-1 rounded-lg border border-slate-200">
              100m Resolution Grid
            </span>
          </div>

          <div className="flex-1 rounded-xl overflow-hidden border border-slate-200 relative z-0">
            <MapContainer center={[28.6139, 77.2090]} zoom={11} className="h-full w-full">
              <TileLayer
                url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
                attribution='&copy; OpenStreetMap'
              />
              {mockStations.map((station) => (
                <React.Fragment key={station.id}>
                  <Marker position={[station.lat, station.lng]}>
                    <Popup>
                      <div className="p-1 text-xs">
                        <strong className="text-slate-900 font-semibold">{station.name}</strong><br />
                        <span className="text-slate-500 font-normal">AQI: </span>
                        <span className="font-bold text-slate-900">{station.aqi || 'OFFLINE'}</span><br />
                        <span className="text-slate-500 font-normal">Status: {station.status}</span>
                      </div>
                    </Popup>
                  </Marker>
                  {station.aqi > 0 && (
                    <Circle
                      center={[station.lat, station.lng]}
                      radius={2000}
                      pathOptions={{
                        color: station.aqi > 300 ? '#DC2626' : '#D97706',
                        fillColor: station.aqi > 300 ? '#DC2626' : '#D97706',
                        fillOpacity: 0.2,
                        weight: 1.5,
                      }}
                    />
                  )}
                </React.Fragment>
              ))}
            </MapContainer>
          </div>
        </div>

        <div className="space-y-6">
          <div className="ui-card space-y-4">
            <h2 className="text-sm font-semibold text-slate-900">Meteorology & Dispersion</h2>
            <div className="grid grid-cols-2 gap-4">
              <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
                <span className="text-xs font-medium text-slate-500">Temperature</span>
                <div className="text-lg font-bold text-slate-900 mt-0.5">{mockDashboardMetrics.weather.temp}</div>
              </div>
              <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
                <span className="text-xs font-medium text-slate-500">Wind Velocity</span>
                <div className="text-lg font-bold text-slate-900 mt-0.5">{mockDashboardMetrics.weather.windSpeed}</div>
              </div>
            </div>

            <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200 flex justify-between items-center text-xs">
              <div className="flex items-center gap-2 text-slate-700 font-medium">
                <Wind className="h-4 w-4 text-blue-600" />
                <span>Wind Direction:</span>
              </div>
              <span className="font-semibold text-slate-900">{mockDashboardMetrics.weather.windDirection}</span>
            </div>
          </div>

          <div className="ui-card">
            <h2 className="text-sm font-semibold text-slate-900 mb-4">Highest Pollution Wards</h2>
            <div className="space-y-2">
              {mockWards.map((ward) => (
                <div key={ward.id} className="flex justify-between items-center p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs">
                  <span className="text-slate-700 font-medium">{ward.name}</span>
                  <span className={`px-2.5 py-1 rounded-md font-semibold ${
                    ward.aqi > 300 ? 'bg-red-50 text-red-700 border border-red-200' : 'bg-amber-50 text-amber-700 border border-amber-200'
                  }`}>
                    {ward.aqi} AQI
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Trend Chart */}
      <div className="ui-card space-y-4">
        <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-2 pb-2 border-b border-slate-100">
          <div>
            <h2 className="text-base font-semibold text-slate-900 mb-1">24-Hour Diurnal AQI Trend</h2>
            <p className="text-xs font-medium text-slate-500">Comparative particulate concentration trajectory across metro zones</p>
          </div>
          <div className="flex items-center gap-6 text-xs font-medium">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 bg-blue-600 rounded-sm"></span>
              <span className="text-slate-700">AQI Index</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 bg-slate-900 rounded-sm"></span>
              <span className="text-slate-700">PM2.5 (µg/m³)</span>
            </div>
          </div>
        </div>

        <div className="h-64 pt-2">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={mockTrendData} margin={{ top: 10, right: 10, left: -15, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" vertical={false} />
              <XAxis dataKey="time" stroke="#64748B" fontSize={12} tickLine={false} />
              <YAxis stroke="#64748B" fontSize={12} tickLine={false} />
              <Tooltip
                contentStyle={{ 
                  backgroundColor: '#FFFFFF', 
                  borderColor: '#E2E8F0', 
                  borderRadius: '12px', 
                  boxShadow: '0 4px 12px rgba(0, 0, 0, 0.08)',
                  color: '#0F172A'
                }}
              />
              <Area type="monotone" dataKey="AQI" stroke="#2563EB" fill="#DBEAFE" fillOpacity={0.5} strokeWidth={2.5} />
              <Area type="monotone" dataKey="PM25" stroke="#0F172A" fill="#94A3B8" fillOpacity={0.2} strokeWidth={2.5} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};