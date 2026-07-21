import React, { useEffect, useMemo, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { AlertTriangle, WifiOff, Wind, ShieldAlert, ArrowUpRight, Layers, Filter, RefreshCw } from 'lucide-react';
import { mockDashboardMetrics, mockStations, mockWards, mockTrendData } from '../mock/data';
import { Station, Ward } from '../types';

type ApiPollutantReading = {
  pollutant: string;
  value: number;
  unit?: string;
  data_quality_status?: string;
};

type ApiStationReading = {
  station_code: string;
  station_name: string;
  ward_code?: string;
  latitude: number;
  longitude: number;
  observed_at?: string;
  data_quality_status?: string;
  readings?: ApiPollutantReading[];
};

type ApiWardSummary = {
  ward_code: string;
  average_aqi: number;
  station_count?: number;
  display_label?: string;
  band?: string;
};

type ApiHealthSnapshot = {
  station_code: string;
  station_name?: string;
  status: 'ONLINE' | 'OFFLINE' | 'DEGRADED' | 'DELAYED';
  data_quality_score?: number;
  is_reliable?: boolean;
};

type ApiHotspot = {
  id?: number;
  hotspot_uid?: string;
  hotspot_id?: string;
  ward_code?: string;
  current_aqi?: number;
  aqi?: number;
  severity?: string;
  last_detected_at?: string;
  detected_at?: string;
  trigger_reasons?: Array<{ reason?: string; pollutant?: string }>;
};

type ApiTrendPoint = {
  observed_at: string;
  average_aqi: number;
};

type ApiDashboard = {
  generated_at?: string;
  city_average_aqi?: number;
  worst_affected_ward?: ApiWardSummary | null;
  active_hotspot_count?: number;
  offline_or_degraded_station_count?: number;
  latest_reliable_station_readings?: ApiStationReading[];
  weather_summary?: {
    temperature_c?: number;
    relative_humidity_pct?: number;
    data_quality_status?: string;
  };
  wind_information?: {
    wind_speed_kmh?: number;
    wind_direction_degrees?: number;
    data_quality_status?: string;
  };
  current_hotspot_summaries?: ApiHotspot[];
  city_pollution_trend?: ApiTrendPoint[];
};

type DashboardState = {
  metrics: typeof mockDashboardMetrics;
  stations: Station[];
  wards: Ward[];
  trend: Array<{ time: string; AQI: number; PM25: number; PM10?: number }>;
  hotspots: ApiHotspot[];
  apiStations: ApiStationReading[];
  health: ApiHealthSnapshot[];
  usingFallback: boolean;
  error?: string;
  refreshedAt?: Date;
};

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
const REFRESH_MS = 60_000;

export const CommandCenter: React.FC = () => {
  const [dashboard, setDashboard] = useState<DashboardState>(() => createFallbackDashboard());
  const [animatedAQI, setAnimatedAQI] = useState(0);
  const [selectedStation, setSelectedStation] = useState<ApiStationReading | null>(null);
  const [layers, setLayers] = useState({ heat: true, stations: true, hotspots: true });

  useEffect(() => {
    let active = true;

    const loadDashboard = async () => {
      const nextDashboard = await fetchDashboardState();
      if (active) {
        setDashboard(nextDashboard);
      }
    };

    loadDashboard();
    const timer = window.setInterval(loadDashboard, REFRESH_MS);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, []);

  useEffect(() => {
    setAnimatedAQI(0);
    const targetAQI = dashboard.metrics.cityAQI;
    const timer = window.setInterval(() => {
      setAnimatedAQI((prev) => Math.min(targetAQI, prev + Math.max(1, Math.ceil(targetAQI / 36))));
    }, 20);
    return () => window.clearInterval(timer);
  }, [dashboard.metrics.cityAQI]);

  const stationHealthByCode = useMemo(() => {
    return new Map(dashboard.health.map((item) => [item.station_code, item]));
  }, [dashboard.health]);

  const mapCenter: [number, number] = dashboard.stations.length
    ? [dashboard.stations[0].lat, dashboard.stations[0].lng]
    : [12.9716, 77.5946];

  return (
    <div className="px-8 py-6 space-y-8 max-w-7xl mx-auto">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 pb-4 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 mb-1">Executive Air Quality Dashboard</h1>
          <p className="text-sm font-medium text-slate-500">Real-time geospatial monitoring and multi-agency response metrics</p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <span className={`inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-semibold ${dashboard.usingFallback ? 'border-amber-200 bg-amber-50 text-amber-700' : 'border-emerald-200 bg-emerald-50 text-emerald-700'}`}>
            <RefreshCw className="h-3.5 w-3.5" />
            {dashboard.usingFallback ? 'Seeded standby data' : 'Live backend data'}
          </span>
          <button className="ui-button-secondary">
            <Filter className="h-4 w-4 text-slate-500" />
            <span>Filter Wards</span>
          </button>
          <button className="ui-button-primary">
            <span>Export Report</span>
          </button>
        </div>
      </div>

      {dashboard.usingFallback && (
        <div className="ui-card border-amber-200 bg-amber-50 text-sm text-amber-900 hover:shadow-sm">
          <div className="flex items-start gap-3">
            <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0" />
            <p>
              <strong>Backend data is unavailable.</strong> {dashboard.error || 'Showing deterministic seeded data so the command center remains usable.'}
            </p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="ui-card flex flex-col justify-between h-40">
          <div className="flex justify-between items-start">
            <span className="text-sm font-medium text-slate-500">Average City AQI</span>
            <span className={`px-2.5 py-1 text-xs font-semibold rounded-full border ${aqiBadgeClass(dashboard.metrics.cityAQI)}`}>{aqiBand(dashboard.metrics.cityAQI)}</span>
          </div>
          <div>
            <div className="text-3xl font-bold text-slate-900 tracking-tight">{animatedAQI}</div>
            <p className="text-xs font-medium text-slate-500 mt-0.5">PM2.5 / PM10 Concentration</p>
          </div>
          <div className="flex items-center gap-1 text-xs font-medium text-amber-700">
            <ArrowUpRight className="h-4 w-4" />
            <span>{dashboard.usingFallback ? 'Seeded scenario baseline' : `Updated ${formatTime(dashboard.refreshedAt)}`}</span>
          </div>
        </div>

        <div className="ui-card flex flex-col justify-between h-40">
          <div className="flex justify-between items-start">
            <span className="text-sm font-medium text-slate-500">Active Hotspots</span>
            <span className="px-2.5 py-1 bg-red-50 text-red-700 border border-red-200 text-xs font-semibold rounded-full">Critical</span>
          </div>
          <div>
            <div className="text-3xl font-bold text-slate-900 tracking-tight">{dashboard.metrics.activeHotspots}</div>
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
            <span className="px-2.5 py-1 bg-slate-100 text-slate-700 border border-slate-200 text-xs font-semibold rounded-full">Maintenance</span>
          </div>
          <div>
            <div className="text-3xl font-bold text-slate-900 tracking-tight">{dashboard.metrics.offlineSensors}</div>
            <p className="text-xs font-medium text-slate-500 mt-0.5">Offline or degraded station network</p>
          </div>
          <div className="flex items-center gap-1 text-xs font-medium text-slate-500">
            <WifiOff className="h-4 w-4 text-slate-400" />
            <span>Sensor health aware analytics</span>
          </div>
        </div>

        <div className="ui-card flex flex-col justify-between h-40">
          <div className="flex justify-between items-start">
            <span className="text-sm font-medium text-slate-500">Worst Impacted Ward</span>
            <span className="px-2.5 py-1 bg-red-50 text-red-700 border border-red-200 text-xs font-semibold rounded-full">Severe</span>
          </div>
          <div>
            <div className="text-lg font-bold text-slate-900 truncate">{dashboard.metrics.worstWard}</div>
            <p className="text-xs font-medium text-slate-500 mt-0.5">Peak Station Reading: {Math.max(...dashboard.stations.map((item) => item.aqi), 0)} AQI</p>
          </div>
          <div className="text-xs font-medium text-slate-700">
            <span>Primary Contributor: PM10</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 ui-card flex flex-col h-[500px]">
          <div className="flex flex-col gap-3 sm:flex-row sm:justify-between sm:items-center mb-4">
            <div className="flex items-center gap-2">
              <Layers className="h-5 w-5 text-blue-600" />
              <h2 className="text-base font-semibold text-slate-900">Geospatial AQI Monitoring Layer</h2>
            </div>
            <div className="flex flex-wrap gap-2">
              {Object.entries(layers).map(([key, enabled]) => (
                <button
                  key={key}
                  type="button"
                  aria-pressed={enabled}
                  onClick={() => setLayers((current) => ({ ...current, [key]: !enabled }))}
                  className="rounded-full border border-slate-200 px-3 py-1 text-xs font-medium capitalize text-slate-600 transition active:scale-95 aria-pressed:bg-blue-600 aria-pressed:text-white"
                >
                  {key}
                </button>
              ))}
            </div>
          </div>

          <div className="flex-1 rounded-xl overflow-hidden border border-slate-200 relative z-0">
            <MapContainer center={mapCenter} zoom={11} className="h-full w-full">
              <TileLayer
                url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
                attribution="&copy; OpenStreetMap"
              />
              {dashboard.stations.map((station) => {
                const health = stationHealthByCode.get(station.id);
                const unhealthy = station.status !== 'ONLINE' || health?.is_reliable === false;
                return (
                  <React.Fragment key={station.id}>
                    {layers.stations && (
                      <Marker position={[station.lat, station.lng]} eventHandlers={{ click: () => setSelectedStation(findApiStation(dashboard.apiStations, station)) }}>
                        <Popup>
                          <div className="p-1 text-xs">
                            <strong className="text-slate-900 font-semibold">{station.name}</strong><br />
                            <span className="text-slate-500 font-normal">AQI: </span>
                            <span className="font-bold text-slate-900">{station.aqi || 'OFFLINE'}</span><br />
                            <span className="text-slate-500 font-normal">Status: {health?.status || station.status}</span>
                          </div>
                        </Popup>
                      </Marker>
                    )}
                    {layers.heat && station.aqi > 0 && (
                      <Circle
                        center={[station.lat, station.lng]}
                        radius={unhealthy ? 1200 : 2200}
                        pathOptions={{
                          color: unhealthy ? '#64748B' : heatColor(station.aqi),
                          fillColor: unhealthy ? '#64748B' : heatColor(station.aqi),
                          fillOpacity: unhealthy ? 0.12 : 0.22,
                          weight: 1.5,
                        }}
                      />
                    )}
                  </React.Fragment>
                );
              })}
              {layers.hotspots && dashboard.hotspots.map((hotspot, index) => {
                const station = dashboard.stations.find((item) => item.id === hotspot.ward_code || item.name.includes(hotspot.ward_code || '')) || dashboard.stations[index % dashboard.stations.length];
                if (!station) return null;
                return (
                  <Circle
                    key={hotspot.hotspot_uid || hotspot.hotspot_id || hotspot.id || index}
                    center={[station.lat + 0.003, station.lng + 0.003]}
                    radius={850}
                    pathOptions={{ color: '#DC2626', fillColor: '#DC2626', fillOpacity: 0.35, weight: 2 }}
                  >
                    <Popup>
                      <strong>Hotspot {hotspot.hotspot_uid || hotspot.hotspot_id || hotspot.id}</strong><br />
                      {hotspot.ward_code || 'Unknown ward'} / {Math.round(hotspot.current_aqi || hotspot.aqi || 0)} AQI
                    </Popup>
                  </Circle>
                );
              })}
            </MapContainer>
          </div>
        </div>

        <div className="space-y-6">
          <div className="ui-card space-y-4">
            <h2 className="text-sm font-semibold text-slate-900">Meteorology & Dispersion</h2>
            <div className="grid grid-cols-2 gap-4">
              <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
                <span className="text-xs font-medium text-slate-500">Temperature</span>
                <div className="text-lg font-bold text-slate-900 mt-0.5">{dashboard.metrics.weather.temp}</div>
              </div>
              <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
                <span className="text-xs font-medium text-slate-500">Wind Velocity</span>
                <div className="text-lg font-bold text-slate-900 mt-0.5">{dashboard.metrics.weather.windSpeed}</div>
              </div>
            </div>

            <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200 flex justify-between items-center text-xs">
              <div className="flex items-center gap-2 text-slate-700 font-medium">
                <Wind className="h-4 w-4 text-blue-600" />
                <span>Wind Direction:</span>
              </div>
              <span className="font-semibold text-slate-900">{dashboard.metrics.weather.windDirection}</span>
            </div>
          </div>

          <div className="ui-card">
            <h2 className="text-sm font-semibold text-slate-900 mb-4">Highest Pollution Wards</h2>
            <div className="space-y-2">
              {dashboard.wards.map((ward) => (
                <div key={ward.id} className="flex justify-between items-center p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs">
                  <span className="text-slate-700 font-medium">{ward.name}</span>
                  <span className={`px-2.5 py-1 rounded-md font-semibold ${ward.aqi > 300 ? 'bg-red-50 text-red-700 border border-red-200' : 'bg-amber-50 text-amber-700 border border-amber-200'}`}>
                    {ward.aqi} AQI
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="ui-card">
            <h2 className="text-sm font-semibold text-slate-900 mb-4">Station Pollutants</h2>
            {selectedStation ? (
              <div className="grid grid-cols-2 gap-3 text-xs">
                {(selectedStation.readings || []).filter((item) => item.pollutant !== 'AQI').map((item) => (
                  <div key={item.pollutant} className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                    <span className="text-slate-500">{item.pollutant}</span>
                    <div className="mt-1 font-bold text-slate-900">{Math.round(item.value)} {item.unit || ''}</div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-500">Click a monitoring station to view pollutant details from the environmental repository.</p>
            )}
          </div>
        </div>
      </div>

      <div className="ui-card space-y-4">
        <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-2 pb-2 border-b border-slate-100">
          <div>
            <h2 className="text-base font-semibold text-slate-900 mb-1">24-Hour Diurnal AQI Trend</h2>
            <p className="text-xs font-medium text-slate-500">Comparative particulate concentration trajectory across metro zones</p>
          </div>
        </div>

        <div className="h-64 pt-2">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={dashboard.trend} margin={{ top: 10, right: 10, left: -15, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" vertical={false} />
              <XAxis dataKey="time" stroke="#64748B" fontSize={12} tickLine={false} />
              <YAxis stroke="#64748B" fontSize={12} tickLine={false} />
              <Tooltip contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#E2E8F0', borderRadius: '12px', boxShadow: '0 4px 12px rgba(0, 0, 0, 0.08)', color: '#0F172A' }} />
              <Area type="monotone" dataKey="AQI" stroke="#2563EB" fill="#DBEAFE" fillOpacity={0.5} strokeWidth={2.5} />
              <Area type="monotone" dataKey="PM25" stroke="#0F172A" fill="#94A3B8" fillOpacity={0.2} strokeWidth={2.5} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

async function fetchDashboardState(): Promise<DashboardState> {
  try {
    const dashboard = await fetchJson<ApiDashboard>('/api/v1/command-center/dashboard');
    const [health, hotspots] = await Promise.all([
      fetchOptionalJson<ApiHealthSnapshot[]>('/api/v1/sensor-health/stations', []),
      fetchOptionalJson<ApiHotspot[]>('/api/v1/hotspots?status=ACTIVE', dashboard.current_hotspot_summaries || []),
    ]);

    return mapApiDashboard(dashboard, health, hotspots);
  } catch (error) {
    return createFallbackDashboard(error instanceof Error ? error.message : 'Unable to load backend dashboard data');
  }
}

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) {
    let detail = '';
    try {
      const payload = await response.json();
      detail = payload.detail ? `: ${payload.detail}` : '';
    } catch {
      detail = '';
    }
    throw new Error(`AeroIntel API returned ${response.status}${detail}`);
  }
  return response.json();
}

async function fetchOptionalJson<T>(path: string, fallback: T): Promise<T> {
  try {
    return await fetchJson<T>(path);
  } catch {
    return fallback;
  }
}

function mapApiDashboard(dashboard: ApiDashboard, health: ApiHealthSnapshot[], hotspots: ApiHotspot[]): DashboardState {
  const apiStations = dashboard.latest_reliable_station_readings || [];
  const stations = apiStations.length ? apiStations.map((station) => toStation(station, health)) : mockStations;
  const wards = dashboard.worst_affected_ward ? [dashboard.worst_affected_ward, ...mockWards.map((ward) => ({ ward_code: ward.id, average_aqi: ward.aqi, display_label: ward.riskLevel }))].map(toWard).slice(0, 5) : mockWards;
  const trend = dashboard.city_pollution_trend?.length ? dashboard.city_pollution_trend.map((point) => ({ time: formatTime(point.observed_at), AQI: Math.round(point.average_aqi), PM25: Math.round(point.average_aqi * 0.62) })) : mockTrendData;
  const weather = dashboard.weather_summary;
  const wind = dashboard.wind_information;

  return {
    metrics: {
      cityAQI: Math.round(dashboard.city_average_aqi || average(stations.map((item) => item.aqi)) || mockDashboardMetrics.cityAQI),
      activeHotspots: dashboard.active_hotspot_count ?? hotspots.length,
      offlineSensors: dashboard.offline_or_degraded_station_count ?? health.filter((item) => ['OFFLINE', 'DEGRADED'].includes(item.status)).length,
      worstWard: dashboard.worst_affected_ward?.ward_code || mockDashboardMetrics.worstWard,
      weather: {
        temp: weather?.temperature_c != null ? `${Math.round(weather.temperature_c)} deg C` : mockDashboardMetrics.weather.temp,
        humidity: weather?.relative_humidity_pct != null ? `${Math.round(weather.relative_humidity_pct)}%` : mockDashboardMetrics.weather.humidity,
        windSpeed: wind?.wind_speed_kmh != null ? `${Math.round(wind.wind_speed_kmh)} km/h` : mockDashboardMetrics.weather.windSpeed,
        windDirection: wind?.wind_direction_degrees != null ? `${Math.round(wind.wind_direction_degrees)} deg` : mockDashboardMetrics.weather.windDirection,
      },
    },
    stations,
    wards,
    trend,
    hotspots,
    apiStations,
    health,
    usingFallback: false,
    refreshedAt: new Date(),
  };
}

function createFallbackDashboard(error?: string): DashboardState {
  return {
    metrics: mockDashboardMetrics,
    stations: mockStations,
    wards: mockWards,
    trend: mockTrendData,
    hotspots: [],
    apiStations: mockStations.map((station) => ({
      station_code: station.id,
      station_name: station.name,
      latitude: station.lat,
      longitude: station.lng,
      ward_code: station.id,
      data_quality_status: station.status === 'ONLINE' ? 'valid' : 'unreliable',
      readings: [
        { pollutant: 'AQI', value: station.aqi, unit: 'index' },
        { pollutant: 'PM25', value: Math.round(station.aqi * 0.56), unit: 'ug/m3' },
        { pollutant: 'PM10', value: Math.round(station.aqi * 0.86), unit: 'ug/m3' },
        { pollutant: 'NO2', value: Math.round(station.aqi * 0.18), unit: 'ug/m3' },
      ],
    })),
    health: [],
    usingFallback: true,
    error,
    refreshedAt: new Date(),
  };
}

function toStation(station: ApiStationReading, health: ApiHealthSnapshot[]): Station {
  const snapshot = health.find((item) => item.station_code === station.station_code);
  const status = snapshot?.status === 'DELAYED' ? 'DEGRADED' : snapshot?.status || (station.data_quality_status === 'valid' ? 'ONLINE' : 'DEGRADED');
  return {
    id: station.station_code,
    name: station.station_name,
    lat: station.latitude,
    lng: station.longitude,
    aqi: extractAqi(station),
    status: status === 'OFFLINE' ? 'OFFLINE' : status === 'ONLINE' ? 'ONLINE' : 'DEGRADED',
  };
}

function toWard(ward: ApiWardSummary): Ward {
  const aqi = Math.round(ward.average_aqi || 0);
  return {
    id: ward.ward_code,
    name: ward.ward_code,
    aqi,
    riskLevel: aqi >= 300 ? 'SEVERE' : aqi >= 200 ? 'VERY_POOR' : aqi >= 150 ? 'POOR' : 'MODERATE',
  };
}

function findApiStation(apiStations: ApiStationReading[], station: Station): ApiStationReading {
  return apiStations.find((item) => item.station_code === station.id) || {
    station_code: station.id,
    station_name: station.name,
    latitude: station.lat,
    longitude: station.lng,
    readings: [{ pollutant: 'AQI', value: station.aqi, unit: 'index' }],
  };
}

function extractAqi(station: ApiStationReading): number {
  const value = station.readings?.find((item) => item.pollutant === 'AQI')?.value;
  return Math.round(value || 0);
}

function average(values: number[]): number {
  const usable = values.filter((value) => Number.isFinite(value) && value > 0);
  return usable.length ? usable.reduce((sum, value) => sum + value, 0) / usable.length : 0;
}

function formatTime(value?: Date | string): string {
  if (!value) return 'pending';
  const date = value instanceof Date ? value : new Date(value);
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function aqiBand(value: number): string {
  if (value >= 300) return 'Severe';
  if (value >= 200) return 'Poor';
  if (value >= 150) return 'Moderate';
  return 'Acceptable';
}

function aqiBadgeClass(value: number): string {
  if (value >= 300) return 'bg-red-50 text-red-700 border-red-200';
  if (value >= 200) return 'bg-orange-50 text-orange-700 border-orange-200';
  if (value >= 150) return 'bg-amber-50 text-amber-700 border-amber-200';
  return 'bg-emerald-50 text-emerald-700 border-emerald-200';
}

function heatColor(value: number): string {
  if (value >= 300) return '#DC2626';
  if (value >= 200) return '#EA580C';
  if (value >= 150) return '#D97706';
  return '#16A34A';
}
