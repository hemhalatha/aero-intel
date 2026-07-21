// Mock data
import { Station, Ward, Hotspot, EvidenceItem, AttributionData, Task, Recommendation, Advisory } from '../types';

export const mockDashboardMetrics = {
  cityAQI: 218,
  activeHotspots: 4,
  offlineSensors: 2,
  worstWard: "Ward 17 (Okhla Phase II)",
  weather: {
    temp: "28°C",
    humidity: "64%",
    windSpeed: "14 km/h",
    windDirection: "SSW (210°)"
  }
};

export const mockStations: Station[] = [
  { id: "ST-01", name: "Anand Vihar", lat: 28.6469, lng: 77.3160, aqi: 342, status: "ONLINE" },
  { id: "ST-02", name: "R.K. Puram", lat: 28.5644, lng: 77.1726, aqi: 210, status: "ONLINE" },
  { id: "ST-03", name: "Punjabi Bagh", lat: 28.6683, lng: 77.1260, aqi: 285, status: "ONLINE" },
  { id: "ST-04", name: "Mandir Marg", lat: 28.6341, lng: 77.1983, aqi: 180, status: "ONLINE" },
  { id: "ST-05", name: "Okhla Ph-II", lat: 28.5308, lng: 77.2713, aqi: 390, status: "ONLINE" },
  { id: "ST-06", name: "Ito Crossing", lat: 28.6289, lng: 77.2415, aqi: 0, status: "OFFLINE" },
  { id: "ST-07", name: "Dwarka Sec-8", lat: 28.5708, lng: 77.0715, aqi: 0, status: "OFFLINE" }
];

export const mockWards: Ward[] = [
  { id: "W-17", name: "Okhla Phase II", aqi: 390, riskLevel: "SEVERE" },
  { id: "W-04", name: "Anand Vihar Hub", aqi: 342, riskLevel: "SEVERE" },
  { id: "W-12", name: "Punjabi Bagh West", aqi: 285, riskLevel: "VERY_POOR" },
  { id: "W-09", name: "Wazirpur Industrial Area", aqi: 260, riskLevel: "VERY_POOR" },
  { id: "W-22", name: "R.K. Puram Sector 5", aqi: 210, riskLevel: "POOR" }
];

export const mockHotspots: Hotspot[] = [
  { id: "HS-801", ward: "Okhla Phase II", lat: 28.5308, lng: 77.2713, aqi: 390, severity: "CRITICAL" },
  { id: "HS-802", ward: "Anand Vihar", lat: 28.6469, lng: 77.3160, aqi: 342, severity: "CRITICAL" },
  { id: "HS-803", ward: "Punjabi Bagh", lat: 28.6683, lng: 77.1260, aqi: 285, severity: "HIGH" },
  { id: "HS-804", ward: "Wazirpur Sector B", lat: 28.6988, lng: 77.1654, aqi: 260, severity: "HIGH" }
];

export const mockTrendData = [
  { time: "00:00", AQI: 240, PM25: 140, PM10: 210 },
  { time: "04:00", AQI: 260, PM25: 160, PM10: 230 },
  { time: "08:00", AQI: 310, PM25: 210, PM10: 290 },
  { time: "12:00", AQI: 280, PM25: 180, PM10: 250 },
  { time: "16:00", AQI: 220, PM25: 130, PM10: 190 },
  { time: "20:00", AQI: 250, PM25: 150, PM10: 220 }
];

export const mockEvidenceItems: EvidenceItem[] = [
  {
    id: "EVD-101",
    timestamp: "2026-07-21 17:30:00",
    type: "CONSTRUCTION",
    title: "Uncovered Soil and Unmitigated Excavation",
    confidence: 0.92,
    description: "Sentinel-2 optical satellite detected high ground surface reflectance indicative of exposed dry earth across 12,000 sq.m without dust suppression sprays.",
    metadata: { "Permit ID": "CNST-2026-8891", "Distance": "320m Upwind", "Dust Index": "0.84" }
  },
  {
    id: "EVD-102",
    timestamp: "2026-07-21 17:15:00",
    type: "TRAFFIC",
    title: "Freight Corridor Congestion Spike",
    confidence: 0.78,
    description: "Geospatial mobility feed detected 450+ heavy diesel trucks idling for >35 minutes along Ring Road arterial junction.",
    metadata: { "Corridor": "Arterial Road 4", "Avg Speed": "6 km/h", "Idle Vehicles": 482 }
  },
  {
    id: "EVD-103",
    timestamp: "2026-07-21 16:45:00",
    type: "INDUSTRIAL",
    title: "Stack Thermal Anomaly",
    confidence: 0.20,
    description: "Thermal infrared sensors identified heat signature from small fabrication units; emissions remain within statutory consent limits.",
    metadata: { "Stack Status": "Compliant", "Temp Anomaly": "+2.4°C" }
  }
];

