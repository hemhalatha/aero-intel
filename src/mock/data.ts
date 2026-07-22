// Mock data for All-India National Air Quality Intelligence Platform
import { Station, Ward, Hotspot, EvidenceItem, AttributionData, Task, Recommendation, Advisory } from '../types';

export const mockDashboardMetrics = {
  cityAQI: 265,
  activeHotspots: 12,
  offlineSensors: 4,
  worstWard: "Okhla Phase II (Delhi) / Talkatora (Lucknow)",
  weather: {
    temp: "29°C",
    humidity: "62%",
    windSpeed: "12 km/h",
    windDirection: "NW (315°)"
  }
};

export const mockStations: Station[] = [
  // Delhi NCR
  { id: "ST-05", name: "Okhla Ph-II (Delhi)", lat: 28.5308, lng: 77.2713, aqi: 390, status: "ONLINE" },
  { id: "ST-01", name: "Anand Vihar (Delhi)", lat: 28.6469, lng: 77.3160, aqi: 342, status: "ONLINE" },
  { id: "ST-03", name: "Punjabi Bagh (Delhi)", lat: 28.6683, lng: 77.1260, aqi: 285, status: "ONLINE" },
  { id: "ST-02", name: "R.K. Puram (Delhi)", lat: 28.5644, lng: 77.1726, aqi: 210, status: "ONLINE" },
  { id: "ST-04", name: "Mandir Marg (Delhi)", lat: 28.6341, lng: 77.1983, aqi: 180, status: "ONLINE" },
  
  // Bengaluru Metro
  { id: "BLR-PEE-AQ", name: "Peenya Industrial (Bengaluru)", lat: 13.0285, lng: 77.5186, aqi: 315, status: "ONLINE" },
  { id: "BLR-IND-AQ", name: "Indiranagar Station (Bengaluru)", lat: 12.9784, lng: 77.6408, aqi: 240, status: "DEGRADED" },
  { id: "BLR-CBD-AQ", name: "CBD Station (Bengaluru)", lat: 12.9716, lng: 77.5946, aqi: 110, status: "ONLINE" },
  { id: "BLR-WHT-AQ", name: "Whitefield (Bengaluru)", lat: 12.9698, lng: 77.7500, aqi: 290, status: "ONLINE" },

  // Mumbai MMR
  { id: "BOM-NAV-AQ", name: "Navi Mumbai Rabale (Mumbai)", lat: 19.1412, lng: 73.0089, aqi: 310, status: "ONLINE" },
  { id: "BOM-BKC-AQ", name: "BKC Bandra (Mumbai)", lat: 19.0600, lng: 72.8683, aqi: 275, status: "ONLINE" },
  { id: "BOM-COL-AQ", name: "Colaba (Mumbai)", lat: 18.9067, lng: 72.8147, aqi: 150, status: "ONLINE" },

  // Kolkata Metro
  { id: "CCU-BAL-AQ", name: "Ballygunge (Kolkata)", lat: 22.5280, lng: 88.3659, aqi: 305, status: "ONLINE" },
  { id: "CCU-VIC-AQ", name: "Victoria Memorial (Kolkata)", lat: 22.5448, lng: 88.3426, aqi: 225, status: "ONLINE" },

  // Chennai Metro
  { id: "MAA-MAN-AQ", name: "Manali Industrial (Chennai)", lat: 13.1667, lng: 80.2667, aqi: 280, status: "ONLINE" },
  { id: "MAA-ALA-AQ", name: "Alandur Bus Stand (Chennai)", lat: 13.0012, lng: 80.2012, aqi: 140, status: "ONLINE" },

  // Hyderabad Metro
  { id: "HYD-ZOO-AQ", name: "Zoo Park Bahadurpura (Hyderabad)", lat: 17.3489, lng: 78.4514, aqi: 260, status: "ONLINE" },
  { id: "HYD-SAN-AQ", name: "Sanathnagar (Hyderabad)", lat: 17.4578, lng: 78.4412, aqi: 215, status: "ONLINE" },

  // Lucknow / UP
  { id: "LKO-TAL-AQ", name: "Talkatora Industrial (Lucknow)", lat: 26.8389, lng: 80.8926, aqi: 365, status: "ONLINE" },

  // Gujarat
  { id: "AMD-MAN-AQ", name: "Maninagar (Ahmedabad)", lat: 22.9972, lng: 72.6008, aqi: 330, status: "ONLINE" }
];

