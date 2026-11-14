import React, { useState, useEffect } from 'react';
import {
  Play,
  Pause,
  Square,
  Cpu,
  RefreshCw,
  Sliders,
  CheckCircle2,
  AlertCircle,
  Radio,
  Zap,
  Users
} from 'lucide-react';
import { SimulatorStatus } from '../types';
import { simulatorApi } from '../services/api';

export const SimulatorPage: React.FC = () => {
  const [status, setStatus] = useState<SimulatorStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  const fetchStatus = async () => {
    try {
      const res = await simulatorApi.getStatus();
      setStatus(res);
    } catch (err) {
      console.error('Error fetching simulator status:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleStart = async () => {
    setActionLoading(true);
    await simulatorApi.start();
    await fetchStatus();
    setActionLoading(false);
  };

  const handlePause = async () => {
    setActionLoading(true);
    await simulatorApi.pause();
    await fetchStatus();
    setActionLoading(false);
  };

  const handleResume = async () => {
    setActionLoading(true);
    await simulatorApi.resume();
    await fetchStatus();
    setActionLoading(false);
  };

  const handleStop = async () => {
    setActionLoading(true);
    await simulatorApi.stop();
    await fetchStatus();
    setActionLoading(false);
  };

  const handleScenarioChange = async (scenarioKey: string) => {
    setActionLoading(true);
    await simulatorApi.setScenario(scenarioKey);
    await fetchStatus();
    setActionLoading(false);
  };

  const handleIntervalChange = async (seconds: number) => {
    setActionLoading(true);
    await simulatorApi.setInterval(seconds);
    await fetchStatus();
    setActionLoading(false);
  };

  const handleTargetChange = async (targetId: string) => {
    setActionLoading(true);
    await simulatorApi.setTarget(targetId);
    await fetchStatus();
    setActionLoading(false);
  };

  const scenariosList = [
    { key: 'normal', name: '1. Normal Astronaut Baseline', badge: 'Nominal', color: 'border-emerald-500/40 text-emerald-400', desc: 'Physiological vitals & cabin atmosphere adhere strictly to nominal deep space parameters.' },
    { key: 'elevated_heart_rate', name: '2. Elevated Resting Heart Rate', badge: 'Urgent', color: 'border-amber-500/40 text-amber-400', desc: 'Resting tachycardia onset climbing to 125-140 bpm while astronaut remains sedentary.' },
    { key: 'reduced_sleep', name: '3. Reduced Sleep Duration', badge: 'Behavioral', color: 'border-violet-500/40 text-violet-400', desc: 'Chronic sleep deprivation, suppressed parasympathetic tone, and fatigue elevation.' },
    { key: 'reduced_activity', name: '4. Reduced Physical Activity', badge: 'Musculoskeletal', color: 'border-cyan-500/40 text-cyan-400', desc: 'Microgravity hypokinesia and prolonged sedentary immobility.' },
    { key: 'abnormal_spo2', name: '5. Abnormal SpO2 Hypoxia Event', badge: 'Emergency', color: 'border-red-500/60 text-red-400', desc: 'Rapid blood oxygen desaturation falling below 88% SpO2 (triggers clinical emergency alert).' },
    { key: 'high_stress', name: '6. High Psychological Stress', badge: 'Stress Spike', color: 'border-amber-500/40 text-amber-400', desc: 'Acute sympathetic stress reaction with collapsed HRV (RMSSD < 22 ms).' },
    { key: 'co2_surge', name: '7. Environmental CO2 Surge', badge: 'Life Support', color: 'border-red-500/50 text-red-400', desc: 'Cabin scrubber saturation; CO2 concentration climbs over 2200 ppm in Command Module.' },
    { key: 'radiation_spike', name: '8. Solar Radiation Event (SPE)', badge: 'Radiation Alarm', color: 'border-amber-500/60 text-amber-400', desc: 'Solar particle event spikes radiation dose rate to 110 µSv/h.' },
    { key: 'sensor_disconnection', name: '9. Hardware Disconnection', badge: 'Packet Loss', color: 'border-slate-500/40 text-slate-400', desc: 'RF interference and 60% packet dropouts simulating loose bio-band electrode contact.' },
    { key: 'invalid_measurements', name: '10. Invalid Sensor Measurements', badge: 'Artifacts', color: 'border-orange-500/40 text-orange-400', desc: 'Extreme out-of-bounds artifacts and measurement quality degradation (<40%).' },
  ];

  return (
    <div className="space-y-6 pb-12 font-mono">
      {/* Header Panel */}
      <div className="p-6 rounded-2xl bg-space-900 border border-space-800 shadow-panel backdrop-blur-md flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-xl bg-amber-500/20 border border-amber-500/30 text-amber-400">
              <Cpu className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white tracking-wider">HARDWARE TELEMETRY SIMULATOR</h1>
              <p className="text-xs text-slate-400">Mathematical aerospace physiological & life-support stream engine</p>
            </div>
          </div>
        </div>

        {/* Controls */}
        <div className="flex flex-wrap items-center gap-2">
          {status?.status === 'running' ? (
            <button
              onClick={handlePause}
              disabled={actionLoading}
              className="px-4 py-2 rounded-lg bg-amber-600 hover:bg-amber-500 text-space-950 font-bold text-xs flex items-center space-x-1.5 transition-all shadow-panel"
            >
              <Pause className="w-4 h-4" />
              <span>PAUSE</span>
            </button>
          ) : status?.status === 'paused' ? (
            <button
              onClick={handleResume}
              disabled={actionLoading}
              className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs flex items-center space-x-1.5 transition-all shadow-panel"
            >
              <Play className="w-4 h-4" />
              <span>RESUME</span>
            </button>
          ) : (
            <button
              onClick={handleStart}
              disabled={actionLoading}
              className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs flex items-center space-x-1.5 transition-all shadow-panel"
            >
              <Play className="w-4 h-4" />
              <span>START ENGINE</span>
            </button>
          )}

          <button
            onClick={handleStop}
            disabled={actionLoading || status?.status === 'stopped'}
            className="px-4 py-2 rounded-lg bg-space-800 hover:bg-red-950/60 hover:text-red-400 text-slate-300 font-bold text-xs flex items-center space-x-1.5 transition-all border border-space-700"
          >
            <Square className="w-4 h-4" />
            <span>STOP</span>
          </button>
        </div>
      </div>

      {/* Operational Metrics Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
        <div className="p-4 rounded-xl bg-space-900/70 border border-space-800">
          <span className="text-slate-400 block text-[11px]">ENGINE STATE:</span>
          <span className={`text-lg font-bold uppercase mt-1 flex items-center space-x-2 ${
            status?.status === 'running' ? 'text-emerald-400' : status?.status === 'paused' ? 'text-amber-400' : 'text-slate-500'
          }`}>
            <span className={`w-2.5 h-2.5 rounded-full ${status?.status === 'running' ? 'bg-emerald-400 telemetry-pulse' : 'bg-slate-600'}`}></span>
            <span>{status?.status || 'STOPPED'}</span>
          </span>
        </div>

        <div className="p-4 rounded-xl bg-space-900/70 border border-space-800">
          <span className="text-slate-400 block text-[11px]">ACTIVE SCENARIO:</span>
          <span className="text-lg font-bold text-cyan-400 capitalize mt-1 block truncate">
            {status?.scenario.replace('_', ' ') || 'Normal'}
          </span>
        </div>

        <div className="p-4 rounded-xl bg-space-900/70 border border-space-800">
          <span className="text-slate-400 block text-[11px]">TARGET CREW MEMBER:</span>
          <div className="flex items-center space-x-1 mt-1">
            {['ASTRO-001', 'ASTRO-002', 'ASTRO-003'].map((astroId) => (
              <button
                key={astroId}
                onClick={() => handleTargetChange(astroId)}
                className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                  status?.target_astronaut_id === astroId
                    ? 'bg-cyan-500 text-space-950'
                    : 'bg-space-800 text-slate-400 hover:text-white'
                }`}
              >
                {astroId}
              </button>
            ))}
          </div>
        </div>

        <div className="p-4 rounded-xl bg-space-900/70 border border-space-800">
          <span className="text-slate-400 block text-[11px]">SAMPLING INTERVAL:</span>
          <div className="flex items-center space-x-1.5 mt-1">
            {[0.5, 1.0, 2.0, 5.0].map((sec) => (
              <button
                key={sec}
                onClick={() => handleIntervalChange(sec)}
                className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                  status?.interval_seconds === sec
                    ? 'bg-amber-500 text-space-950'
                    : 'bg-space-800 text-slate-400 hover:text-white'
                }`}
              >
                {sec}s
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* 10 Selectable Scenarios Grid */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center space-x-2">
            <Sliders className="w-4 h-4 text-cyan-400" />
            <span>Selectable Mission Scenario Profiles</span>
          </h2>
          <span className="text-xs text-slate-400">Click card to dynamically activate scenario</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {scenariosList.map((item) => {
            const isActive = status?.scenario === item.key;
            return (
              <button
                key={item.key}
                onClick={() => handleScenarioChange(item.key)}
                className={`text-left p-4 rounded-xl border transition-all duration-200 ${
                  isActive
                    ? 'bg-space-850 border-cyan-400 shadow-cyan-glow'
                    : 'bg-space-900/60 border-space-800 hover:border-space-700 hover:bg-space-850'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <h3 className={`text-sm font-bold ${isActive ? 'text-cyan-300' : 'text-slate-200'}`}>
                    {item.name}
                  </h3>
                  <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${item.color}`}>
                    {item.badge}
                  </span>
                </div>
                <p className="text-xs text-slate-400 leading-relaxed font-sans">{item.desc}</p>
                {isActive && (
                  <div className="mt-3 pt-2 border-t border-space-800 flex items-center text-[10px] text-cyan-400 font-bold space-x-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>CURRENTLY BROADCASTING LIVE</span>
                  </div>
                )}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};

