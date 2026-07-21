import React, { useState, useEffect } from 'react';
import { Truck, HardHat, Factory, Terminal, Cpu } from 'lucide-react';
import { motion } from 'framer-motion';
import { mockEvidenceItems } from '../mock/data';

export const Investigation: React.FC = () => {
  const [terminalText, setTerminalText] = useState('');
  const fullText = "> RUNNING SPATIAL SWEEP... \n> CHECKING SENTINEL-5P AEROSOL INDEX... \n> DETECTED UNCOVERED SOIL AT PERMIT #8891 (CONFIDENCE 92%)... \n> ATTRIBUTION COMPLETE.";

  useEffect(() => {
    let index = 0;
    const timer = setInterval(() => {
      setTerminalText(fullText.slice(0, index));
      index++;
      if (index > fullText.length) clearInterval(timer);
    }, 30);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="space-y-6">
      {/* AI Investigation Terminal Header */}
      <div className="glass-panel-cyan p-5 rounded-xl flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs text-brand-cyan font-mono mb-1">
            <Cpu className="h-4 w-4 animate-spin" />
            <span>AI AGENT INVESTIGATION ENGINE ACTIVE</span>
          </div>
          <h2 className="text-2xl font-bold font-mono text-white">HOTSPOT CASE #HS-801</h2>
          <p className="text-xs text-gray-400 font-mono mt-0.5">Ward 17 (Okhla Phase II) • Sensor Station ST-05</p>
        </div>
        <div className="font-mono text-right bg-dark-900/80 p-3 rounded-lg border border-dark-700">
          <div className="text-[10px] text-gray-400">ISOLATED CONFIDENCE</div>
          <div className="text-2xl font-bold text-brand-cyan">92.4%</div>
        </div>
      </div>

      {/* Terminal Output Card */}
      <div className="glass-panel p-4 rounded-xl font-mono text-xs text-brand-green bg-dark-950/90 border border-brand-green/30">
        <div className="flex items-center gap-2 text-gray-500 pb-2 border-b border-dark-800 mb-2">
          <Terminal className="h-4 w-4 text-brand-green" />
          <span>AEROINTEL AGENT LOG STREAM</span>
        </div>
        <pre className="whitespace-pre-wrap leading-relaxed">{terminalText}</pre>
      </div>

      {/* Evidence Cards Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {mockEvidenceItems.map((item) => (
          <motion.div
            key={item.id}
            whileHover={{ y: -4 }}
            className="glass-panel p-5 rounded-xl border border-dark-700/80 flex flex-col justify-between"
          >
            <div>
              <div className="flex justify-between items-start mb-3">
                <div className="p-2.5 bg-dark-900 border border-dark-700 rounded-lg">
                  {item.type === 'CONSTRUCTION' && <HardHat className="h-6 w-6 text-brand-amber" />}
                  {item.type === 'TRAFFIC' && <Truck className="h-6 w-6 text-brand-cyan" />}
                  {item.type === 'INDUSTRIAL' && <Factory className="h-6 w-6 text-brand-red" />}
                </div>
                <span className="text-xs font-mono font-bold px-2.5 py-1 bg-brand-cyan/10 border border-brand-cyan/30 text-brand-cyan rounded-md">
                  {(item.confidence * 100).toFixed(0)}% Match
                </span>
              </div>
              <h3 className="font-bold text-white text-sm mb-1">{item.title}</h3>
              <p className="text-xs text-gray-400 leading-relaxed mb-4">{item.description}</p>
            </div>

            <div className="border-t border-dark-700/80 pt-3 space-y-1 font-mono text-xs">
              {Object.entries(item.metadata).map(([key, value]) => (
                <div key={key} className="flex justify-between">
                  <span className="text-gray-500">{key}:</span>
                  <span className="text-gray-200 font-bold">{value}</span>
                </div>
              ))}
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
};