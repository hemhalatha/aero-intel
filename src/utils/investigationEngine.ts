import { Hotspot, EvidenceItem } from '../types';

export const generateEvidenceForHotspot = (hotspot: Hotspot): EvidenceItem[] => {
    const isIndustrial = hotspot.ward.toLowerCase().includes('industrial') || hotspot.ward.toLowerCase().includes('talkatora');
    const isTraffic = hotspot.ward.toLowerCase().includes('hub') || hotspot.ward.toLowerCase().includes('vihar');
    
    const items: EvidenceItem[] = [];
    
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
};
