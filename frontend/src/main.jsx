import React, { useEffect, useMemo, useState } from 'react'
import { createRoot } from 'react-dom/client'
import './styles.css'

const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
const refreshMs = 60000
const cityBounds = {
  minLatitude: 12.84,
  maxLatitude: 13.08,
  minLongitude: 77.48,
  maxLongitude: 77.74,
}

const demoDashboard = {
  generated_at: '2025-01-15T12:00:00Z',
  city_average_aqi: 184,
  worst_affected_ward: {
    ward_code: 'BLR-W-014',
    average_aqi: 238,
    station_count: 3,
    band: 'Poor',
    severity_rank: 4,
    display_label: 'Poor',
    health_severity_category: 'High respiratory concern',
  },
  active_hotspot_count: 3,
  offline_or_degraded_station_count: 2,
  latest_reliable_station_readings: [
    station('BLR-CBD-AQ', 'Central Business District', 'BLR-W-010', 12.975, 77.603, 182, 'valid', { pm25: 76, pm10: 118, no2: 42, so2: 11, co: 0.9, o3: 28 }),
    station('BLR-SB-AQ', 'Silk Board Junction', 'BLR-W-014', 12.917, 77.623, 238, 'valid', { pm25: 112, pm10: 188, no2: 74, so2: 14, co: 1.4, o3: 24 }),
    station('BLR-PEENYA-AQ', 'Peenya Industrial Estate', 'BLR-W-022', 13.028, 77.519, 216, 'suspect', { pm25: 91, pm10: 146, no2: 61, so2: 27, co: 1.1, o3: 21 }),
    station('BLR-JAYANAGAR-AQ', 'Jayanagar', 'BLR-W-006', 12.925, 77.593, 142, 'valid', { pm25: 54, pm10: 82, no2: 29, so2: 8, co: 0.5, o3: 36 }),
    station('BLR-WF-AQ', 'Whitefield Tech Park', 'BLR-W-031', 12.969, 77.749, 168, 'valid', { pm25: 64, pm10: 95, no2: 38, so2: 10, co: 0.7, o3: 33 }),
  ],
  weather_summary: {
    location_code: 'BLR-CENTRE',
    city: 'Bengaluru',
    observed_at: '2025-01-15T12:00:00Z',
    temperature_c: 28.4,
    relative_humidity_pct: 52,
    data_quality_status: 'valid',
  },
  wind_information: {
    location_code: 'BLR-CENTRE',
    city: 'Bengaluru',
    observed_at: '2025-01-15T12:00:00Z',
    wind_speed_kmh: 16,
    wind_direction_degrees: 315,
    data_quality_status: 'valid',
  },
  current_hotspot_summaries: [
    { hotspot_id: '101', ward_code: 'BLR-W-014', severity: 'high', aqi: 238, detected_at: '2025-01-15T11:45:00Z', summary: 'Silk Board corridor showing traffic-aligned PM and NO2 pressure.' },
    { hotspot_id: '102', ward_code: 'BLR-W-022', severity: 'medium', aqi: 216, detected_at: '2025-01-15T11:30:00Z', summary: 'Peenya plume requires industrial evidence review.' },
    { hotspot_id: '103', ward_code: 'BLR-W-010', severity: 'medium', aqi: 182, detected_at: '2025-01-15T11:55:00Z', summary: 'CBD build-up near arterial roads.' },
  ],
  city_pollution_trend: [
    { observed_at: '2025-01-15T06:00:00Z', average_aqi: 126 },
    { observed_at: '2025-01-15T08:00:00Z', average_aqi: 151 },
    { observed_at: '2025-01-15T10:00:00Z', average_aqi: 176 },
    { observed_at: '2025-01-15T12:00:00Z', average_aqi: 184 },
    { observed_at: '2025-01-15T14:00:00Z', average_aqi: 171 },
    { observed_at: '2025-01-15T16:00:00Z', average_aqi: 193 },
  ],
}

const demoHealth = [
  health('BLR-CBD-AQ', 'Central Business District', 'ONLINE', 0.94),
  health('BLR-SB-AQ', 'Silk Board Junction', 'ONLINE', 0.91),
  health('BLR-PEENYA-AQ', 'Peenya Industrial Estate', 'DEGRADED', 0.62, ['SO2 drift requires calibration']),
  health('BLR-JAYANAGAR-AQ', 'Jayanagar', 'ONLINE', 0.97),
  health('BLR-WF-AQ', 'Whitefield Tech Park', 'DELAYED', 0.72, ['Last packet delayed']),
]