export const mockWards: Ward[] = [
  // SEVERE (> 300 AQI)
  { id: "W-17", name: "Okhla Phase II (Delhi)", aqi: 390, riskLevel: "SEVERE" },
  { id: "DEL-W-88", name: "Bawana Industrial Zone (Delhi)", aqi: 380, riskLevel: "SEVERE" },
  { id: "KAN-W-01", name: "Nehru Nagar (Kanpur)", aqi: 370, riskLevel: "SEVERE" },
  { id: "LKO-W-04", name: "Talkatora Industrial (Lucknow)", aqi: 365, riskLevel: "SEVERE" },
  { id: "DEL-W-92", name: "Narela Industrial Area (Delhi)", aqi: 360, riskLevel: "SEVERE" },
  { id: "PUN-W-01", name: "Focal Point Industrial (Ludhiana)", aqi: 355, riskLevel: "SEVERE" },
  { id: "UP-W-12", name: "Vasundhara Sector 16 (Ghaziabad)", aqi: 350, riskLevel: "SEVERE" },
  { id: "W-04", name: "Anand Vihar Hub (Delhi)", aqi: 342, riskLevel: "SEVERE" },
  { id: "CCU-W-18", name: "Howrah Railway Hub (Kolkata)", aqi: 340, riskLevel: "SEVERE" },
  { id: "DEL-W-19", name: "Wazirpur Industrial Area (Delhi)", aqi: 335, riskLevel: "SEVERE" },
  { id: "AMD-W-12", name: "Maninagar (Ahmedabad)", aqi: 330, riskLevel: "SEVERE" },
  { id: "UP-W-89", name: "Varanasi Cantt Zone (Varanasi)", aqi: 325, riskLevel: "SEVERE" },
  { id: "NCR-W-45", name: "Greater Noida Alpha 1 (NCR)", aqi: 320, riskLevel: "SEVERE" },
  { id: "BLR-W-003", name: "Peenya Industrial (Bengaluru)", aqi: 315, riskLevel: "SEVERE" },
  { id: "BOM-W-09", name: "Navi Mumbai Rabale (Mumbai)", aqi: 310, riskLevel: "SEVERE" },
  { id: "BOM-W-22", name: "Chembur Industrial Corridor (Mumbai)", aqi: 305, riskLevel: "SEVERE" },
  { id: "CCU-W-02", name: "Ballygunge (Kolkata)", aqi: 305, riskLevel: "SEVERE" },

  // POOR / VERY POOR (200 - 300 AQI)
  { id: "DEL-W-34", name: "Rohini Sector 16 (Delhi)", aqi: 295, riskLevel: "VERY_POOR" },
  { id: "UP-W-02", name: "Sanjay Place (Agra)", aqi: 295, riskLevel: "VERY_POOR" },
  { id: "BOM-W-14", name: "Kurla West Arterial (Mumbai)", aqi: 295, riskLevel: "VERY_POOR" },
  { id: "BLR-W-005", name: "Whitefield Tech Park (Bengaluru)", aqi: 290, riskLevel: "VERY_POOR" },
  { id: "HYD-W-08", name: "Charminar Heritage Zone (Hyderabad)", aqi: 290, riskLevel: "VERY_POOR" },
  { id: "W-12", name: "Punjabi Bagh West (Delhi)", aqi: 285, riskLevel: "VERY_POOR" },
  { id: "MAA-W-01", name: "Manali Industrial Zone (Chennai)", aqi: 280, riskLevel: "VERY_POOR" },
  { id: "CCU-W-05", name: "Rabindra Bharati University (Kolkata)", aqi: 280, riskLevel: "VERY_POOR" },
  { id: "BOM-W-33", name: "Andheri MIDC (Mumbai)", aqi: 280, riskLevel: "VERY_POOR" },
  { id: "RAJ-W-01", name: "Mansarovar Sector 3 (Jaipur)", aqi: 275, riskLevel: "VERY_POOR" },
  { id: "BOM-W-04", name: "BKC Bandra Commercial (Mumbai)", aqi: 275, riskLevel: "VERY_POOR" },
  { id: "DEL-W-41", name: "Patparganj Industrial (Delhi)", aqi: 270, riskLevel: "VERY_POOR" },
  { id: "NCR-W-11", name: "Gurugram Cyber City (NCR)", aqi: 265, riskLevel: "VERY_POOR" },
  { id: "HYD-W-02", name: "Zoo Park Corridor (Hyderabad)", aqi: 260, riskLevel: "VERY_POOR" },
  { id: "BOM-W-19", name: "Thane West Junction (Mumbai)", aqi: 260, riskLevel: "VERY_POOR" },
  { id: "MAA-W-09", name: "Ambattur Industrial Estate (Chennai)", aqi: 255, riskLevel: "VERY_POOR" },
  { id: "BLR-W-12", name: "Marathahalli Junction (Bengaluru)", aqi: 250, riskLevel: "POOR" },
  { id: "BLR-W-002", name: "Indiranagar Station (Bengaluru)", aqi: 240, riskLevel: "POOR" },
  { id: "GUJ-W-04", name: "Surat Varachha Ring Road (Surat)", aqi: 240, riskLevel: "POOR" },
  { id: "CCU-W-01", name: "Victoria Memorial Zone (Kolkata)", aqi: 225, riskLevel: "POOR" },
  { id: "BLR-W-18", name: "Rajajinagar 1st Block (Bengaluru)", aqi: 220, riskLevel: "POOR" },
  { id: "HYD-W-01", name: "Sanathnagar Industrial (Hyderabad)", aqi: 215, riskLevel: "POOR" },
  { id: "W-22", name: "R.K. Puram Sector 5 (Delhi)", aqi: 210, riskLevel: "POOR" },
  { id: "BOM-W-40", name: "Malad West Station (Mumbai)", aqi: 210, riskLevel: "POOR" },
  { id: "LKO-W-10", name: "Gomti Nagar Extension (Lucknow)", aqi: 210, riskLevel: "POOR" },
  { id: "BLR-W-09", name: "Hebbal Flyover (Bengaluru)", aqi: 205, riskLevel: "POOR" },

  // MODERATE (< 200 AQI)
  { id: "BLR-W-15", name: "Koramangala 4th Block (Bengaluru)", aqi: 195, riskLevel: "MODERATE" },
  { id: "DEL-W-55", name: "Najafgarh Residential (Delhi)", aqi: 190, riskLevel: "MODERATE" },
  { id: "HYD-W-11", name: "Begumpet Airport Zone (Hyderabad)", aqi: 185, riskLevel: "MODERATE" },
  { id: "GUJ-W-09", name: "Satellite Area (Ahmedabad)", aqi: 185, riskLevel: "MODERATE" },
  { id: "W-09", name: "Mandir Marg Residential (Delhi)", aqi: 180, riskLevel: "MODERATE" },
  { id: "BLR-W-21", name: "Electronic City Phase 1 (Bengaluru)", aqi: 175, riskLevel: "MODERATE" },
  { id: "MAA-W-14", name: "Kodambakkam High Road (Chennai)", aqi: 175, riskLevel: "MODERATE" },
  { id: "LKO-W-01", name: "Hazratganj Market (Lucknow)", aqi: 175, riskLevel: "MODERATE" },
  { id: "CCU-W-09", name: "Salt Lake Sector V (Kolkata)", aqi: 170, riskLevel: "MODERATE" },
  { id: "BLR-W-004", name: "BTM Layout Ring Road (Bengaluru)", aqi: 165, riskLevel: "MODERATE" },
  { id: "BOM-W-52", name: "Borivali East National Park (Mumbai)", aqi: 165, riskLevel: "MODERATE" },
  { id: "DEL-W-60", name: "Lodhi Road Institutional (Delhi)", aqi: 160, riskLevel: "MODERATE" },
  { id: "MAA-W-05", name: "Velachery Main Road (Chennai)", aqi: 160, riskLevel: "MODERATE" },
  { id: "CCU-W-14", name: "Fort William Esplanade (Kolkata)", aqi: 155, riskLevel: "MODERATE" },
  { id: "HYD-W-20", name: "Gachibowli IT Corridor (Hyderabad)", aqi: 150, riskLevel: "MODERATE" },
  { id: "BOM-W-01", name: "Colaba Waterfront (Mumbai)", aqi: 150, riskLevel: "MODERATE" },
  { id: "BLR-W-30", name: "Yelahanka New Town (Bengaluru)", aqi: 145, riskLevel: "MODERATE" },
  { id: "BOM-W-11", name: "Worli Sea Face (Mumbai)", aqi: 140, riskLevel: "MODERATE" },
  { id: "MAA-W-02", name: "Alandur Transport Hub (Chennai)", aqi: 140, riskLevel: "MODERATE" },
  { id: "BLR-W-25", name: "Jayanagar 4th Block (Bengaluru)", aqi: 135, riskLevel: "MODERATE" },
  { id: "HYD-W-15", name: "Jubilee Hills Checkpost (Hyderabad)", aqi: 135, riskLevel: "MODERATE" },
  { id: "MAA-W-08", name: "Royapettah Metro Zone (Chennai)", aqi: 130, riskLevel: "MODERATE" },
  { id: "BLR-W-001", name: "CBD Station Ward (Bengaluru)", aqi: 110, riskLevel: "MODERATE" }
];

