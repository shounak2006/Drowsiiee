import React from 'react';
import { AlertTriangle, ShieldCheck, AlertOctagon } from 'lucide-react';

export function StatusIndicator({ status }) {
  const getConfig = () => {
    switch (status) {
      case 'SAFE':
        return {
          color: 'text-neonGreen',
          bg: 'bg-neonGreen/5',
          border: 'border-neonGreen/30',
          shadow: 'shadow-neon-green',
          icon: <ShieldCheck size={48} />,
          text: 'SAFE',
          subtext: 'Driver is alert.'
        };
      case 'WARNING':
        return {
          color: 'text-neonYellow',
          bg: 'bg-neonYellow/5',
          border: 'border-neonYellow/30',
          shadow: 'shadow-neon-yellow',
          icon: <AlertTriangle size={48} />,
          text: 'WARNING',
          subtext: 'Drowsiness signs detected.'
        };
      case 'CRITICAL':
        return {
          color: 'text-neonRed',
          bg: 'bg-neonRed/5',
          border: 'border-neonRed/30',
          shadow: 'shadow-neon-red animate-pulse-critical',
          icon: <AlertOctagon size={48} className="animate-bounce" />,
          text: 'CRITICAL',
          subtext: 'WAKE UP! High fatigue level!'
        };
      default:
        return {
          color: 'text-slate-500',
          bg: 'bg-slate-800',
          border: 'border-slate-700',
          shadow: '',
          icon: <ShieldCheck size={48} />,
          text: 'IDLE',
          subtext: 'System offline or analyzing...'
        };
    }
  };

  const c = getConfig();

  return (
    <div className={`glass-panel p-6 flex flex-col items-center justify-center h-full text-center border-2 transition-all duration-300 ${c.bg} ${c.border} ${c.shadow} min-h-[200px]`}>
      <div className={`mb-4 ${c.color} transition-colors duration-300`}>
        {c.icon}
      </div>
      <h2 className={`text-5xl lg:text-4xl xl:text-5xl font-extrabold tracking-widest uppercase mb-2 ${c.color} transition-colors duration-300`}>
        {c.text}
      </h2>
      <p className="text-slate-300 text-lg">
        {c.subtext}
      </p>
    </div>
  );
}