const demoWardSummaries = [
  demoDashboard.worst_affected_ward,
  { ward_code: 'BLR-W-022', average_aqi: 216, station_count: 2, band: 'Poor', severity_rank: 4, display_label: 'Poor', health_severity_category: 'High concern' },
  { ward_code: 'BLR-W-010', average_aqi: 182, station_count: 2, band: 'Moderate', severity_rank: 3, display_label: 'Moderate', health_severity_category: 'Sensitive groups affected' },
  { ward_code: 'BLR-W-031', average_aqi: 168, station_count: 1, band: 'Moderate', severity_rank: 3, display_label: 'Moderate', health_severity_category: 'Monitor trend' },
]

const demoHeatmap = {
  type: 'FeatureCollection',
  features: demoDashboard.latest_reliable_station_readings.map((item) => ({
    type: 'Feature',
    properties: { aqi: extractAqi(item), station_code: item.station_code },
    geometry: { type: 'Point', coordinates: [item.longitude, item.latitude] },
  })),
}

const demoWards = [
  { code: 'BLR-W-014', label: 'Silk Board', points: [[24, 61], [45, 55], [54, 70], [36, 82], [20, 75]] },
  { code: 'BLR-W-010', label: 'CBD', points: [[42, 34], [62, 30], [69, 47], [52, 57], [37, 48]] },
  { code: 'BLR-W-022', label: 'Peenya', points: [[10, 12], [34, 11], [39, 29], [25, 43], [8, 33]] },
  { code: 'BLR-W-006', label: 'Jayanagar', points: [[38, 67], [58, 58], [74, 70], [64, 88], [43, 86]] },
  { code: 'BLR-W-031', label: 'Whitefield', points: [[70, 31], [93, 34], [92, 61], [73, 57], [65, 43]] },
]

function station(station_code, station_name, ward_code, latitude, longitude, aqi, data_quality_status, pollutants) {
  return {
    station_code,
    station_name,
    ward_code,
    latitude,
    longitude,
    observed_at: '2025-01-15T12:00:00Z',
    data_quality_status,
    readings: [
      { pollutant: 'AQI', value: aqi, unit: 'index', data_quality_status },
      ...Object.entries(pollutants).map(([pollutant, value]) => ({ pollutant: pollutant.toUpperCase(), value, unit: pollutant === 'co' ? 'mg/m3' : 'ug/m3', data_quality_status })),
    ],
  }
}

function health(station_code, station_name, status, score, reasons = []) {
  return {
    station_code,
    station_name,
    status,
    data_quality_score: score,
    evaluated_at: '2025-01-15T12:00:00Z',
    reasons,
    is_reliable: status === 'ONLINE' && score >= 0.75,
  }
}

