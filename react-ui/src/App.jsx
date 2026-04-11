import React, { useEffect } from 'react';
import { useDetectionStream } from './hooks/useDetectionStream';
import { LiveVideo } from './components/LiveVideo';
import { ThreeVisualizer } from './components/ThreeVisualizer';
import { StatusIndicator } from './components/StatusIndicator';
import { Activity, Play, Square } from 'lucide-react';

function App() {
  const {
    data,
    history,
    connected,
    cameraError,
    monitoring,
    startCamera,
    stopCamera,
    attachVideoRef,
  } = useDetectionStream();

  // Auto-start camera when page loads
  useEffect(() => {
    startCamera();
    return () => { stopCamera(); };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className={`min-h-screen p-6 transition-all duration-300 ${data.status === 'CRITICAL' ? 'animate-shake' : ''}`}>

      {/* Header */}
      <header className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-neonCyan">
            <Activity size={24} />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-wider text-white">
              DROWSIIEE <span className="text-slate-500 font-normal">AI.SYSTEM</span>
            </h1>
            <p className="text-xs text-slate-400 font-mono flex items-center gap-2 mt-1">
              <span className={`w-2 h-2 rounded-full ${
                cameraError  ? 'bg-neonRed' :
                connected    ? 'bg-neonGreen animate-pulse' :
                monitoring   ? 'bg-amber-400 animate-pulse' :
                               'bg-slate-500'
              }`}></span>
              {cameraError
                ? 'CAMERA ERROR — CHECK PERMISSIONS'
                : connected
                  ? 'CONNECTED · PROCESSING LIVE'
                  : monitoring
                    ? 'CAMERA ON · RUN python app.py TO CONNECT'
                    : 'IDLE'}
            </p>
          </div>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-4 bg-slate-800/40 border border-slate-700 p-2 rounded-lg backdrop-blur-sm shadow-xl">
          <button
            onClick={startCamera}
            disabled={monitoring && !cameraError}
            className={`flex items-center gap-2 px-5 py-2 rounded-md font-bold tracking-wider text-sm transition-all duration-300
              ${(monitoring && !cameraError)
                ? 'bg-slate-700/50 text-slate-500 cursor-not-allowed'
                : 'bg-neonGreen/10 text-neonGreen hover:bg-neonGreen/20 hover:shadow-[0_0_15px_rgba(57,255,20,0.3)] border border-neonGreen/30'}`}
          >
            <Play size={16} /> START
          </button>

          <button
            onClick={stopCamera}
            disabled={!monitoring}
            className={`flex items-center gap-2 px-5 py-2 rounded-md font-bold tracking-wider text-sm transition-all duration-300
              ${!monitoring
                ? 'bg-slate-700/50 text-slate-500 cursor-not-allowed'
                : 'bg-neonRed/10 text-neonRed hover:bg-neonRed/20 hover:shadow-[0_0_15px_rgba(255,49,49,0.3)] border border-neonRed/30'}`}
          >
            <Square size={16} fill="currentColor" /> STOP
          </button>
        </div>
      </header>

      {/* Main Grid */}
      <div className="flex flex-col xl:flex-row gap-6 lg:h-[calc(100vh-120px)]">

        {/* Left Column - Video HUD */}
        <div className="flex-1 flex flex-col gap-6 h-full">
          <div className="flex-1 h-[60vh] xl:h-auto min-h-[500px]">
            <LiveVideo
              data={data}
              history={history}
              attachVideoRef={attachVideoRef}
              connected={connected}
              cameraError={cameraError}
            />
          </div>
        </div>

        {/* Right Column - Matrix & Status */}
        <div className="w-full xl:w-[400px] flex flex-col gap-6 min-h-[600px] xl:h-[calc(100vh-120px)]">
          <div className="glass-panel flex-1 overflow-hidden relative border border-slate-700 group min-h-[300px]">
            <div className="absolute top-4 left-4 text-xs tracking-wider text-slate-500 font-bold z-10">AI STATE MATRIX</div>
            <ThreeVisualizer status={data.status} />
            <div className="absolute top-4 right-4 flex gap-1">
              <div className="w-1 h-4 bg-slate-600"></div>
              <div className="w-1 h-3 mt-1 bg-slate-600"></div>
              <div className="w-1 h-2 mt-2 bg-slate-600"></div>
            </div>
          </div>

          <div className="flex-1 min-h-[300px]">
            <StatusIndicator status={data.status} />
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