export const mockAttributionData: AttributionData[] = [
  { source: "Construction Dust", percentage: 85, color: "#FFB800" },
  { source: "Vehicular Emissions", percentage: 10, color: "#00F0FF" },
  { source: "Industrial Stack", percentage: 5, color: "#FF4D4D" }
];

export const mockScenarioBaseline = [
  { hour: "00h", AQI: 380 },
  { hour: "04h", AQI: 375 },
  { hour: "08h", AQI: 365 },
  { hour: "12h", AQI: 360 },
  { hour: "16h", AQI: 350 },
  { hour: "20h", AQI: 345 },
  { hour: "24h", AQI: 340 }
];

export const mockScenarioIntervention = [
  { hour: "00h", AQI: 380 },
  { hour: "04h", AQI: 340 },
  { hour: "08h", AQI: 310 },
  { hour: "12h", AQI: 285 },
  { hour: "16h", AQI: 260 },
  { hour: "20h", AQI: 255 },
  { hour: "24h", AQI: 250 }
];

export const mockRecommendations: Recommendation[] = [
  {
    id: "REC-01",
    title: "Anti-Smog Sprinkling Deployment",
    description: "Dispatch 4 high-pressure water sprinklers to Okhla Phase II perimeter roads to suppress fugitive dust.",
    priority: "HIGH",
    expectedReduction: "-45 AQI Points",
    department: "Municipality",
    costEstimate: "₹25,000 / day",
    applied: false
  },
  {
    id: "REC-02",
    title: "Dust Barrier Netting Enforcement",
    description: "Issue immediate stop-work warning to Construction Permit #CNST-2026-8891 until perimeter wind-breakers are mounted.",
    priority: "HIGH",
    expectedReduction: "-30 AQI Points",
    department: "Public Works",
    costEstimate: "Compliance Notice",
    applied: false
  },
  {
    id: "REC-03",
    title: "Freight Traffic Rerouting",
    description: "Divert heavy diesel commercial transport to Outer Bypass corridor between 18:00 and 06:00.",
    priority: "MEDIUM",
    expectedReduction: "-18 AQI Points",
    department: "Traffic Police",
    costEstimate: "Zero Operational Cost",
    applied: false
  }
];

export const mockTasks: Task[] = [
  {
    id: "TSK-301",
    title: "Inspect Construction Site Permit #8891",
    department: "Municipality",
    priority: "HIGH",
    status: "ASSIGNED",
    ward: "Okhla Phase II",
    assignedDate: "2026-07-21 10:00",
    ageDays: 1,
    escalationStatus: "NORMAL"
  },
  {
    id: "TSK-298",
    title: "Deploy Water Sprinklers along Corridor 4",
    department: "Public Works",
    priority: "CRITICAL",
    status: "ACCEPTED",
    ward: "Anand Vihar",
    assignedDate: "2026-07-20 14:30",
    ageDays: 2,
    escalationStatus: "REMINDER_SENT"
  },
  {
    id: "TSK-254",
    title: "Enforce Freight Rerouting at Junction 12",
    department: "Traffic Police",
    priority: "HIGH",
    status: "IN_PROGRESS",
    ward: "Punjabi Bagh",
    assignedDate: "2026-07-19 09:00",
    ageDays: 3,
    escalationStatus: "ESCALATED"
  },
  {
    id: "TSK-190",
    title: "Audit Stack Emissions at Industrial Block C",
    department: "Pollution Control Board",
    priority: "CRITICAL",
    status: "ASSIGNED",
    ward: "Wazirpur",
    assignedDate: "2026-07-17 11:15",
    ageDays: 5,
    escalationStatus: "CRITICAL_ALERT"
  }
];

export const mockAdvisories: Advisory[] = [
  { language: "English", code: "en", text: "Air quality is Severe. Avoid all outdoor strenuous activities. Keep windows closed and run N95 / HEPA filtration indoors." },
  { language: "Tamil", code: "ta", text: "காற்றின் தரம் மிகவும் மோசமாக உள்ளது. வெளிப்புற உடற்பயிற்சி மற்றும் செயல்பாடுகளை தவிர்க்கவும். வீட்டிற்குள் இருங்கள்." },
  { language: "Hindi", code: "hi", text: "वायु गुणवत्ता गंभीर श्रेणी में है। बाहर की सभी गतिविधियों से बचें। मास्क पहनें और खिड़कियां बंद रखें।" },
  { language: "Kannada", code: "kn", text: "ವಾಯು ಗುಣಮಟ್ಟವು ತೀವ್ರವಾಗಿದೆ. ಹೊರಾಂಗಣ ಚಟುವಟಿಕೆಗಳನ್ನು தவிர்க்கಿ. ಮುಖವಾಡ ಧರಿಸಿ." }
];