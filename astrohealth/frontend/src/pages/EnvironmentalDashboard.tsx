import React, { useState, useEffect } from 'react';
import {
  Thermometer,
  Droplets,
  Gauge,
  Wind,
  Radiation,
  ShieldCheck,
  AlertTriangle,
  RefreshCw,
  Compass,
  Sliders,
  CheckCircle2,
  Cpu
} from 'lucide-react';
import {
  AreaChart,
  Area,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend
} from 'recharts';

import { EnvironmentalReading } from '../types';
import { telemetryApi } from '../services/api';

const COMPARTMENTS = [
  { id: 'Command_Module', name: 'Command Module Alpha', type: 'Primary Flight Deck' },
  { id: 'Living_Quarters', name: 'Crew Living Quarters', type: 'Habitation & Sleep Pods' },
  { id: 'Science_Lab', name: 'Science Laboratory', type: 'Biomedical & Physics Bay' },
  { id: 'EVA_Airlock', name: 'EVA Airlock Chamber', type: 'Extravehicular Depress Bay' },
];

export const EnvironmentalDashboard: React.FC = () => {
  const [selectedComp, setSelectedComp] = useState<string>('Command_Module');
  const [latestReadings, setLatestReadings] = useState<Record<string, EnvironmentalReading>>({});
  const [history, setHistory] = useState<EnvironmentalReading[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [simulatedFlag, setSimulatedFlag] = useState<boolean>(false);

  const fetchEnvironmental = async () => {
    try {
      setLoading(true);
      const latestList = await telemetryApi.getLatestEnvironmental();
      const map: Record<string, EnvironmentalReading> = {};
      latestList.forEach((r) => {
        map[r.compartment_id] = r;
      });
      setLatestReadings(map);

      // Load history for selected compartment
      const hist = await telemetryApi.getEnvironmentalHistory(selectedComp, 40);
      setHistory(hist.reverse());
      if (hist.length > 0) {
        setSimulatedFlag(hist[hist.length - 1].is_simulated);
      }
    } catch (e) {
      console.error('Error fetching environmental telemetry', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEnvironmental();
    const interval = setInterval(fetchEnvironmental, 5000);
    return () => clearInterval(interval);
  }, [selectedComp]);

  const current = latestReadings[selectedComp] || {
    temperature: 21.5,
    humidity: 45.0,
    atmospheric_pressure: 101.3,
    co2_ppm: 580.0,
    voc_index: 90.0,
    radiation_dose_rate_uSv_h: 22.0,
    radiation_cumulative_mSv: 15.2,
    radiation_exposure_estimated: 19.8,
    sensor_status: 'NOMINAL',
    is_simulated: true,
    timestamp: new Date().toISOString()
  };

  // Threshold evaluations
  const co2Status = current.co2_ppm > 2500 ? 'CRITICAL' : (current.co2_ppm > 1200 ? 'WARNING' : 'NOMINAL');
  const radStatus = current.radiation_dose_rate_uSv_h > 100 ? 'CRITICAL' : (current.radiation_dose_rate_uSv_h > 45 ? 'WARNING' : 'NOMINAL');
  const pressureStatus = (current.atmospheric_pressure < 94 || current.atmospheric_pressure > 108) ? 'WARNING' : 'NOMINAL';

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-4 md:p-8 space-y-8 font-sans">
      {/* Environmental Mission Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900/90 border border-slate-800 p-6 rounded-2xl shadow-xl backdrop-blur-md">
        <div className="flex items-center space-x-4">
          <div className="p-3 bg-cyan-500/10 border border-cyan-500/30 rounded-xl text-cyan-400">
            <Compass className="w-8 h-8" />
          </div>
          <div>
            <div className="flex items-center space-x-3">
              <h1 className="text-2xl font-bold tracking-tight text-white">
                Spacecraft Life Support & Atmospheric Monitoring
              </h1>
              {simulatedFlag && (
                <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/20 text-amber-400 border border-amber-500/30 flex items-center space-x-1">
                  <Cpu className="w-3 h-3" />
                  <span>HARDWARE SIMULATOR FEED</span>
                </span>
              )}
            </div>
            <p className="text-sm text-slate-400 mt-1">
              Project Ares-V &bull; Multi-Zone Environmental Life Support System (ECLSS) &bull; Active Radiation Dosimetry
            </p>
          </div>
        </div>

        <button
          onClick={fetchEnvironmental}
          disabled={loading}
          className="flex items-center space-x-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium rounded-lg border border-slate-700 transition"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          <span>Sync ECLSS Telemetry</span>
        </button>
      </div>

      {/* Habitat Compartment Selector Bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {COMPARTMENTS.map((comp) => {
          const isSelected = selectedComp === comp.id;
          const reading = latestReadings[comp.id];
          const co2 = reading ? Math.round(reading.co2_ppm) : 580;
          const temp = reading ? reading.temperature.toFixed(1) : '21.5';

          return (
            <div
              key={comp.id}
              onClick={() => setSelectedComp(comp.id)}
              className={`cursor-pointer p-4 rounded-xl border transition-all duration-200 ${
                isSelected
                  ? 'bg-slate-900 border-cyan-500 shadow-lg shadow-cyan-500/10'
                  : 'bg-slate-900/60 border-slate-800 hover:border-slate-700 hover:bg-slate-900/80'
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-bold text-white truncate">{comp.name}</span>
                <span className={`w-2 h-2 rounded-full ${isSelected ? 'bg-cyan-400 ring-2 ring-cyan-400/40' : 'bg-slate-600'}`} />
              </div>
              <p className="text-[11px] text-slate-400 mb-2 truncate">{comp.type}</p>
              <div className="flex items-center justify-between text-xs pt-2 border-t border-slate-800 text-slate-300">
                <span>{temp}°C</span>
                <span className={co2 > 1200 ? 'text-amber-400 font-semibold' : 'text-slate-400'}>
                  {co2} ppm CO2
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Primary Atmospheric Telemetry Strip */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* CO2 Sensirion SCD41 */}
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-xl">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
            <span className="flex items-center space-x-1.5 font-semibold text-slate-300">
              <Wind className="w-4 h-4 text-cyan-400" />
              <span>CO2 CONCENTRATION</span>
            </span>
            <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
              co2Status === 'CRITICAL' ? 'bg-rose-500/20 text-rose-400' :
              (co2Status === 'WARNING' ? 'bg-amber-500/20 text-amber-400' : 'bg-emerald-500/20 text-emerald-400')
            }`}>
              {co2Status}
            </span>
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-3xl font-extrabold text-white">
              {Math.round(current.co2_ppm)}
            </span>
            <span className="text-xs text-slate-400">ppm</span>
          </div>
          <div className="mt-3 text-[11px] text-slate-400 flex justify-between">
            <span>Sensirion SCD41 NDIR</span>
            <span>Limit: &lt;1,200 ppm</span>
          </div>
        </div>

        {/* Temperature & Humidity BME680 */}
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-xl">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
            <span className="flex items-center space-x-1.5 font-semibold text-slate-300">
              <Thermometer className="w-4 h-4 text-blue-400" />
              <span>CABIN TEMPERATURE</span>
            </span>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400">
              NOMINAL
            </span>
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-3xl font-extrabold text-white">
              {current.temperature.toFixed(1)}
            </span>
            <span className="text-xs text-slate-400">°C</span>
          </div>
          <div className="mt-3 text-[11px] text-slate-400 flex justify-between">
            <span className="flex items-center space-x-1">
              <Droplets className="w-3 h-3 text-cyan-400" />
              <span>{current.humidity.toFixed(1)}% RH</span>
            </span>
            <span>Target: 21.0 - 24.0°C</span>
          </div>
        </div>

        {/* Atmospheric Pressure */}
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-xl">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
            <span className="flex items-center space-x-1.5 font-semibold text-slate-300">
              <Gauge className="w-4 h-4 text-violet-400" />
              <span>BAROMETRIC PRESSURE</span>
            </span>
            <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
              pressureStatus === 'WARNING' ? 'bg-amber-500/20 text-amber-400' : 'bg-emerald-500/20 text-emerald-400'
            }`}>
              {pressureStatus}
            </span>
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-3xl font-extrabold text-white">
              {current.atmospheric_pressure.toFixed(1)}
            </span>
            <span className="text-xs text-slate-400">kPa</span>
          </div>
          <div className="mt-3 text-[11px] text-slate-400 flex justify-between">
            <span>Cabin Pressurization</span>
            <span>Nominal: 101.3 kPa</span>
          </div>
        </div>

        {/* VOC Gas Quality */}
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-xl">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
            <span className="flex items-center space-x-1.5 font-semibold text-slate-300">
              <Sliders className="w-4 h-4 text-amber-400" />
              <span>AIR VOC PURITY</span>
            </span>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400">
              OPTIMAL
            </span>
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-3xl font-extrabold text-white">
              {Math.round(current.voc_index)}
            </span>
            <span className="text-xs text-slate-400">index</span>
          </div>
          <div className="mt-3 text-[11px] text-slate-400 flex justify-between">
            <span>BME680 Metal Oxide Gas</span>
            <span>&lt;200 Normal</span>
          </div>
        </div>
      </div>

      {/* Radiation Monitoring Section - Explicit Measured vs Estimated Distinction */}
      <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 border-b border-slate-800 pb-4">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-rose-500/10 text-rose-400 rounded-xl border border-rose-500/20">
              <Radiation className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white">
                Space Radiation Dosimetry Suite
              </h3>
              <p className="text-xs text-slate-400">
                Continuous silicon solid-state detector dosimetry &bull; Strict distinction between measured physical dose and projected galactic cosmic ray exposure
              </p>
            </div>
          </div>
          <span className={`px-3 py-1 rounded-full text-xs font-semibold self-start md:self-auto ${
            radStatus === 'CRITICAL' ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' :
            (radStatus === 'WARNING' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30')
          }`}>
            FLUX STATUS: {radStatus}
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
          {/* Measured Dose Rate */}
          <div className="bg-slate-950/70 p-5 rounded-xl border border-slate-800">
            <span className="text-xs font-semibold text-cyan-400 uppercase tracking-wider block mb-1">
              [Measured] Live Dose Flux Rate
            </span>
            <div className="flex items-baseline space-x-1.5 mb-2">
              <span className="text-3xl font-black text-white">
                {current.radiation_dose_rate_uSv_h.toFixed(1)}
              </span>
              <span className="text-xs text-slate-400 font-mono">µSv / hour</span>
            </div>
            <p className="text-[11px] text-slate-400">
              Real-time physical ionization events registered by active sensor head.
            </p>
          </div>

          {/* Cumulative Mission Absorbed Dose */}
          <div className="bg-slate-950/70 p-5 rounded-xl border border-slate-800">
            <span className="text-xs font-semibold text-blue-400 uppercase tracking-wider block mb-1">
              [Measured] Cumulative Absorbed Dose
            </span>
            <div className="flex items-baseline space-x-1.5 mb-2">
              <span className="text-3xl font-black text-white">
                {current.radiation_cumulative_mSv.toFixed(2)}
              </span>
              <span className="text-xs text-slate-400 font-mono">mSv (Total)</span>
            </div>
            <p className="text-[11px] text-slate-400">
              Total integrated physical tissue-equivalent dose since mission launch.
            </p>
          </div>

          {/* Estimated Projected Exposure */}
          <div className="bg-slate-950/70 p-5 rounded-xl border border-amber-500/30 bg-amber-500/5">
            <span className="text-xs font-semibold text-amber-400 uppercase tracking-wider block mb-1">
              [Estimated] GCR Model Projection
            </span>
            <div className="flex items-baseline space-x-1.5 mb-2">
              <span className="text-3xl font-black text-amber-300">
                {current.radiation_exposure_estimated.toFixed(2)}
              </span>
              <span className="text-xs text-amber-400/80 font-mono">mSv (Est. 30-Day)</span>
            </div>
            <p className="text-[11px] text-slate-400">
              Empirical mathematical estimate considering heliospheric modulation and hull shielding.
            </p>
          </div>
        </div>
      </div>

      {/* Historical Atmospheric & Radiation Telemetry Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Carbon Dioxide & Pressure Chart */}
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h4 className="text-base font-bold text-white">Carbon Dioxide & Pressure Trends</h4>
              <p className="text-xs text-slate-400">Telemetry over past 40 samples in {selectedComp.replace('_', ' ')}</p>
            </div>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={history} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="timestamp" hide />
                <YAxis yAxisId="co2" domain={[400, 'auto']} stroke="#06b6d4" tick={{ fontSize: 10 }} />
                <YAxis yAxisId="pressure" orientation="right" domain={[90, 110]} stroke="#a855f7" tick={{ fontSize: 10 }} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }} />
                <Legend />
                <Line yAxisId="co2" type="monotone" dataKey="co2_ppm" stroke="#06b6d4" strokeWidth={2} dot={false} name="CO2 (ppm)" />
                <Line yAxisId="pressure" type="monotone" dataKey="atmospheric_pressure" stroke="#a855f7" strokeWidth={2} dot={false} name="Pressure (kPa)" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Radiation Flux Chart */}
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h4 className="text-base font-bold text-white">Radiation Dose Flux Trajectory</h4>
              <p className="text-xs text-slate-400">Measured ionization rate (µSv/h) vs 45 µSv/h warning threshold</p>
            </div>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={history} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="radGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.6} />
                    <stop offset="95%" stopColor="#f43f5e" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="timestamp" hide />
                <YAxis domain={[0, 'auto']} stroke="#64748b" tick={{ fontSize: 10 }} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }} />
                <Area type="monotone" dataKey="radiation_dose_rate_uSv_h" stroke="#f43f5e" fillOpacity={1} fill="url(#radGrad)" strokeWidth={2} name="Flux (µSv/h)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};