export const mockHotspots: Hotspot[] = [
  { id: "HS-801", ward: "Okhla Phase II (Delhi)", lat: 28.5308, lng: 77.2713, aqi: 390, severity: "CRITICAL" },
  { id: "HS-805", ward: "Talkatora (Lucknow)", lat: 26.8389, lng: 80.8926, aqi: 365, severity: "CRITICAL" },
  { id: "HS-802", ward: "Anand Vihar (Delhi)", lat: 28.6469, lng: 77.3160, aqi: 342, severity: "CRITICAL" },
  { id: "HS-806", ward: "Maninagar (Ahmedabad)", lat: 22.9972, lng: 72.6008, aqi: 330, severity: "CRITICAL" },
  { id: "HS-BLR-001", ward: "Peenya Industrial (Bengaluru)", lat: 13.0285, lng: 77.5186, aqi: 315, severity: "CRITICAL" },
  { id: "HS-807", ward: "Navi Mumbai (Mumbai)", lat: 19.1412, lng: 73.0089, aqi: 310, severity: "CRITICAL" },
  { id: "HS-808", ward: "Ballygunge (Kolkata)", lat: 22.5280, lng: 88.3659, aqi: 305, severity: "CRITICAL" },
  { id: "HS-MAA-001", ward: "Manali Industrial (Chennai)", lat: 13.1667, lng: 80.2667, aqi: 280, severity: "HIGH" },
  { id: "HS-803", ward: "Punjabi Bagh (Delhi)", lat: 28.6683, lng: 77.1260, aqi: 285, severity: "HIGH" }
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