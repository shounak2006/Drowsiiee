import React from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

export function FatigueChart({ history, status, isHUD = false }) {
  const getStrokeColor = () => {
    switch(status) {
      case 'SAFE': return '#00fca8';
      case 'WARNING': return '#fbbf24';
      case 'CRITICAL': return '#ff3366';
      default: return '#00fca8';
    }
  };

  return (
    <div className={`${isHUD ? 'w-full h-full' : 'glass-panel p-4 h-full min-h-[250px] flex flex-col'}`}>
      {!isHUD && <h3 className="text-slate-400 text-sm uppercase tracking-wider mb-4">Fatigue Trend</h3>}
      <div className="flex-1 w-full h-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={history} margin={{ top: 10, right: 0, left: -25, bottom: 0 }}>
            <defs>
              <linearGradient id="colorFatigue" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={getStrokeColor()} stopOpacity={isHUD ? 0.3 : 0.8}/>
                <stop offset="95%" stopColor={getStrokeColor()} stopOpacity={0}/>
              </linearGradient>
            </defs>
            <XAxis dataKey="time" stroke={isHUD ? "rgba(255,255,255,0.4)" : "#475569"} fontSize={10} tickMargin={8} maxChars={5} tickFormatter={(val) => val ? val.split(":")[2] : '' } />
            <YAxis stroke={isHUD ? "rgba(255,255,255,0.4)" : "#475569"} fontSize={10} domain={[0, 100]} />
            <Tooltip 
              contentStyle={{ backgroundColor: 'rgba(0,0,0,0.7)', border: '1px solid #334155', borderRadius: '8px', backdropFilter: 'blur(4px)' }}
              itemStyle={{ color: '#00fca8' }}
            />
            <Area 
              type="monotone" 
              dataKey="fatigue" 
              stroke={getStrokeColor()} 
              strokeWidth={isHUD ? 2 : 1}
              fillOpacity={1} 
              fill="url(#colorFatigue)" 
              isAnimationActive={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