function App() {
  const [dashboard, setDashboard] = useState(null)
  const [heatmap, setHeatmap] = useState(null)
  const [wards, setWards] = useState([])
  const [healthSnapshots, setHealthSnapshots] = useState([])
  const [hotspots, setHotspots] = useState([])
  const [selectedStation, setSelectedStation] = useState(null)
  const [selectedHotspot, setSelectedHotspot] = useState(null)
  const [layers, setLayers] = useState({ heatmap: true, stations: true, hotspots: true, wards: true, wind: true })
  const [status, setStatus] = useState({ loading: true, error: '', demo: false, refreshedAt: null })

  useEffect(() => {
    let alive = true
    const load = async () => {
      setStatus((current) => ({ ...current, loading: true, error: '' }))
      try {
        const next = await fetchCommandCenterData()
        if (!alive) return
        setDashboard(next.dashboard)
        setHeatmap(next.heatmap)
        setWards(next.wards)
        setHealthSnapshots(next.health)
        setHotspots(next.hotspots)
        setStatus({ loading: false, error: '', demo: false, refreshedAt: new Date() })
      } catch (error) {
        if (!alive) return
        setDashboard(demoDashboard)
        setHeatmap(demoHeatmap)
        setWards(demoWardSummaries)
        setHealthSnapshots(demoHealth)
        setHotspots(demoDashboard.current_hotspot_summaries)
        setStatus({ loading: false, error: error.message, demo: true, refreshedAt: new Date() })
      }
    }
    load()
    const timer = window.setInterval(load, refreshMs)
    return () => {
      alive = false
      window.clearInterval(timer)
    }
  }, [])

  const stations = useMemo(() => mergeStationHealth(dashboard?.latest_reliable_station_readings || [], healthSnapshots), [dashboard, healthSnapshots])
  const wardList = wards.length ? wards : demoWardSummaries
  const hotspotList = hotspots.length ? hotspots : dashboard?.current_hotspot_summaries || []
  const worstWards = [...wardList].sort((a, b) => (b.average_aqi || 0) - (a.average_aqi || 0)).slice(0, 5)

  if (!dashboard && status.loading) {
    return <Shell><LoadingState /></Shell>
  }

  return (
    <Shell>
      <section className="hero-band">
        <div>
          <p className="eyebrow">AeroIntel</p>
          <h1>Urban Air Quality Command Center</h1>
          <p className="hero-copy">A live operational view of city AQI, sensors, hotspots, wind and investigation readiness.</p>
        </div>
        <div className="refresh-panel" aria-live="polite">
          <span className={status.demo ? 'status-dot warning' : 'status-dot'} />
          <div>
            <strong>{status.demo ? 'Demo standby data' : 'Live city state'}</strong>
            <span>Updated {formatTime(status.refreshedAt || dashboard.generated_at)}</span>
          </div>
        </div>
      </section>

      {status.demo && <Notice title="Live backend unavailable" message={`${status.error}. Showing seeded command-center data so the workspace remains explorable.`} />}
      {!status.demo && !stations.length && <Notice title="No station readings yet" message="The dashboard API returned no reliable station readings for the current city window." />}

      <section className="kpi-grid" aria-label="City health indicators">
        <KpiCard label="City average AQI" value={formatNumber(dashboard.city_average_aqi)} detail={aqiLabel(dashboard.city_average_aqi)} tone={aqiTone(dashboard.city_average_aqi)} />
        <KpiCard label="Worst ward" value={dashboard.worst_affected_ward?.ward_code || 'None'} detail={dashboard.worst_affected_ward ? `${Math.round(dashboard.worst_affected_ward.average_aqi)} AQI / ${dashboard.worst_affected_ward.display_label}` : 'No active ward summary'} />
        <KpiCard label="Active hotspots" value={dashboard.active_hotspot_count ?? hotspotList.length} detail="Linked to investigation workflow" />
        <KpiCard label="Sensor exceptions" value={dashboard.offline_or_degraded_station_count ?? healthSnapshots.filter((item) => ['OFFLINE', 'DEGRADED'].includes(item.status)).length} detail="Offline or degraded stations" tone="warning" />
      </section>

      <section className="command-grid">
        <article className="map-tile" aria-label="Interactive city air quality map">
          <div className="section-heading map-heading">
            <div>
              <p className="eyebrow">Spatial Operations</p>
              <h2>Bengaluru live air picture</h2>
            </div>
            <LayerToggle layers={layers} setLayers={setLayers} />
          </div>
          <CityMap
            stations={stations}
            hotspots={hotspotList}
            heatmap={heatmap}
            layers={layers}
            wind={dashboard.wind_information}
            selectedStation={selectedStation}
            setSelectedStation={setSelectedStation}
            setSelectedHotspot={setSelectedHotspot}
          />
          <MapLegend />
        </article>

        <aside className="side-stack">
          <WeatherWidget weather={dashboard.weather_summary} wind={dashboard.wind_information} />
          <SensorHealthPanel health={healthSnapshots} stations={stations} />
          <SelectedStationPanel station={selectedStation} />
        </aside>
      </section>

      <section className="insight-grid">
        <WorstWards wards={worstWards} />
        <TrendPanel trend={dashboard.city_pollution_trend || []} />
        <HotspotPanel hotspots={hotspotList} selectedHotspot={selectedHotspot} setSelectedHotspot={setSelectedHotspot} />
      </section>
    </Shell>
  )
}

