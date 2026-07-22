import React, { useState, useMemo } from 'react';
import { Sparkles, Check, MapPin, ShieldAlert } from 'lucide-react';
import { mockHotspots, mockTasks } from '../mock/data';
import { generateEvidenceForHotspot } from '../utils/investigationEngine';
import { Recommendation } from '../types';

export const Recommendations: React.FC = () => {
  const [selectedHotspotId, setSelectedHotspotId] = useState(mockHotspots[0].id);
  const selectedHotspot = mockHotspots.find(h => h.id === selectedHotspotId) || mockHotspots[0];

  const [appliedIds, setAppliedIds] = useState<Set<string>>(new Set());

  // Use the exact same AI investigation engine to pull the evidence
  const investigationResults = useMemo(() => {
    return generateEvidenceForHotspot(selectedHotspot);
  }, [selectedHotspot]);

  // Dynamically generate mitigation actions based on the specific evidence found
  const dynamicRecommendations = useMemo(() => {
    const recs: Recommendation[] = [];

    investigationResults.forEach(evidence => {
      // Don't generate direct actions for satellite context
      if (evidence.type === 'SATELLITE') return;

      if (evidence.type === 'INDUSTRIAL') {
        recs.push({
          id: `REC-IND-${evidence.id}`,
          title: "Factory Stack Shutdown & Audit",
          description: `Mandate emergency shutdown and inspection of units flagged in ${evidence.id}. Send PCB inspectors for immediate compliance check.`,
          priority: evidence.confidence > 0.8 ? 'HIGH' : 'MEDIUM',
          expectedReduction: "-45 AQI Points",
          department: "Pollution Control Board",
          costEstimate: "Compliance Enforcement",
          evidence: evidence.title,
          time: "12 Hours",
          applied: false,
          reductionValue: 45
        });
        recs.push({
          id: `REC-IND2-${evidence.id}`,
          title: "Industrial Area Water Sprinkling",
          description: `Deploy industrial-grade water cannons near identified fabrication units to suppress fugitive particulate matter.`,
          priority: 'MEDIUM',
          expectedReduction: "-15 AQI Points",
          department: "Municipality",
          costEstimate: "₹45,000 / day",
          evidence: "Secondary mitigation for " + evidence.title,
          time: "4 Hours",
          applied: false,
          reductionValue: 15
        });
      }

      if (evidence.type === 'TRAFFIC') {
        recs.push({
          id: `REC-TRF-${evidence.id}`,
          title: "Heavy Freight Diversion",
          description: `Issue directive to reroute diesel commercial transport away from ${evidence.metadata?.['Corridor'] || 'congested zones'} during peak hours.`,
          priority: evidence.confidence > 0.8 ? 'HIGH' : 'MEDIUM',
          expectedReduction: "-25 AQI Points",
          department: "Traffic Police",
          costEstimate: "Zero Operational Cost",
          evidence: evidence.title,
          time: "24 Hours",
          applied: false,
          reductionValue: 25
        });
      }

      if (evidence.type === 'CONSTRUCTION') {
        recs.push({
          id: `REC-CON-${evidence.id}`,
          title: "Dust Barrier Netting Enforcement",
          description: `Issue immediate stop-work warning to Permit ${evidence.metadata?.['Permit ID'] || 'sites'} until perimeter wind-breakers and dust suppression sprays are active.`,
          priority: 'HIGH',
          expectedReduction: "-30 AQI Points",
          department: "Public Works",
          costEstimate: "Compliance Notice",
          evidence: evidence.title,
          time: "8 Hours",
          applied: false,
          reductionValue: 30
        });
      }
    });

    // Add a generic multi-agency one if AQI is critical
    if (selectedHotspot.severity === 'CRITICAL') {
        recs.push({
            id: `REC-MULTI-${selectedHotspot.id}`,
            title: "Multi-Agency Taskforce Deployment",
            description: `Trigger GRAP (Graded Response Action Plan) Stage III protocols for the entire ${selectedHotspot.ward} district.`,
            priority: 'HIGH',
            expectedReduction: "-65 AQI Points",
            department: "Central Command",
            costEstimate: "Emergency Funds",
            evidence: `Severity Level: ${selectedHotspot.severity}`,
            time: "Immediately",
            applied: false,
            reductionValue: 65
        });
    }

    // Sort by projected AQI impact (highest first)
    return recs.sort((a, b) => (b.reductionValue || 0) - (a.reductionValue || 0));
  }, [investigationResults, selectedHotspot]);


  const toggleApply = (id: string) => {
    setAppliedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
        const rec = dynamicRecommendations.find(r => r.id === id);
        if (rec) {
          mockTasks.unshift({
            id: `TSK-${Math.floor(Math.random() * 900) + 100}`,
            title: rec.title,
            department: rec.department,
            priority: rec.priority,
            status: 'ASSIGNED',
            ward: selectedHotspot.ward,
            assignedDate: new Date().toISOString().split('T')[0] + ' ' + new Date().toLocaleTimeString().slice(0,5),
            ageDays: 0,
            escalationStatus: 'NORMAL',
            expectedReduction: rec.expectedReduction,
            estimatedTime: rec.time,
            evidence: rec.evidence,
            completionPercentage: 0
          });
        }
      }
      return next;
    });
  };

  const handleHotspotChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedHotspotId(e.target.value);
    setAppliedIds(new Set()); // Reset applied actions when switching wards
  };

  return (
    <div className="px-8 py-6 space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 pb-4 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2 mb-1">
            <Sparkles className="h-6 w-6 text-blue-600" /> AI Recommendation Engine
          </h1>
          <p className="text-sm font-medium text-slate-500">Evidence-backed mitigation directives derived from Hotspot Investigation data</p>
        </div>
        <div className="flex items-center gap-2 bg-white border border-slate-200 rounded-xl px-3 py-1.5 shadow-sm">
          <MapPin className="w-4 h-4 text-slate-500" />
          <select 
            value={selectedHotspotId} 
            onChange={handleHotspotChange}
            className="bg-transparent text-sm font-semibold text-slate-800 focus:outline-none cursor-pointer"
          >
            {mockHotspots.map(h => (
              <option key={h.id} value={h.id}>
                {h.ward}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Ward Context Summary */}
      <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
            <ShieldAlert className={`h-8 w-8 ${selectedHotspot.severity === 'CRITICAL' ? 'text-red-600' : 'text-amber-600'}`} />
            <div>
                <h3 className="text-sm font-bold text-slate-900">{selectedHotspot.ward}</h3>
                <p className="text-xs font-medium text-slate-500">Target Action Area</p>
            </div>
        </div>
        <div className="flex items-center gap-8">
            <div className="text-center">
                <div className="text-2xl font-bold text-slate-900">{selectedHotspot.aqi}</div>
                <div className="text-xs font-medium text-slate-500">Current AQI</div>
            </div>
            <div className="text-center">
                <div className={`text-sm font-bold px-3 py-1 rounded-full ${selectedHotspot.severity === 'CRITICAL' ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'}`}>
                    {selectedHotspot.severity}
                </div>
                <div className="text-xs font-medium text-slate-500 mt-1">Risk Level</div>
            </div>
            <div className="text-center">
                <div className="text-xl font-bold text-slate-900">{investigationResults.length}</div>
                <div className="text-xs font-medium text-slate-500">Pollution Sources</div>
            </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {dynamicRecommendations.map((rec) => {
          const isApplied = appliedIds.has(rec.id);
          return (
            <div
              key={rec.id}
              className={`ui-card flex flex-col justify-between ${
                isApplied ? 'border-emerald-500 bg-emerald-50/20' : ''
              }`}
            >
              <div>
                <div className="flex justify-between items-center mb-4">
                  <span className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${
                    rec.priority === 'HIGH' ? 'bg-red-50 text-red-700 border-red-200' : 'bg-amber-50 text-amber-700 border-amber-200'
                  }`}>
                    {rec.priority} PRIORITY
                  </span>
                  <span className="text-sm font-bold text-blue-600">{rec.expectedReduction}</span>
                </div>
                <h2 className="text-base font-semibold text-slate-900 mb-2">{rec.title}</h2>
                <p className="text-xs font-normal text-slate-700 leading-relaxed mb-6">{rec.description}</p>
              </div>

              <div className="space-y-3 pt-4 border-t border-slate-200">
                <div className="flex justify-between text-xs font-medium text-slate-700">
                  <span className="text-slate-500">Linked Evidence:</span>
                  <span className="font-semibold text-slate-900 truncate max-w-[150px]" title={rec.evidence}>{rec.evidence}</span>
                </div>
                <div className="flex justify-between text-xs font-medium text-slate-700">
                  <span className="text-slate-500">Target Dept:</span>
                  <span className="font-semibold text-slate-900">{rec.department}</span>
                </div>
                <div className="flex justify-between text-xs font-medium text-slate-700 pb-2">
                  <span className="text-slate-500">Est. Time:</span>
                  <span className="font-semibold text-slate-900">{rec.time}</span>
                </div>
                
                <button
                  onClick={() => toggleApply(rec.id)}
                  className={`w-full ${isApplied ? 'bg-emerald-600 hover:bg-emerald-700 text-white font-medium text-sm rounded-xl px-4 py-2 transition-colors duration-150 shadow-sm flex items-center justify-center gap-2' : 'ui-button-primary'}`}
                >
                  {isApplied ? <><Check className="h-4 w-4" /> Directive Issued</> : 'Issue Directive'}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};