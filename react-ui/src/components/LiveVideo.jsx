import React from 'react';
import { FatigueChart } from './FatigueChart';
import { Activity, Eye, Zap, VideoOff, UserX } from 'lucide-react';

export function LiveVideo({ data, history, attachVideoRef, connected, cameraError }) {
  const getBorderColor = () => {
    if (cameraError) return 'border-slate-700';
    switch (data?.status) {
      case 'SAFE':     return 'border-neonGreen shadow-neon-green';
      case 'WARNING':  return 'border-neonYellow shadow-neon-yellow';
      case 'CRITICAL': return 'border-neonRed shadow-neon-red animate-pulse-critical';
      default:         return 'border-slate-700';
    }
  };

  const getTextColor = (val, thresholds) => {
    if (val >= thresholds[1]) return 'text-neonRed font-bold drop-shadow-[0_0_8px_rgba(255,51,102,0.8)]';
    if (val >= thresholds[0]) return 'text-neonYellow font-bold drop-shadow-[0_0_8px_rgba(251,191,36,0.8)]';
    return 'text-neonGreen font-bold drop-shadow-[0_0_8px_rgba(0,252,168,0.8)]';
  };

  return (
    <div className={`relative rounded-xl overflow-hidden glass-panel border-2 transition-all duration-300 ${getBorderColor()} h-full min-h-[500px] flex flex-col bg-black`}>

      {/* Live Feed Status Pill */}
      <div className="absolute top-4 left-4 bg-black/60 px-4 py-1.5 rounded-full text-xs font-mono backdrop-blur-md z-20 text-white flex items-center gap-2 border border-slate-600/50">
        <span className={`w-2 h-2 rounded-full ${
          cameraError   ? 'bg-neonRed' :
          !connected    ? 'bg-slate-500 animate-pulse' :
          data?.status === 'IDLE' ? 'bg-slate-500 animate-pulse' :
                          'bg-red-500 animate-pulse'
        }`}></span>
        {cameraError ? 'CAMERA ERROR' : connected ? 'LIVE FEED' : 'CONNECTING…'}
      </div>

      {/* HUD Overlay - Top Right Metrics */}
      <div className="absolute top-4 right-4 z-20 flex flex-col gap-3">
        {/* Fatigue */}
        <div className="bg-black/40 backdrop-blur-sm border border-slate-600/30 px-4 py-2 rounded-lg flex items-center justify-between gap-4">
          <span className="flex items-center gap-1 font-bold text-slate-300 text-xs font-mono"><Activity size={12}/> FATIGUE</span>
          <div className={`text-2xl font-mono tracking-wider ${getTextColor(data?.fatigue_score || 0, [40, 65])}`}>
            {(data?.fatigue_score || 0).toFixed(1)}
          </div>
        </div>

        {/* EAR */}
        <div className="bg-black/40 backdrop-blur-sm border border-slate-600/30 px-4 py-2 rounded-lg flex items-center justify-between gap-4">
          <span className="flex items-center gap-1 font-bold text-slate-300 text-xs font-mono"><Eye size={12}/> EAR</span>
          <div className={`text-2xl font-mono tracking-wider ${
            (data?.ear || 0) < 0.25
              ? 'text-neonRed font-bold drop-shadow-[0_0_8px_rgba(255,51,102,0.8)]'
              : 'text-neonGreen font-bold drop-shadow-[0_0_8px_rgba(0,252,168,0.8)]'
          }`}>
            {(data?.ear || 0).toFixed(3)}
          </div>
        </div>

        {/* Blink */}
        <div className="bg-black/40 backdrop-blur-sm border border-slate-600/30 px-4 py-2 rounded-lg flex items-center justify-between gap-4">
          <span className="flex items-center gap-1 font-bold text-slate-300 text-xs font-mono"><Zap size={12}/> BLINKS</span>
          <div className="text-2xl font-mono tracking-wider text-white font-bold drop-shadow-[0_0_8px_rgba(255,255,255,0.8)]">
            {(data?.blink_rate || 0).toFixed(1)}
          </div>
        </div>
      </div>

      {/* ── Browser camera feed (always rendered, hidden before stream attaches) ── */}
      <video
        ref={attachVideoRef}
        autoPlay
        playsInline
        muted
        className="absolute inset-0 w-full h-full object-cover z-0 opacity-90"
        style={{ display: cameraError ? 'none' : 'block' }}
      />

      {/* Face-not-detected overlay (subtle) */}
      {connected && data?.face_detected === false && !cameraError && (
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-10 flex flex-col items-center gap-2 text-slate-400 bg-black/40 backdrop-blur-sm px-6 py-4 rounded-xl border border-slate-700/50">
          <UserX size={32} />
          <span className="text-xs font-mono tracking-widest">NO FACE DETECTED</span>
        </div>
      )}

      {/* Camera error placeholder */}
      {cameraError && (
        <div className="absolute inset-0 z-10 flex flex-col items-center justify-center gap-4 bg-black">
          <div className="absolute inset-0 bg-[repeating-linear-gradient(0deg,transparent,transparent_2px,rgba(255,51,102,0.03)_2px,rgba(255,51,102,0.03)_4px)]" />
          <VideoOff size={48} className="text-slate-600" />
          <p className="text-neonRed font-mono text-sm tracking-widest uppercase">Camera Access Denied</p>
          <p className="text-slate-500 font-mono text-xs max-w-xs text-center">{cameraError}</p>
          <p className="text-slate-600 font-mono text-xs">Allow camera in your browser and click START.</p>
        </div>
      )}

      {/* Dark gradient for chart readability */}
      <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/20 to-transparent pointer-events-none z-10" />

      {/* Bottom chart overlay */}
      <div className="absolute bottom-0 left-0 right-0 h-48 z-20 px-4 pb-2 pt-8 pointer-events-none">
        <FatigueChart history={history} status={data?.status || 'IDLE'} isHUD={true} />
      </div>
    </div>
  );
}