function Shell({ children }) {
  return (
    <main className="app-shell">
      <nav className="global-nav" aria-label="Global navigation">
        <span className="brand-mark">AeroIntel</span>
        <span>Command Center</span>
        <span>Investigations</span>
        <span>Evidence</span>
      </nav>
      <div className="sub-nav">
        <strong>City operations</strong>
        <a href="#map">Map</a>
        <a href="#wards">Wards</a>
        <a href="#trend">Trend</a>
        <button type="button">Live</button>
      </div>
      {children}
    </main>
  )
}

function LoadingState() {
  return (
    <section className="loading-state" aria-live="polite">
      <div className="loading-pulse" />
      <h1>Loading city state</h1>
      <p>Connecting to AeroIntel services and preparing the command map.</p>
    </section>
  )
}

function Notice({ title, message }) {
  return (
    <section className="notice" role="status">
      <strong>{title}</strong>
      <span>{message}</span>
    </section>
  )
}

function KpiCard({ label, value, detail, tone = 'neutral' }) {
  return (
    <article className={`kpi-card ${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      <p>{detail}</p>
    </article>
  )
}

function LayerToggle({ layers, setLayers }) {
  return (
    <div className="layer-toggle" aria-label="Map layers">
      {Object.keys(layers).map((key) => (
        <button
          key={key}
          type="button"
          aria-pressed={layers[key]}
          onClick={() => setLayers((current) => ({ ...current, [key]: !current[key] }))}
        >
          {key}
        </button>
      ))}
    </div>
  )
}

function CityMap({ stations, hotspots, heatmap, layers, wind, selectedStation, setSelectedStation, setSelectedHotspot }) {
  const heatPoints = heatmapPoints(heatmap, stations)
  return (
    <div id="map" className="city-map">
      <svg viewBox="0 0 100 100" role="img" aria-label="Bengaluru AQI heatmap with station, ward and hotspot markers">
        <rect width="100" height="100" rx="0" className="map-canvas" />
        <path className="arterial" d="M5 75 C24 62 37 63 54 49 C66 39 78 33 96 28" />
        <path className="arterial secondary" d="M16 12 C28 28 42 36 55 54 C65 68 75 78 91 88" />
        {layers.wards && demoWards.map((ward) => <WardShape key={ward.code} ward={ward} />)}
        {layers.heatmap && heatPoints.map((point, index) => <HeatPoint key={`${point.x}-${point.y}-${index}`} point={point} />)}
        {layers.wind && <WindLayer wind={wind} />}
        {layers.stations && stations.map((item) => (
          <StationMarker key={item.station_code} station={item} selected={selectedStation?.station_code === item.station_code} onClick={setSelectedStation} />
        ))}
        {layers.hotspots && hotspots.map((item, index) => <HotspotMarker key={item.hotspot_id || index} hotspot={item} index={index} onClick={setSelectedHotspot} />)}
      </svg>
    </div>
  )
}

function WardShape({ ward }) {
  return (
    <g>
      <polygon className="ward-shape" points={ward.points.map((point) => point.join(',')).join(' ')} />
      <text x={ward.points[0][0] + 5} y={ward.points[0][1] + 8} className="ward-label">{ward.label}</text>
    </g>
  )
}

function HeatPoint({ point }) {
  return <circle cx={point.x} cy={point.y} r={point.radius} className={`heat-point ${aqiTone(point.aqi)}`} />
}

function WindLayer({ wind }) {
  const angle = wind?.wind_direction_degrees || 315
  return (
    <g className="wind-layer" transform={`rotate(${angle} 84 18)`}>
      <path d="M76 18 L91 18" />
      <path d="M87 14 L91 18 L87 22" />
      <text x="63" y="11">Wind {Math.round(wind?.wind_speed_kmh || 0)} km/h</text>
    </g>
  )
}

function StationMarker({ station, selected, onClick }) {
  const point = latLngToPoint(station.latitude, station.longitude)
  const unhealthy = !station.isReliable
  return (
    <g className={`station-marker ${selected ? 'selected' : ''} ${unhealthy ? 'unhealthy' : ''}`} onClick={() => onClick(station)} tabIndex="0" role="button" aria-label={`${station.station_name} station, AQI ${extractAqi(station)}`} onKeyDown={(event) => event.key === 'Enter' && onClick(station)}>
      <circle cx={point.x} cy={point.y} r="2.8" />
      <circle cx={point.x} cy={point.y} r="5.2" />
    </g>
  )
}

function HotspotMarker({ hotspot, index, onClick }) {
  const stationMatch = demoDashboard.latest_reliable_station_readings.find((item) => item.ward_code === hotspot.ward_code)
  const point = stationMatch ? latLngToPoint(stationMatch.latitude, stationMatch.longitude) : { x: 32 + index * 19, y: 52 + index * 9 }
  return (
    <g className={`hotspot-marker ${hotspot.severity || 'medium'}`} onClick={() => onClick(hotspot)} tabIndex="0" role="button" aria-label={`Hotspot ${hotspot.hotspot_id}, AQI ${hotspot.aqi}`} onKeyDown={(event) => event.key === 'Enter' && onClick(hotspot)}>
      <circle cx={point.x + 2.8} cy={point.y - 2.4} r="4.4" />
      <text x={point.x + 2.8} y={point.y - 1.2}>!</text>
    </g>
  )
}

function MapLegend() {
  return (
    <div className="map-legend" aria-label="Map legend">
      <span><i className="legend heat" /> AQI heat</span>
      <span><i className="legend station" /> Reliable station</span>
      <span><i className="legend station bad" /> Unhealthy sensor</span>
      <span><i className="legend hotspot" /> Hotspot</span>
    </div>
  )
}

function WeatherWidget({ weather, wind }) {
  return (
    <article className="utility-card weather-card">
      <div className="section-heading compact">
        <div>
          <p className="eyebrow">Weather</p>
          <h2>{weather?.city || 'City'} now</h2>
        </div>
        <span>{weather?.data_quality_status || 'unknown'}</span>
      </div>
      <div className="weather-readout">
        <strong>{weather?.temperature_c != null ? `${Math.round(weather.temperature_c)} deg C` : 'No data'}</strong>
        <span>{weather?.relative_humidity_pct != null ? `${Math.round(weather.relative_humidity_pct)}% humidity` : 'Humidity unavailable'}</span>
      </div>
      <div className="wind-cardline">
        <span>Wind</span>
        <strong>{wind?.wind_speed_kmh != null ? `${Math.round(wind.wind_speed_kmh)} km/h` : 'No wind'}</strong>
        <span>{directionName(wind?.wind_direction_degrees)}</span>
      </div>
    </article>
  )
}

function SensorHealthPanel({ health, stations }) {
  const records = health.length ? health : stations
  return (
    <article className="utility-card">
      <div className="section-heading compact">
        <div>
          <p className="eyebrow">Sensors</p>
          <h2>Health indicators</h2>
        </div>
        <span>{records.length} stations</span>
      </div>
      <div className="sensor-list">
        {records.length ? records.slice(0, 5).map((item) => (
          <div className="sensor-row" key={item.station_code}>
            <span className={`health-light ${(item.status || item.healthStatus || '').toLowerCase()}`} />
            <div>
              <strong>{item.station_name}</strong>
              <span>{item.status || item.healthStatus || item.data_quality_status}</span>
            </div>
            <em>{Math.round((item.data_quality_score || item.dataQualityScore || 0) * 100)}%</em>
          </div>
        )) : <EmptyState label="No sensor-health records returned." />}
      </div>
    </article>
  )
}

function SelectedStationPanel({ station }) {
  return (
    <article className="utility-card station-detail">
      <div className="section-heading compact">
        <div>
          <p className="eyebrow">Station detail</p>
          <h2>{station ? station.station_name : 'Select a station'}</h2>
        </div>
      </div>
      {station ? (
        <>
          <div className="station-aqi"><strong>{extractAqi(station)}</strong><span>AQI / {station.ward_code}</span></div>
          <dl className="pollutant-grid">
            {station.readings.filter((item) => item.pollutant !== 'AQI').slice(0, 6).map((item) => (
              <div key={item.pollutant}>
                <dt>{item.pollutant}</dt>
                <dd>{Math.round(item.value)} <small>{item.unit}</small></dd>
              </div>
            ))}
          </dl>
          {!station.isReliable && <p className="station-warning">Sensor is marked unhealthy; downstream analytics can reduce or reject this observation.</p>}
        </>
      ) : <EmptyState label="No station selected." />}
    </article>
  )
}

function WorstWards({ wards }) {
  return (
    <article id="wards" className="utility-card span-4">
      <div className="section-heading compact">
        <div>
          <p className="eyebrow">Priority wards</p>
          <h2>Worst affected areas</h2>
        </div>
      </div>
      <div className="ward-list">
        {wards.length ? wards.map((ward) => (
          <div className="ward-row" key={ward.ward_code}>
            <strong>{ward.ward_code}</strong>
            <div className="ward-bar"><span style={{ width: `${Math.min(100, (ward.average_aqi || 0) / 3)}%` }} /></div>
            <span>{Math.round(ward.average_aqi || 0)} AQI</span>
            <em>{ward.display_label || ward.band}</em>
          </div>
        )) : <EmptyState label="No ward AQI summaries returned." />}
      </div>
    </article>
  )
}

function TrendPanel({ trend }) {
  const points = trend.length ? trend : []
  const max = Math.max(...points.map((item) => item.average_aqi), 1)
  const chartPoints = points.map((item, index) => {
    const x = points.length === 1 ? 50 : (index / (points.length - 1)) * 100
    const y = 100 - (item.average_aqi / max) * 82 - 8
    return `${x},${y}`
  }).join(' ')
  return (
    <article id="trend" className="utility-card span-4 trend-panel">
      <div className="section-heading compact">
        <div>
          <p className="eyebrow">City trend</p>
          <h2>Pollution trajectory</h2>
        </div>
      </div>
      {points.length ? (
        <svg viewBox="0 0 100 100" preserveAspectRatio="none" aria-label="City pollution trend chart">
          <polyline points={chartPoints} />
          {points.map((item, index) => {
            const [x, y] = chartPoints.split(' ')[index].split(',')
            return <circle key={item.observed_at} cx={x} cy={y} r="1.8" />
          })}
        </svg>
      ) : <EmptyState label="No city trend returned." />}
    </article>
  )
}

function HotspotPanel({ hotspots, selectedHotspot, setSelectedHotspot }) {
  return (
    <article className="utility-card span-4 hotspot-panel">
      <div className="section-heading compact">
        <div>
          <p className="eyebrow">Investigations</p>
          <h2>Current hotspots</h2>
        </div>
      </div>
      <div className="hotspot-list">
        {hotspots.length ? hotspots.map((hotspot) => (
          <button type="button" key={hotspot.hotspot_id} onClick={() => setSelectedHotspot(hotspot)} className={selectedHotspot?.hotspot_id === hotspot.hotspot_id ? 'active' : ''}>
            <span>{hotspot.ward_code || 'Unknown ward'}</span>
            <strong>{Math.round(hotspot.aqi)} AQI</strong>
            <em>{hotspot.severity}</em>
          </button>
        )) : <EmptyState label="No active hotspots returned." />}
      </div>
      {selectedHotspot && (
        <div className="investigation-workspace">
          <span>Investigation workspace</span>
          <strong>Hotspot {selectedHotspot.hotspot_id}</strong>
          <p>{selectedHotspot.summary || 'Ready for evidence review.'}</p>
          <a href={`${apiBase}/docs#/hotspots/get_hotspot_detail_api_v1_hotspots__hotspot_id__get`} target="_blank" rel="noreferrer">Open API workspace</a>
        </div>
      )}
    </article>
  )
}

