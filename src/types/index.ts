// Type definitions
export interface Station {
  id: string;
  name: string;
  lat: number;
  lng: number;
  aqi: number;
  status: 'ONLINE' | 'OFFLINE' | 'DEGRADED';
}

export interface Ward {
  id: string;
  name: string;
  aqi: number;
  riskLevel: 'MODERATE' | 'POOR' | 'VERY_POOR' | 'SEVERE';
}

export interface Hotspot {
  id: string;
  ward: string;
  lat: number;
  lng: number;
  aqi: number;
  severity: 'HIGH' | 'CRITICAL' | 'MODERATE';
}

export interface EvidenceItem {
  id: string;
  timestamp: string;
  type: 'TRAFFIC' | 'CONSTRUCTION' | 'INDUSTRIAL' | 'SATELLITE';
  title: string;
  confidence: number;
  description: string;
  metadata: Record<string, string | number>;
}

export interface AttributionData {
  source: string;
  percentage: number;
  color: string;
}

export interface Task {
  id: string;
  title: string;
  department: 'Municipality' | 'Traffic Police' | 'Pollution Control Board' | 'Public Works';
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  status: 'ASSIGNED' | 'ACCEPTED' | 'IN_PROGRESS' | 'COMPLETED';
  ward: string;
  assignedDate: string;
  ageDays: number;
  escalationStatus: 'NORMAL' | 'REMINDER_SENT' | 'ESCALATED' | 'CRITICAL_ALERT';
}

export interface Recommendation {
  id: string;
  title: string;
  description: string;
  priority: 'HIGH' | 'MEDIUM' | 'LOW';
  expectedReduction: string;
  department: string;
  costEstimate: string;
  applied: boolean;
  evidence?: string;
  time?: string;
  reductionValue?: number;
}

export interface Advisory {
  language: string;
  code: string;
  text: string;
}