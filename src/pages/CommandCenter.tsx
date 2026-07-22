import React, { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import L from 'leaflet';
import { MapContainer, TileLayer, Marker, Popup, Circle, useMap } from 'react-leaflet';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';


function MapFlyTo({ center, zoom }: { center: [number, number] | null; zoom?: number }) {
  const map = useMap();
  useEffect(() => {
    if (center && Number.isFinite(center[0]) && Number.isFinite(center[1])) {
      map.flyTo(center, zoom || 11, { animate: true, duration: 1.8 });
    }
  }, [center, zoom, map]);
  return null;
}



import { AlertTriangle, WifiOff, Wind, ShieldAlert, ArrowUpRight, Layers, Filter, RefreshCw, Download, FileText, X, Check } from 'lucide-react';

import { mockDashboardMetrics, mockStations, mockWards, mockTrendData, mockHotspots } from '../mock/data';

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
  station_code?: string;
  current_aqi?: number;
  aqi?: number;
  severity?: string;
  summary?: string;
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

const STATION_COORDINATES: Record<string, [number, number]> = {
  // Bengaluru Metros
  'BLR-PEE-AQ': [13.0285, 77.5186],
  'BLR-W-003': [13.0285, 77.5186],
  'HS-BLR-001': [13.0285, 77.5186],
  'BLR-CBD-AQ': [12.9716, 77.5946],
  'BLR-W-001': [12.9716, 77.5946],
  'BLR-IND-AQ': [12.9784, 77.6408],
  'BLR-W-002': [12.9784, 77.6408],
  'BLR-WHT-AQ': [12.9698, 77.7500],
  'BLR-W-005': [12.9698, 77.7500],

  // Delhi NCR Metros
  'ST-01': [28.6469, 77.3160],
  'W-04': [28.6469, 77.3160],
  'HS-802': [28.6469, 77.3160],
  'ST-05': [28.5308, 77.2713],
  'W-17': [28.5308, 77.2713],
  'HS-801': [28.5308, 77.2713],
  'ST-03': [28.6683, 77.1260],
  'W-12': [28.6683, 77.1260],
  'HS-803': [28.6683, 77.1260],
  'ST-02': [28.5644, 77.1726],
  'W-22': [28.5644, 77.1726],
  'ST-04': [28.6341, 77.1983],
  'W-09': [28.6341, 77.1983],
  'HS-804': [28.6341, 77.1983],
  'ST-06': [28.6289, 77.2415],
  'ST-07': [28.5708, 77.0715],

  // Mumbai MMR
  'BOM-NAV-AQ': [19.1412, 73.0089],
  'BOM-W-09': [19.1412, 73.0089],
  'HS-807': [19.1412, 73.0089],
  'BOM-BKC-AQ': [19.0600, 72.8683],
  'BOM-COL-AQ': [18.9067, 72.8147],

  // Kolkata Metro
  'CCU-BAL-AQ': [22.5280, 88.3659],
  'CCU-W-02': [22.5280, 88.3659],
  'HS-808': [22.5280, 88.3659],
  'CCU-VIC-AQ': [22.5448, 88.3426],

  // Chennai Metro
  'MAA-MAN-AQ': [13.1667, 80.2667],
  'MAA-W-01': [13.1667, 80.2667],
  'HS-MAA-001': [13.1667, 80.2667],
  'MAA-ALA-AQ': [13.0012, 80.2012],


  // Hyderabad Metro
  'HYD-ZOO-AQ': [17.3489, 78.4514],
  'HYD-SAN-AQ': [17.4578, 78.4412],

  // Lucknow / UP
  'LKO-TAL-AQ': [26.8389, 80.8926],
  'LKO-W-04': [26.8389, 80.8926],
  'HS-805': [26.8389, 80.8926],

  // Gujarat
  'AMD-MAN-AQ': [22.9972, 72.6008],
  'AMD-W-12': [22.9972, 72.6008],
  'HS-806': [22.9972, 72.6008],
};



function createStationPinIcon(aqi: number, status: string) {
  let color = '#64748B';
  let label = 'OFFLINE';

  if (status === 'ONLINE') {
    color = heatColor(aqi);
    label = aqi > 0 ? `${Math.round(aqi)} AQI` : 'ONLINE';
  } else if (status === 'DEGRADED') {
    color = '#D97706';
    label = aqi > 0 ? `${Math.round(aqi)} AQI` : 'DEGRADED';
  } else {
    color = '#64748B';
    label = 'OFFLINE';
  }

  return L.divIcon({
    className: 'custom-station-pin',
    html: `<div style="background-color: ${color}; color: white; font-weight: 700; font-size: 11px; padding: 4px 8px; border-radius: 12px; border: 2px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3); display: flex; align-items: center; gap: 4px; white-space: nowrap;">
      <span style="width: 7px; height: 7px; border-radius: 50%; background-color: white; display: inline-block;"></span>
      ${label}
    </div>`,
    iconSize: [80, 26],
    iconAnchor: [40, 13],
  });
}


function createHotspotPinIcon(aqi: number) {
  return L.divIcon({
    className: 'custom-hotspot-pin',
    html: `<div style="background-color: #DC2626; color: white; font-weight: 800; font-size: 11px; padding: 5px 10px; border-radius: 14px; border: 2px solid white; box-shadow: 0 0 12px rgba(220,38,38,0.8); display: flex; align-items: center; gap: 5px; white-space: nowrap;">
      <span style="font-size: 12px;">🔥</span> HOTSPOT ${Math.round(aqi)} AQI
    </div>`,
    iconSize: [110, 28],
    iconAnchor: [55, 14],
  });
}


export const CommandCenter: React.FC = () => {
  const [dashboard, setDashboard] = useState<DashboardState>(() => createFallbackDashboard());
  const [animatedAQI, setAnimatedAQI] = useState(0);
  const [selectedStation, setSelectedStation] = useState<ApiStationReading | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [layers, setLayers] = useState({ heat: true, stations: true, hotspots: true });

  const [searchParams] = useSearchParams();
  const [isFilterModalOpen, setIsFilterModalOpen] = useState(false);
  const [isExportModalOpen, setIsExportModalOpen] = useState(false);
  const [selectedSeverityFilter, setSelectedSeverityFilter] = useState<'ALL' | 'SEVERE' | 'POOR' | 'MODERATE'>('ALL');
  const [selectedWardId, setSelectedWardId] = useState<string | null>(null);

  const handleSelectWard = (ward: Ward) => {
    setSelectedWardId(ward.id);
    const known = STATION_COORDINATES[ward.id];
    const matchStation = dashboard.apiStations.find(
      (s) => s.ward_code === ward.id || s.station_code === ward.id
    );
    if (matchStation) {
      setSelectedStation(matchStation);
    } else if (known) {
      setSelectedStation({
        station_code: ward.id,
        station_name: ward.name,
        latitude: known[0],
        longitude: known[1],
        ward_code: ward.id,
        readings: [
          { pollutant: 'AQI', value: ward.aqi, unit: 'index' },
          { pollutant: 'PM25', value: Math.round(ward.aqi * 0.58), unit: 'ug/m3' },
          { pollutant: 'PM10', value: Math.round(ward.aqi * 0.88), unit: 'ug/m3' },
          { pollutant: 'NO2', value: Math.round(ward.aqi * 0.22), unit: 'ug/m3' },
        ],
      });
    }
  };


  const filteredWards = useMemo(() => {
    if (selectedSeverityFilter === 'ALL') return dashboard.wards;
    if (selectedSeverityFilter === 'SEVERE') return dashboard.wards.filter((w) => w.aqi >= 300);
    if (selectedSeverityFilter === 'POOR') return dashboard.wards.filter((w) => w.aqi >= 200 && w.aqi < 300);
    return dashboard.wards.filter((w) => w.aqi < 200);
  }, [dashboard.wards, selectedSeverityFilter]);

  const filteredStations = useMemo(() => {
    let list = dashboard.stations;
    if (selectedSeverityFilter === 'SEVERE') list = list.filter((s) => s.aqi >= 300);
    else if (selectedSeverityFilter === 'POOR') list = list.filter((s) => s.aqi >= 200 && s.aqi < 300);
    else if (selectedSeverityFilter === 'MODERATE') list = list.filter((s) => s.aqi < 200);

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      list = list.filter((s) => s.id.toLowerCase().includes(q) || s.name.toLowerCase().includes(q));
    }
    return list;
  }, [dashboard.stations, selectedSeverityFilter, searchQuery]);


  const handleExportCSV = () => {
    const headers = ['Station_Code', 'Station_Name', 'AQI_Level', 'Status', 'Latitude', 'Longitude'];
    const rows = dashboard.stations.map((s) => [s.id, `"${s.name}"`, s.aqi, s.status, s.lat, s.lng]);
    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map((e) => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `AeroIntel_Pollution_Audit_Report_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  useEffect(() => {
    const q = searchParams.get('search');
    if (q) {
      setSearchQuery(q);
    }
  }, [searchParams]);


  useEffect(() => {
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      const match = dashboard.apiStations.find(
        (s) => s.station_code.toLowerCase().includes(q) || s.station_name.toLowerCase().includes(q)
      );
      if (match) {
        setSelectedStation(match);
      }
    }
  }, [searchQuery, dashboard.apiStations]);



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

  const regionParam = searchParams.get('region');

  const regionTarget = useMemo<{ coords: [number, number]; zoom: number } | null>(() => {
    if (regionParam === 'INDIA') return { coords: [21.7679, 78.8718], zoom: 5 };
    if (regionParam === 'NCR') return { coords: [28.6139, 77.2090], zoom: 11 };
    if (regionParam === 'BLR') return { coords: [12.9716, 77.5946], zoom: 11 };
    if (regionParam === 'BOM') return { coords: [19.0760, 72.8777], zoom: 11 };
    if (regionParam === 'CCU') return { coords: [22.5726, 88.3639], zoom: 11 };
    if (regionParam === 'MAA') return { coords: [13.0827, 80.2707], zoom: 11 };
    if (regionParam === 'HYD') return { coords: [17.3850, 78.4867], zoom: 11 };
    return null;
  }, [regionParam]);

  const defaultHotspotCenter = useMemo<[number, number]>(() => {
    if (dashboard.hotspots.length > 0) {
      const topHotspot = dashboard.hotspots[0];
      const wardCode = topHotspot.ward_code || '';
      const known = STATION_COORDINATES[wardCode] || (topHotspot.station_code ? STATION_COORDINATES[topHotspot.station_code] : undefined);
      if (known) return known;
    }
    if (dashboard.stations.length > 0) {
      const sorted = [...dashboard.stations].sort((a, b) => b.aqi - a.aqi);
      if (sorted[0]?.lat && sorted[0]?.lng) {
        return [sorted[0].lat, sorted[0].lng];
      }
    }
    return [13.0285, 77.5186];
  }, [dashboard.hotspots, dashboard.stations]);

  const flyTargetCoords = useMemo<[number, number] | null>(() => {
    if (selectedStation) {
      const known = STATION_COORDINATES[selectedStation.station_code] || (selectedStation.ward_code ? STATION_COORDINATES[selectedStation.ward_code] : undefined);
      if (known) return known;
      if (Number.isFinite(selectedStation.latitude) && Number.isFinite(selectedStation.longitude)) {
        return [selectedStation.latitude, selectedStation.longitude];
      }
    }
    if (searchQuery.trim() && filteredStations.length > 0) {
      return [filteredStations[0].lat, filteredStations[0].lng];
    }
    if (regionTarget) return regionTarget.coords;
    return defaultHotspotCenter;
  }, [selectedStation, searchQuery, filteredStations, regionTarget, defaultHotspotCenter]);

  const flyZoom = useMemo(() => {
    if (selectedStation || searchQuery.trim()) return 13;
    if (regionTarget) return regionTarget.zoom;
    return 11;
  }, [selectedStation, searchQuery, regionTarget]);

  const mapCenter: [number, number] = regionTarget ? regionTarget.coords : defaultHotspotCenter;




  return (
    <div className="px-8 py-6 space-y-8 max-w-7xl mx-auto">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 pb-4 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 mb-1">Executive Air Quality Dashboard</h1>
          <p className="text-sm font-medium text-slate-500">Real-time geospatial monitoring and multi-agency response metrics</p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <input
            type="text"
            placeholder="Search Station (e.g. BLR-IND-AQ, Peenya)..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-64 px-3 py-1.5 text-xs rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white shadow-sm"
          />
          <span className={`inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-semibold ${dashboard.usingFallback ? 'border-amber-200 bg-amber-50 text-amber-700' : 'border-emerald-200 bg-emerald-50 text-emerald-700'}`}>
            <RefreshCw className="h-3.5 w-3.5" />
            {dashboard.usingFallback ? 'Seeded standby data' : 'Live backend data'}
          </span>
          <button onClick={() => setIsFilterModalOpen(true)} className="ui-button-secondary">
            <Filter className="h-4 w-4 text-slate-500" />
            <span>Filter Wards</span>
          </button>
          <button onClick={() => setIsExportModalOpen(true)} className="ui-button-primary">
            <Download className="h-4 w-4" />
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
              <MapFlyTo center={flyTargetCoords} zoom={flyZoom} />

              <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              />

              {filteredStations.map((station) => {

                if (!Number.isFinite(station?.lat) || !Number.isFinite(station?.lng)) return null;
                const health = stationHealthByCode.get(station.id);

                const unhealthy = station.status !== 'ONLINE' || health?.is_reliable === false;
                return (
                  <React.Fragment key={station.id}>
                    {layers.stations && (
                      <Marker
                        position={[station.lat, station.lng]}
                        icon={createStationPinIcon(station.aqi, station.status)}

                        eventHandlers={{ click: () => setSelectedStation(findApiStation(dashboard.apiStations, station)) }}
                      >
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
                const wardCode = hotspot.ward_code || '';
                const known = STATION_COORDINATES[wardCode] || (hotspot.station_code ? STATION_COORDINATES[hotspot.station_code] : undefined);
                const fallbackStation = dashboard.stations.find((item) => item.id === wardCode || item.name.includes(wardCode)) || dashboard.stations[index % dashboard.stations.length];
                const lat = known ? known[0] : (fallbackStation?.lat ?? 13.0285);
                const lng = known ? known[1] : (fallbackStation?.lng ?? 77.5186);
                const aqiVal = Math.round(hotspot.current_aqi || hotspot.aqi || 315);

                if (!Number.isFinite(lat) || !Number.isFinite(lng)) return null;

                return (
                  <React.Fragment key={hotspot.hotspot_uid || hotspot.hotspot_id || hotspot.id || index}>
                    <Marker position={[lat, lng]} icon={createHotspotPinIcon(aqiVal)}>
                      <Popup>
                        <div className="p-2 text-xs space-y-1">
                          <div className="text-red-700 font-bold text-sm flex items-center gap-1">
                            <span>🚨 ACTIVE CRITICAL HOTSPOT</span>
                          </div>
                          <div><strong>Ward / Location:</strong> {wardCode || hotspot.ward_code || hotspot.station_code || 'Monitored Zone'}</div>
                          <div><strong>AQI Reading:</strong> <span className="font-bold text-red-600">{aqiVal} AQI</span></div>
                          <p className="text-slate-600 text-xs mt-1">{hotspot.summary || `Severe particulate emission surge detected in ${wardCode || 'monitored zone'}.`}</p>

                        </div>
                      </Popup>
                    </Marker>
                    <Circle
                      center={[lat, lng]}
                      radius={1800}
                      pathOptions={{ color: '#DC2626', fillColor: '#EF4444', fillOpacity: 0.35, weight: 2.5 }}
                    />
                  </React.Fragment>
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
            <div className="flex justify-between items-center mb-4">
              <div>
                <h2 className="text-sm font-semibold text-slate-900">Highest Pollution Wards</h2>
                <p className="text-[11px] text-slate-400">Scroll to view all {filteredWards.length} wards</p>
              </div>
              {selectedSeverityFilter !== 'ALL' && (
                <span className="text-[10px] font-bold text-blue-600 bg-blue-50 border border-blue-200 px-2 py-0.5 rounded-full">
                  {selectedSeverityFilter} Filter Active
                </span>
              )}
            </div>
            <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
              {filteredWards.length > 0 ? (
                filteredWards.map((ward) => (
                  <div
                    key={ward.id}
                    onClick={() => handleSelectWard(ward)}
                    className={`flex justify-between items-center p-3 rounded-xl border text-xs cursor-pointer transition-all ${
                      selectedWardId === ward.id
                        ? 'bg-blue-50 border-blue-500 shadow-md ring-2 ring-blue-500/20'
                        : 'bg-slate-50 hover:bg-blue-50/60 border-slate-200'
                    }`}
                  >
                    <span className="text-slate-700 font-semibold truncate max-w-[200px]" title={ward.name}>
                      {ward.name}
                    </span>
                    <span className={`px-2.5 py-1 rounded-md font-semibold shrink-0 ${
                      ward.aqi >= 300
                        ? 'bg-red-50 text-red-700 border border-red-200'
                        : ward.aqi >= 200
                        ? 'bg-amber-50 text-amber-800 border border-amber-200'
                        : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                    }`}>
                      {ward.aqi} AQI
                    </span>
                  </div>

                ))
              ) : (
                <div className="p-4 text-center text-xs text-slate-400 bg-slate-50 rounded-xl border border-slate-200">
                  No wards match current severity filter
                </div>
              )}
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

      {/* Filter Wards Modal */}

      {isFilterModalOpen && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-5 border border-slate-200">
            <div className="flex justify-between items-center pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <Filter className="h-5 w-5 text-blue-600" />
                <h3 className="text-base font-bold text-slate-900">Filter Municipal Wards</h3>
              </div>
              <button onClick={() => setIsFilterModalOpen(false)} className="text-slate-400 hover:text-slate-600 p-1 rounded-lg">
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="space-y-4 text-xs">
              <div>
                <label className="font-semibold text-slate-700 block mb-2 uppercase tracking-wider text-[11px]">Severity Risk Threshold</label>
                <div className="grid grid-cols-2 gap-2">
                  {(['ALL', 'SEVERE', 'POOR', 'MODERATE'] as const).map((sev) => (
                    <button
                      key={sev}
                      onClick={() => setSelectedSeverityFilter(sev)}
                      className={`p-2.5 rounded-xl border text-center font-semibold transition-all ${
                        selectedSeverityFilter === sev
                          ? 'bg-blue-600 text-white border-blue-600 shadow-sm'
                          : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
                      }`}
                    >
                      {sev === 'ALL' ? 'All Wards' : sev}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="flex gap-3 pt-2">
              <button onClick={() => setIsFilterModalOpen(false)} className="ui-button-primary w-full py-2.5">
                <Check className="h-4 w-4" />
                <span>Apply Filter</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Export Executive Audit Report Modal */}
      {isExportModalOpen && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-xl w-full p-6 shadow-2xl space-y-5 border border-slate-200">
            <div className="flex justify-between items-center pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-blue-600" />
                <h3 className="text-base font-bold text-slate-900">Executive Air Quality Audit Report</h3>
              </div>
              <button onClick={() => setIsExportModalOpen(false)} className="text-slate-400 hover:text-slate-600 p-1 rounded-lg">
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="space-y-3 text-xs bg-slate-50 p-4 rounded-xl border border-slate-200 font-mono">
              <div className="flex justify-between">
                <span className="text-slate-500">Report Date:</span>
                <span className="font-semibold text-slate-900">{new Date().toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Monitored City Average AQI:</span>
                <span className="font-bold text-blue-600">{dashboard.metrics.cityAQI} AQI</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Active Hotspots Flagged:</span>
                <span className="font-bold text-red-600">{dashboard.metrics.activeHotspots} Emergency Zones</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Worst Impacted Ward:</span>
                <span className="font-bold text-slate-900">{dashboard.metrics.worstWard}</span>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row gap-3 pt-2">
              <button onClick={handleExportCSV} className="ui-button-primary flex-1 py-2.5">
                <Download className="h-4 w-4" />
                <span>Download CSV Audit Log</span>
              </button>
              <button onClick={() => window.print()} className="ui-button-secondary flex-1 py-2.5">
                <span>Print / Save PDF</span>
              </button>
            </div>
          </div>
        </div>
      )}
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
  const wards = mockWards;

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
    hotspots: mockHotspots.map((h, idx) => ({
      id: idx + 1,
      hotspot_id: h.id,
      hotspot_uid: h.id,
      ward_code: h.ward,
      station_code: h.id === 'HS-801' ? 'ST-05' : h.id === 'HS-802' ? 'ST-01' : 'ST-03',
      current_aqi: h.aqi,
      severity: h.severity,
      summary: `High particulate emission surge detected in ${h.ward}.`,

    })),

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
  
  const known = STATION_COORDINATES[station.station_code] || (station.ward_code ? STATION_COORDINATES[station.ward_code] : undefined);
  const mockMatch = mockStations.find((item) => item.id === station.station_code || item.name === station.station_name);
  const lat = Number.isFinite(station.latitude) ? station.latitude : (known ? known[0] : (mockMatch?.lat ?? 12.9716));
  const lng = Number.isFinite(station.longitude) ? station.longitude : (known ? known[1] : (mockMatch?.lng ?? 77.5946));

  return {
    id: station.station_code,
    name: station.station_name || station.station_code,
    lat,
    lng,
    aqi: extractAqi(station),
    status: status === 'OFFLINE' ? 'OFFLINE' : status === 'ONLINE' ? 'ONLINE' : 'DEGRADED',
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