function EmptyState({ label }) {
  return <p className="empty-state">{label}</p>
}

async function fetchCommandCenterData() {
  const bbox = `min_latitude=${cityBounds.minLatitude}&min_longitude=${cityBounds.minLongitude}&max_latitude=${cityBounds.maxLatitude}&max_longitude=${cityBounds.maxLongitude}`
  const dashboard = await fetchJson('/api/v1/command-center/dashboard')
  const [heatmap, wards, health, hotspots] = await Promise.all([
    fetchOptionalJson(`/api/v1/heatmap/current?${bbox}&grid_resolution=0.025`, demoHeatmap),
    fetchOptionalJson(`/api/v1/heatmap/wards?${bbox}`, demoWardSummaries),
    fetchOptionalJson('/api/v1/sensor-health/stations', demoHealth),
    fetchOptionalJson('/api/v1/hotspots?status=ACTIVE', dashboard.current_hotspot_summaries || []),
  ])
  return { dashboard, heatmap, wards, health, hotspots: normalizeHotspots(hotspots, dashboard.current_hotspot_summaries) }
}

async function fetchOptionalJson(path, fallback) {
  try {
    return await fetchJson(path)
  } catch {
    return fallback
  }
}

async function fetchJson(path) {
  const response = await fetch(`${apiBase}${path}`)
  if (!response.ok) {
    let detail = ''
    try {
      const payload = await response.json()
      detail = payload.detail ? `: ${payload.detail}` : ''
    } catch {
      detail = ''
    }
    throw new Error(`AeroIntel API returned ${response.status}${detail}`)
  }
  return response.json()
}

