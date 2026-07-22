import React, { useState, useMemo } from 'react';
import { Truck, HardHat, Factory, Satellite, MapPin } from 'lucide-react';
import { mockHotspots } from '../mock/data';
import { EvidenceItem } from '../types';

export const Investigation: React.FC = () => {
  const [selectedHotspotId, setSelectedHotspotId] = useState(mockHotspots[0].id);
  const selectedHotspot = mockHotspots.find(h => h.id === selectedHotspotId) || mockHotspots[0];

  const dynamicEvidence = useMemo(() => {
    const isIndustrial = selectedHotspot.ward.toLowerCase().includes('industrial');
    const isTraffic = selectedHotspot.ward.toLowerCase().includes('hub') || selectedHotspot.ward.toLowerCase().includes('vihar');
    
    const items = [];
    
    if (isIndustrial) {
      items.push({
        id: "EVD-IND-01",
        timestamp: "2026-07-21 16:45:00",
        type: "INDUSTRIAL",
        title: "Stack Thermal Anomaly",
        confidence: 0.94,
        description: "Thermal infrared sensors identified heat signature from major fabrication units exceeding consent limits.",
        metadata: { "Stack Status": "Non-Compliant", "Temp Anomaly": "+4.2°C" }
      });
      items.push({
        id: "EVD-TRF-02",
        timestamp: "2026-07-21 17:15:00",
        type: "TRAFFIC",
        title: "Heavy Freight Movement",
        confidence: 0.45,
        description: "Mobility feed detected heavy diesel trucks moving into industrial zone.",
        metadata: { "Corridor": "Industrial Approach", "Idle Vehicles": 82 }
      });
    } else if (isTraffic) {
      items.push({
        id: "EVD-TRF-01",
        timestamp: "2026-07-21 17:15:00",
        type: "TRAFFIC",
        title: "Freight Corridor Congestion Spike",
        confidence: 0.96,
        description: "Geospatial mobility feed detected 450+ heavy diesel trucks idling for >35 minutes along arterial junction.",
        metadata: { "Corridor": "Arterial Road 4", "Avg Speed": "6 km/h", "Idle Vehicles": 482 }
      });
      items.push({
        id: "EVD-CON-02",
        timestamp: "2026-07-21 17:30:00",
        type: "CONSTRUCTION",
        title: "Minor Roadworks",
        confidence: 0.35,
        description: "Roadside excavation detected by municipal cameras.",
        metadata: { "Permit ID": "ROAD-221", "Distance": "100m Upwind" }
      });
    } else {
      items.push({
        id: "EVD-CON-01",
        timestamp: "2026-07-21 17:30:00",
        type: "CONSTRUCTION",
        title: "Uncovered Soil and Unmitigated Excavation",
        confidence: 0.92,
        description: "Sentinel-2 optical satellite detected high ground surface reflectance indicative of exposed dry earth across 12,000 sq.m without dust suppression sprays.",
        metadata: { "Permit ID": "CNST-2026-8891", "Distance": "320m Upwind", "Dust Index": "0.84" }
      });
      items.push({
        id: "EVD-TRF-03",
        timestamp: "2026-07-21 18:00:00",
        type: "TRAFFIC",
        title: "Local Traffic Build-up",
        confidence: 0.65,
        description: "Local ring road showing higher than normal density.",
        metadata: { "Corridor": "Ring Road", "Congestion Level": "High" }
      });
    }

    // Add a common satellite item
    items.push({
      id: "EVD-SAT-01",
      timestamp: "2026-07-21 19:15:00",
      type: "SATELLITE",
      title: "Aerosol Optical Depth (AOD) Spike",
      confidence: 0.88,
      description: "Sentinel-5P TROPOMI sensor confirms elevated boundary layer particulate concentration directly over the coordinate bounding box.",
      metadata: { "AOD Index": "0.62", "Observation": "Clear Sky Match" }
    });

    return items;
  }, [selectedHotspot.ward]);

  const overallConfidence = useMemo(() => {
    const confidences = dynamicEvidence.map(e => e.confidence).sort((a, b) => b - a);
    return ((confidences[0] + confidences[1]) / 2) * 100;
  }, [dynamicEvidence]);

  const handleHotspotChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedHotspotId(e.target.value);
  };

  return (
    <div className="px-8 py-6 space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="px-2.5 py-0.5 bg-red-50 text-red-700 border border-red-200 text-xs font-semibold rounded-full">
              Active Case File
            </span>
            <span className="text-xs font-medium text-slate-500">Incident #{selectedHotspot.id}</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 mb-1">Hotspot Investigation: {selectedHotspot.ward}</h1>
          <p className="text-sm font-medium text-slate-500">
            Cross-referencing satellite aerosol feeds, traffic density indices, and municipal registries
          </p>
        </div>
        <div className="flex flex-col items-end gap-3">
          <div className="flex items-center gap-2 bg-white border border-slate-200 rounded-xl px-3 py-1.5 shadow-sm">
            <MapPin className="w-4 h-4 text-slate-500" />
            <select 
              value={selectedHotspotId} 
              onChange={handleHotspotChange}
              className="bg-transparent text-sm font-semibold text-slate-800 focus:outline-none cursor-pointer"
            >
              {mockHotspots.map(h => (
                <option key={h.id} value={h.id}>
                  {h.ward} ({h.aqi} AQI)
                </option>
              ))}
            </select>
          </div>
          <div className="text-right">
            <span className="text-xs font-medium text-slate-500">Overall Confidence Score</span>
            <div className="text-2xl font-bold text-slate-900">{overallConfidence.toFixed(1)}%</div>
          </div>
        </div>
      </div>

      {/* Evidence Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {dynamicEvidence.map((item) => (
          <div key={item.id} className="ui-card flex flex-col justify-between">
            <div>
              <div className="flex justify-between items-start mb-4">
                <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-slate-700">
                  {item.type === 'CONSTRUCTION' && <HardHat className="h-6 w-6 text-amber-600" />}
                  {item.type === 'TRAFFIC' && <Truck className="h-6 w-6 text-blue-600" />}
                  {item.type === 'INDUSTRIAL' && <Factory className="h-6 w-6 text-red-600" />}
                  {item.type === 'SATELLITE' && <Satellite className="h-6 w-6 text-purple-600" />}
                </div>
                <span className="text-xs font-semibold px-2.5 py-1 bg-slate-100 text-slate-700 rounded-lg border border-slate-200">
                  {(item.confidence * 100).toFixed(0)}% Confidence
                </span>
              </div>
              <h2 className="text-base font-semibold text-slate-900 mb-2">{item.title}</h2>
              <p className="text-xs font-normal text-slate-700 leading-relaxed mb-6">{item.description}</p>
            </div>

            <div className="border-t border-slate-200 pt-4 space-y-2 text-xs">
              {Object.entries(item.metadata).map(([key, value]) => (
                <div key={key} className="flex justify-between items-center">
                  <span className="font-medium text-slate-500">{key}:</span>
                  <span className="font-semibold text-slate-900">{String(value)}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Investigation Activity Log */}
      <div className="ui-card space-y-4">
        <div className="flex justify-between items-center pb-3 border-b border-slate-200">
          <div>
            <h2 className="text-base font-semibold text-slate-900 mb-1">Evidence Gathering Audit Trail</h2>
            <p className="text-xs font-medium text-slate-500">Sequential sensor triggers and satellite sweep logs</p>
          </div>
          <span className="text-xs font-medium text-slate-500">{dynamicEvidence.length} Logs Recorded</span>
        </div>

        <div className="space-y-3">
          {dynamicEvidence.map((item, idx) => (
            <div key={item.id} className="p-4 bg-slate-50/80 border border-slate-200 rounded-xl flex items-start gap-4">
              <div className="w-8 h-8 rounded-xl bg-white border border-slate-200 flex items-center justify-center text-xs font-bold text-slate-700 shrink-0">
                {idx + 1}
              </div>
              <div className="flex-1 text-xs space-y-1">
                <div className="flex justify-between font-medium">
                  <span className="text-slate-500">{item.timestamp}</span>
                  <span className="text-blue-600 font-semibold">{item.type} DETECTED</span>
                </div>
                <div className="text-sm font-semibold text-slate-900">{item.title}</div>
                <p className="text-slate-700 font-normal">{item.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
