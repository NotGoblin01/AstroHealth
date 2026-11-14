import React, { useState } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine
} from 'recharts';
import { SensorReading } from '../types';

interface BiometricChartsProps {
  data: SensorReading[];
  astronautName: string;
}

export const BiometricCharts: React.FC<BiometricChartsProps> = ({ data, astronautName }) => {
  const [activeChart, setActiveChart] = useState<'cardio' | 'spo2' | 'temp' | 'motion'>('cardio');

  // Format timestamp for chart XAxis with defensive validation
  const formattedData = (data || []).map((d) => {
    let timeLabel = '--:--:--';
    try {
      const parsed = new Date(d.timestamp);
      if (!isNaN(parsed.getTime())) {
        timeLabel = parsed.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      }
    } catch {
      timeLabel = '--:--:--';
    }
    return {
      ...d,
      timeLabel
    };
  });

  return (
    <div className="rounded-xl border border-space-800 bg-space-900/70 p-5 backdrop-blur-md shadow-panel">
      {/* Chart Header & Tab Selectors */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-6 pb-4 border-b border-space-800">
        <div>
          <h2 className="text-sm font-semibold uppercase tracking-wider text-white flex items-center space-x-2">
            <span>Biometric Telemetry Stream</span>
            <span className="text-xs font-mono text-cyan-400 font-normal">({astronautName})</span>
          </h2>
          <p className="text-[11px] text-slate-400 font-mono mt-0.5">
            Continuous PPG, Thermistor & 6-Axis IMU sensor fusion
          </p>
        </div>

        <div className="flex items-center space-x-1 p-1 rounded-lg bg-space-950 border border-space-800">
          <button
            onClick={() => setActiveChart('cardio')}
            className={`px-3 py-1 text-xs font-medium rounded transition-all ${activeChart === 'cardio'
                ? 'bg-cyan-500 text-space-950 font-bold shadow-cyan-glow'
                : 'text-slate-400 hover:text-white'
              }`}
          >
            Heart Rate & HRV
          </button>
          <button
            onClick={() => setActiveChart('spo2')}
            className={`px-3 py-1 text-xs font-medium rounded transition-all ${activeChart === 'spo2'
                ? 'bg-cyan-500 text-space-950 font-bold shadow-cyan-glow'
                : 'text-slate-400 hover:text-white'
              }`}
          >
            Pulse Oximetry (SpO2)
          </button>
          <button
            onClick={() => setActiveChart('temp')}
            className={`px-3 py-1 text-xs font-medium rounded transition-all ${activeChart === 'temp'
                ? 'bg-cyan-500 text-space-950 font-bold shadow-cyan-glow'
                : 'text-slate-400 hover:text-white'
              }`}
          >
            Core Temp
          </button>
          <button
            onClick={() => setActiveChart('motion')}
            className={`px-3 py-1 text-xs font-medium rounded transition-all ${activeChart === 'motion'
                ? 'bg-cyan-500 text-space-950 font-bold shadow-cyan-glow'
                : 'text-slate-400 hover:text-white'
              }`}
          >
            IMU Motion
          </button>
        </div>
      </div>

      {/* Main Chart Canvas */}
      <div className="h-64 sm:h-80 w-full">
        {formattedData.length === 0 ? (
          <div className="h-full flex items-center justify-center text-slate-500 font-mono text-xs">
            Connecting to spacecraft telemetry feed...
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            {activeChart === 'cardio' ? (
              <LineChart data={formattedData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" opacity={0.6} />
                <XAxis dataKey="timeLabel" stroke="#64748b" fontSize={10} tickLine={false} />
                <YAxis yAxisId="hr" stroke="#06b6d4" fontSize={10} domain={['dataMin - 10', 'dataMax + 10']} tickLine={false} unit=" bpm" />
                <YAxis yAxisId="hrv" orientation="right" stroke="#8b5cf6" fontSize={10} domain={[10, 120]} tickLine={false} unit=" ms" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#080d1a', borderColor: '#1e293b', borderRadius: '8px', fontSize: '11px', fontFamily: 'monospace' }}
                  labelStyle={{ color: '#94a3b8' }}
                />
                <ReferenceLine yAxisId="hr" y={100} stroke="#f59e0b" strokeDasharray="3 3" label={{ value: 'Tachycardia (100 bpm)', fill: '#f59e0b', fontSize: 10 }} />
                <Line yAxisId="hr" type="monotone" dataKey="heart_rate" name="Heart Rate (bpm)" stroke="#06b6d4" strokeWidth={2} dot={false} isAnimationActive={false} />
                <Line yAxisId="hrv" type="monotone" dataKey="hrv" name="HRV (ms)" stroke="#8b5cf6" strokeWidth={1.5} dot={false} isAnimationActive={false} />
              </LineChart>
            ) : activeChart === 'spo2' ? (
              <LineChart data={formattedData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" opacity={0.6} />
                <XAxis dataKey="timeLabel" stroke="#64748b" fontSize={10} tickLine={false} />
                <YAxis stroke="#10b981" fontSize={10} domain={[80, 100]} tickLine={false} unit=" %" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#080d1a', borderColor: '#1e293b', borderRadius: '8px', fontSize: '11px', fontFamily: 'monospace' }}
                  labelStyle={{ color: '#94a3b8' }}
                />
                <ReferenceLine y={90} stroke="#ef4444" strokeDasharray="3 3" label={{ value: 'Hypoxia Threshold (90%)', fill: '#ef4444', fontSize: 10 }} />
                <ReferenceLine y={95} stroke="#f59e0b" strokeDasharray="3 3" label={{ value: 'Nominal Lower (95%)', fill: '#f59e0b', fontSize: 10 }} />
                <Line type="monotone" dataKey="spo2" name="Blood Oxygen (SpO2)" stroke="#10b981" strokeWidth={2.5} dot={false} isAnimationActive={false} />
              </LineChart>
            ) : activeChart === 'temp' ? (
              <LineChart data={formattedData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" opacity={0.6} />
                <XAxis dataKey="timeLabel" stroke="#64748b" fontSize={10} tickLine={false} />
                <YAxis stroke="#f97316" fontSize={10} domain={[35.0, 39.5]} tickLine={false} unit=" °C" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#080d1a', borderColor: '#1e293b', borderRadius: '8px', fontSize: '11px', fontFamily: 'monospace' }}
                  labelStyle={{ color: '#94a3b8' }}
                />
                <ReferenceLine y={38.0} stroke="#ef4444" strokeDasharray="3 3" label={{ value: 'Fever Threshold (38.0°C)', fill: '#ef4444', fontSize: 10 }} />
                <Line type="monotone" dataKey="body_temp" name="Core Body Temp (°C)" stroke="#f97316" strokeWidth={2} dot={false} isAnimationActive={false} />
              </LineChart>
            ) : (
              <LineChart data={formattedData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" opacity={0.6} />
                <XAxis dataKey="timeLabel" stroke="#64748b" fontSize={10} tickLine={false} />
                <YAxis stroke="#38bdf8" fontSize={10} domain={[0, 2.5]} tickLine={false} unit=" g" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#080d1a', borderColor: '#1e293b', borderRadius: '8px', fontSize: '11px', fontFamily: 'monospace' }}
                  labelStyle={{ color: '#94a3b8' }}
                />
                <Line type="monotone" dataKey="motion_magnitude" name="Total Acceleration (g)" stroke="#38bdf8" strokeWidth={2} dot={false} isAnimationActive={false} />
                <Line type="monotone" dataKey="motion_z" name="Z-Axis (g)" stroke="#64748b" strokeWidth={1} strokeDasharray="2 2" dot={false} isAnimationActive={false} />
              </LineChart>
            )}
          </ResponsiveContainer>
        )}
      </div>

      {/* Footer Legend / Quality metric */}
      <div className="mt-4 pt-3 border-t border-space-800 flex items-center justify-between text-[11px] text-slate-400 font-mono">
        <div className="flex items-center space-x-4">
          <span className="flex items-center space-x-1.5">
            <span className="w-2 h-2 rounded-full bg-cyan-400"></span>
            <span>Live Hardware Sync</span>
          </span>
          <span className="flex items-center space-x-1.5">
            <span className="w-2 h-2 rounded-full bg-violet-400"></span>
            <span>Autonomous Calibration</span>
          </span>
        </div>
        <div>
          <span>Samples in View: {formattedData.length}</span>
        </div>
      </div>
    </div>
  );
};