function mergeStationHealth(stations, health) {
  return stations.map((item) => {
    const fallback = demoDashboard.latest_reliable_station_readings.find((demo) => demo.station_code === item.station_code) || {}
    const snapshot = health.find((record) => record.station_code === item.station_code) || {}
    const status = snapshot.status || (item.data_quality_status === 'valid' ? 'ONLINE' : 'DEGRADED')
    return {
      ...fallback,
      ...item,
      latitude: item.latitude ?? fallback.latitude,
      longitude: item.longitude ?? fallback.longitude,
      status,
      data_quality_score: snapshot.data_quality_score ?? (item.data_quality_status === 'valid' ? 0.9 : 0.65),
      isReliable: snapshot.is_reliable ?? status === 'ONLINE',
    }
  }).filter((item) => item.latitude && item.longitude)
}

function normalizeHotspots(hotspots, summaries) {
  if (Array.isArray(hotspots) && hotspots.length) {
    return hotspots.map((item) => ({
      hotspot_id: String(item.id || item.hotspot_uid),
      ward_code: item.ward_code,
      severity: String(item.severity || 'medium').toLowerCase(),
      aqi: item.current_aqi,
      detected_at: item.last_detected_at,
      summary: item.trigger_reasons?.map((reason) => reason.reason || reason.pollutant).filter(Boolean).join(', ') || 'Hotspot under active lifecycle management.',
    }))
  }
  return summaries || []
}

