import React from 'react';
import { Activity, Eye, Zap, Clock } from 'lucide-react';

export function MetricsPanel({ data }) {
  const getValueColor = (val, thresholds) => {
    if (val >= thresholds[1]) return 'text-neonRed';
    if (val >= thresholds[0]) return 'text-neonYellow';
    return 'text-neonGreen';
  };

  return (
    <div className="grid grid-cols-2 gap-4">
      {/* Fatigue Score */}
      <div className="glass-panel p-4 flex flex-col justify-between min-h-[100px]">
        <div className="flex items-center gap-2 text-slate-400 mb-2">
          <Activity size={18} />
          <span className="text-sm uppercase tracking-wider">Fatigue</span>
        </div>
        <div className={`text-4xl font-mono ${getValueColor(data.fatigue_score, [40, 65])}`}>
          {data.fatigue_score.toFixed(1)}
        </div>
      </div>

      {/* EAR */}
      <div className="glass-panel p-4 flex flex-col justify-between min-h-[100px]">
        <div className="flex items-center gap-2 text-slate-400 mb-2">
          <Eye size={18} />
          <span className="text-sm uppercase tracking-wider">EAR</span>
        </div>
        <div className={`text-4xl font-mono ${data.ear < 0.25 ? 'text-neonRed' : 'text-neonGreen'}`}>
          {data.ear.toFixed(3)}
        </div>
      </div>

      {/* Blink Rate */}
      <div className="glass-panel p-4 flex flex-col justify-between min-h-[100px]">
        <div className="flex items-center gap-2 text-slate-400 mb-2">
          <Zap size={18} />
          <span className="text-sm uppercase tracking-wider">Blink Rate</span>
        </div>
        <div className="text-4xl font-mono text-white">
          {data.blink_rate.toFixed(1)} <span className="text-sm text-slate-500">/min</span>
        </div>
      </div>

      {/* FPS */}
      <div className="glass-panel p-4 flex flex-col justify-between min-h-[100px]">
        <div className="flex items-center gap-2 text-slate-400 mb-2">
          <Clock size={18} />
          <span className="text-sm uppercase tracking-wider">FPS</span>
        </div>
        <div className="text-4xl font-mono text-slate-300">
          {data.fps.toFixed(1)}
        </div>
      </div>
    </div>
  );
}