function heatmapPoints(heatmap, stations) {
  const features = heatmap?.features || []
  if (features.length) {
    return features.map((feature) => {
      const [longitude, latitude] = feature.geometry?.coordinates || []
      const point = latLngToPoint(latitude, longitude)
      const aqi = feature.properties?.aqi || feature.properties?.average_aqi || 120
      return { ...point, aqi, radius: Math.max(7, Math.min(18, aqi / 16)) }
    }).filter((item) => Number.isFinite(item.x) && Number.isFinite(item.y))
  }
  return stations.map((item) => ({ ...latLngToPoint(item.latitude, item.longitude), aqi: extractAqi(item), radius: 12 }))
}

function latLngToPoint(latitude, longitude) {
  const x = ((longitude - cityBounds.minLongitude) / (cityBounds.maxLongitude - cityBounds.minLongitude)) * 100
  const y = 100 - ((latitude - cityBounds.minLatitude) / (cityBounds.maxLatitude - cityBounds.minLatitude)) * 100
  return { x: clamp(x, 4, 96), y: clamp(y, 4, 96) }
}

function extractAqi(station) {
  const reading = station?.readings?.find((item) => item.pollutant === 'AQI')
  return Math.round(reading?.value || station?.aqi || 0)
}

function aqiTone(value) {
  if (value >= 250) return 'severe'
  if (value >= 200) return 'poor'
  if (value >= 150) return 'moderate'
  return 'good'
}

function aqiLabel(value) {
  if (value == null) return 'Awaiting readings'
  if (value >= 250) return 'Severe city conditions'
  if (value >= 200) return 'Poor city conditions'
  if (value >= 150) return 'Moderate city conditions'
  return 'Acceptable city conditions'
}

function formatNumber(value) {
  return value == null ? 'No data' : Math.round(value)
}

function formatTime(value) {
  if (!value) return 'pending'
  const date = value instanceof Date ? value : new Date(value)
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function directionName(degrees) {
  if (degrees == null) return 'Direction unavailable'
  const names = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
  return `${names[Math.round(degrees / 45) % 8]} / ${Math.round(degrees)} deg`
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value))
}

createRoot(document.getElementById('root')).render(<App />)
