import React, { useState, useEffect } from 'react';
import {
  Heart,
  Activity,
  Droplets,
  Thermometer,
  Zap,
  Moon,
  Smile,
  ShieldCheck,
  AlertTriangle,
  Radio,
  Wifi,
  Brain,
  Clock,
  Compass,
  CheckCircle2,
  RefreshCw,
  ChevronDown,
  UserCheck
} from 'lucide-react';
import { Astronaut, SensorReading, HealthAlert, EnvironmentalReading } from '../types';
import { TelemetryCard } from '../components/TelemetryCard';
import { BiometricCharts } from '../components/BiometricCharts';
import { telemetryApi, astronautApi, alertsApi } from '../services/api';

interface AstronautDashboardProps {
  astronautId: string;
  onEmergencyClick: () => void;
  onAstronautChange?: (astronautId: string) => void;
}

export const AstronautDashboard: React.FC<AstronautDashboardProps> = ({
  astronautId,
  onEmergencyClick,
  onAstronautChange
}) => {
  const [profile, setProfile] = useState<Astronaut | null>(null);
  const [astronautsList, setAstronautsList] = useState<Astronaut[]>([]);
  const [latestReading, setLatestReading] = useState<SensorReading | null>(null);
  const [history, setHistory] = useState<SensorReading[]>([]);
  const [activeAlerts, setActiveAlerts] = useState<HealthAlert[]>([]);
  const [envReading, setEnvReading] = useState<EnvironmentalReading | null>(null);
  const [loading, setLoading] = useState(true);
  const [wsConnected, setWsConnected] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const [crewSelectorOpen, setCrewSelectorOpen] = useState(false);

  // Fetch astronaut profile and initial telemetry
  const fetchData = async () => {
    try {
      const [astro, reading, hist, envList, allAstros, alertsList] = await Promise.all([
        astronautApi.getAstronautById(astronautId).catch(() => null),
        telemetryApi.getLatestBiometrics(astronautId).catch(() => null),
        telemetryApi.getBiometricHistory(astronautId, 45).catch(() => []),
        telemetryApi.getLatestEnvironmental().catch(() => []),
        astronautApi.getAstronauts().catch(() => []),
        alertsApi.getActiveAlerts().catch(() => [])
      ]);

      if (astro) setProfile(astro);
      if (allAstros && allAstros.length > 0) setAstronautsList(allAstros);
      if (reading) setLatestReading(reading);
      if (hist && hist.length > 0) setHistory(hist);
      if (envList && envList.length > 0) setEnvReading(envList[0]);
      if (alertsList) {
        const astroAlerts = alertsList.filter(
          (a) => a.astronaut_id === astronautId || a.category === 'emergency'
        );
        setActiveAlerts(astroAlerts);
      }
      setLastUpdated(new Date());
    } catch (err) {
      console.error('Error fetching dashboard telemetry:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();

    // WebSocket real-time connection for sub-second telemetry
    let ws: WebSocket | null = null;
    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/telemetry`;
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setWsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'biometric_telemetry' && msg.astronaut_id === astronautId) {
            setLatestReading(msg.data);
            setHistory((prev) => {
              const updated = [...prev, msg.data];
              return updated.slice(-50); // Keep last 50 points
            });
            setLastUpdated(new Date());
          } else if (msg.type === 'health_alert') {
            setActiveAlerts((prev) => [msg.alert, ...prev.filter(a => a.id !== msg.alert.id)]);
          } else if (msg.type === 'environmental_telemetry') {
            setEnvReading(msg.data);
          }
        } catch (e) {
          // Non-JSON ping/pong
        }
      };

      ws.onclose = () => setWsConnected(false);
      ws.onerror = () => setWsConnected(false);
    } catch (e) {
      setWsConnected(false);
    }

    // Polling fallback every 3 seconds to guarantee updates even if WS is closed
    const interval = setInterval(fetchData, 3000);

    return () => {
      clearInterval(interval);
      if (ws) ws.close();
    };
  }, [astronautId]);

  if (loading && !latestReading) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center space-y-3">
        <RefreshCw className="w-8 h-8 text-cyan-400 animate-spin" />
        <p className="font-mono text-sm text-slate-400">Acquiring Deep Space Telemetry Stream...</p>
      </div>
    );
  }

  // Determine vital status
  const getVitalStatus = (type: 'hr' | 'spo2' | 'temp') => {
    if (!latestReading) return 'nominal';
    if (type === 'spo2') {
      if (latestReading.spo2 < 88.0) return 'emergency';
      if (latestReading.spo2 < 93.0) return 'urgent';
      if (latestReading.spo2 < 96.0) return 'attention';
      return 'nominal';
    }
    if (type === 'hr') {
      if (latestReading.heart_rate > 130 || latestReading.heart_rate < 40) return 'emergency';
      if (latestReading.heart_rate > 105 || latestReading.heart_rate < 50) return 'urgent';
      return 'nominal';
    }
    if (type === 'temp') {
      if (latestReading.body_temp > 38.6 || latestReading.body_temp < 35.0) return 'urgent';
      return 'nominal';
    }
    return 'nominal';
  };

  const hrStatus = getVitalStatus('hr');
  const spo2Status = getVitalStatus('spo2');
  const tempStatus = getVitalStatus('temp');

  const activeEmergency = activeAlerts.find(a => a.category === 'emergency');
  const activeUrgent = activeAlerts.find(a => a.category === 'urgent_assessment');

  return (
    <div className="space-y-6 pb-12">
      {/* Top Banner / Mission Context */}
      <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 p-5 rounded-2xl bg-space-900/90 border border-space-800 shadow-panel backdrop-blur-md">
        <div className="flex items-center space-x-4">
          <div className="relative">
            <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-cyan-600 to-space-800 border border-cyan-500/30 flex items-center justify-center text-lg font-bold text-white shadow-cyan-glow">
              {profile?.full_name ? profile.full_name.split(' ').map(n=>n[0]).join('') : 'AN'}
            </div>
            <span className={`absolute -bottom-1 -right-1 w-4 h-4 rounded-full border-2 border-space-900 ${
              wsConnected ? 'bg-emerald-400 telemetry-pulse' : 'bg-amber-400'
            }`} title={wsConnected ? 'Live WebSocket Connected' : 'Polling Sync Mode'} />
          </div>

          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-bold text-white tracking-wide">
                {profile?.full_name || 'Cmdr. Alex Novak'}
              </h1>
              
              {/* Crew Member Quick Selector */}
              {astronautsList.length > 1 && onAstronautChange && (
                <div className="relative">
                  <button
                    onClick={() => setCrewSelectorOpen(!crewSelectorOpen)}
                    className="p-1 rounded bg-space-800 hover:bg-space-700 text-cyan-400 border border-space-700 flex items-center"
                    title="Switch Active Astronaut"
                  >
                    <ChevronDown className="w-3.5 h-3.5" />
                  </button>
                  {crewSelectorOpen && (
                    <div className="absolute left-0 mt-1 w-56 rounded-lg bg-space-900 border border-space-700 shadow-panel py-1.5 z-40 text-xs">
                      <div className="px-3 py-1 text-[10px] text-slate-400 font-mono uppercase">
                        Select Crew Subject:
                      </div>
                      {astronautsList.map((a) => (
                        <button
                          key={a.astronaut_id}
                          onClick={() => {
                            onAstronautChange(a.astronaut_id);
                            setCrewSelectorOpen(false);
                          }}
                          className={`w-full text-left px-3 py-1.5 flex items-center justify-between hover:bg-space-800 ${
                            a.astronaut_id === astronautId ? 'text-cyan-400 font-bold bg-space-850' : 'text-slate-300'
                          }`}
                        >
                          <span>{a.full_name}</span>
                          <span className="font-mono text-[10px] text-slate-400">{a.astronaut_id}</span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}

              <span className="text-xs font-mono uppercase px-2 py-0.5 rounded bg-space-800 text-cyan-400 border border-cyan-800/40">
                {profile?.astronaut_id || astronautId}
              </span>
              <span className="text-xs font-mono uppercase px-2 py-0.5 rounded bg-emerald-950/60 text-emerald-400 border border-emerald-800/40 hidden sm:inline">
                {profile?.medical_clearance_status || 'FIT FOR MISSION'}
              </span>
            </div>
            <p className="text-xs text-slate-400 font-mono mt-0.5">
              Role: <span className="text-slate-200">{profile?.role_description || 'Commander & Navigation Specialist'}</span> • Mission: <span className="text-cyan-400">ARES-V Deep Space</span>
            </p>
          </div>
        </div>

        {/* Telemetry Status Indicators */}
        <div className="flex items-center space-x-4 text-xs font-mono">
          <div className="p-2 px-3 rounded-lg bg-space-950 border border-space-800 text-slate-300">
            <span className="text-slate-500 block text-[10px]">DEVICE NODE:</span>
            <span className="text-cyan-400 font-bold flex items-center space-x-1.5">
              <Wifi className="w-3.5 h-3.5 text-cyan-400" />
              <span>BioBand Mk-IV (Online)</span>
            </span>
          </div>

          <div className="p-2 px-3 rounded-lg bg-space-950 border border-space-800 text-slate-300">
            <span className="text-slate-500 block text-[10px]">DATA STREAM:</span>
            <span className="text-emerald-400 font-bold flex items-center space-x-1.5">
              <Radio className="w-3.5 h-3.5 animate-pulse" />
              <span>{latestReading?.is_simulated ? 'Simulated Hardware' : 'Live Sensor Feed'}</span>
            </span>
          </div>
        </div>
      </div>

      {/* Emergency / Urgent Active Alert Warning Bar if triggered */}
      {(spo2Status === 'emergency' || activeEmergency || activeUrgent) && (
        <div className={`p-4 rounded-xl border flex items-center justify-between animate-pulse ${
          activeEmergency || spo2Status === 'emergency'
            ? 'bg-red-950/60 border-red-500/70 shadow-alert-glow text-red-200'
            : 'bg-amber-950/60 border-amber-500/70 shadow-panel text-amber-200'
        }`}>
          <div className="flex items-center space-x-3">
            <AlertTriangle className={`w-6 h-6 flex-shrink-0 ${
              activeEmergency || spo2Status === 'emergency' ? 'text-red-400' : 'text-amber-400'
            }`} />
            <div>
              <p className="font-bold text-sm tracking-wide">
                {activeEmergency?.title || (spo2Status === 'emergency' ? 'CRITICAL MEDICAL ALERT: ACUTE HYPOXIA DETECTED' : activeUrgent?.title || 'HEALTH ALERT ACTIVE')}
              </p>
              <p className="text-xs font-mono opacity-90">
                {activeEmergency?.message || (spo2Status === 'emergency' ? 'SpO2 dropped below 88.0%. Medical Officer informed. Supplemental O2 protocol advised.' : activeUrgent?.message || 'Biometric parameters deviate from individual baseline.')}
              </p>
            </div>
          </div>
          <button 
            onClick={onEmergencyClick}
            className="px-3 py-1.5 rounded bg-red-600 hover:bg-red-500 text-white font-mono text-xs font-bold flex-shrink-0 ml-3 shadow-alert-glow"
          >
            CONFIRM SOS
          </button>
        </div>
      )}

      {/* Primary Biometrics Telemetry Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Heart Rate */}
        <TelemetryCard
          title="Heart Rate"
          value={latestReading?.heart_rate != null ? latestReading.heart_rate.toFixed(0) : '--'}
          unit="BPM"
          icon={Heart}
          status={hrStatus}
          baseline={`${profile?.baseline_vitals?.resting_heart_rate != null ? profile.baseline_vitals.resting_heart_rate.toFixed(0) : '62'} bpm`}
          subtext="MAX30102 Optical PPG"
          quality={latestReading?.measurement_quality}
          isSimulated={latestReading?.is_simulated}
        />

        {/* Blood Oxygen SpO2 */}
        <TelemetryCard
          title="Blood Oxygen (SpO2)"
          value={latestReading?.spo2 != null ? latestReading.spo2.toFixed(1) : '--'}
          unit="%"
          icon={Droplets}
          status={spo2Status}
          baseline={`${profile?.baseline_vitals?.baseline_spo2 != null ? profile.baseline_vitals.baseline_spo2.toFixed(1) : '98.4'}%`}
          subtext="Dual-Wavelength Pulse Oximetry"
          quality={latestReading?.measurement_quality}
          isSimulated={latestReading?.is_simulated}
        />

        {/* Heart Rate Variability */}
        <TelemetryCard
          title="HRV (RMSSD)"
          value={latestReading?.hrv != null ? latestReading.hrv.toFixed(0) : '--'}
          unit="MS"
          icon={Activity}
          status={latestReading && latestReading.hrv < 30 ? 'urgent' : 'nominal'}
          baseline={`${profile?.baseline_vitals?.resting_hrv != null ? profile.baseline_vitals.resting_hrv.toFixed(0) : '72'} ms`}
          subtext="Autonomic Parasympathetic Index"
          quality={latestReading?.measurement_quality}
          isSimulated={latestReading?.is_simulated}
        />

        {/* Core Body Temperature */}
        <TelemetryCard
          title="Core Body Temp"
          value={latestReading?.body_temp != null ? latestReading.body_temp.toFixed(2) : '--'}
          unit="°C"
          icon={Thermometer}
          status={tempStatus}
          baseline={`${profile?.baseline_vitals?.baseline_body_temp != null ? profile.baseline_vitals.baseline_body_temp.toFixed(1) : '36.7'}°C`}
          subtext={latestReading?.temp_measurement_type ? latestReading.temp_measurement_type.replace('_', ' ') : 'DS18B20 Core Probe'}
          quality={latestReading?.measurement_quality}
          isSimulated={latestReading?.is_simulated}
        />
      </div>

      {/* Secondary Row: IMU Activity, Sleep, Stress & Environment */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Physical Activity (MPU6050) */}
        <div className="rounded-xl border border-space-800 bg-space-900/60 p-4 backdrop-blur-md">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Physical Activity</span>
            <Zap className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-2xl font-bold font-mono text-white capitalize">
              {latestReading?.activity_level || 'Rest'}
            </span>
          </div>
          <div className="mt-2 text-[11px] font-mono text-slate-400 flex justify-between">
            <span>Acc: {latestReading?.motion_magnitude != null ? latestReading.motion_magnitude.toFixed(2) : '0.98'}g</span>
            <span className="text-cyan-400 font-semibold">MPU6050 6-Axis</span>
          </div>
        </div>

        {/* Sleep Duration */}
        <div className="rounded-xl border border-space-800 bg-space-900/60 p-4 backdrop-blur-md">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Sleep Duration</span>
            <Moon className="w-4 h-4 text-violet-400" />
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-2xl font-bold font-mono text-white">7.4</span>
            <span className="text-xs font-mono text-slate-400">HRS / 24H</span>
          </div>
          <div className="mt-2 text-[11px] font-mono text-slate-400 flex justify-between">
            <span>Quality: <span className="text-emerald-400">88%</span></span>
            <span className="text-violet-400">REM: 1.8h</span>
          </div>
        </div>

        {/* Self-Reported Stress */}
        <div className="rounded-xl border border-space-800 bg-space-900/60 p-4 backdrop-blur-md">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Stress Score</span>
            <Smile className="w-4 h-4 text-amber-400" />
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-2xl font-bold font-mono text-white">4</span>
            <span className="text-xs font-mono text-slate-400">/ 10 (MILD)</span>
          </div>
          <div className="mt-2 text-[11px] font-mono text-slate-400 flex justify-between">
            <span>Workload: Nominal</span>
            <span className="text-emerald-400">Coping: Good</span>
          </div>
        </div>

        {/* Radiation Exposure */}
        <div className="rounded-xl border border-space-800 bg-space-900/60 p-4 backdrop-blur-md">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Space Radiation</span>
            <Radio className="w-4 h-4 text-amber-400" />
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-2xl font-bold font-mono text-white">
              {envReading?.radiation_dose_rate_uSv_h != null ? envReading.radiation_dose_rate_uSv_h.toFixed(1) : '21.8'}
            </span>
            <span className="text-xs font-mono text-slate-400">µSV/H</span>
          </div>
          <div className="mt-2 text-[11px] font-mono text-slate-400 flex justify-between">
            <span>Cumul: {envReading?.radiation_cumulative_mSv != null ? envReading.radiation_cumulative_mSv.toFixed(2) : '43.15'} mSv</span>
            <span className="text-emerald-400">Sub-Limit</span>
          </div>
        </div>
      </div>

      {/* Main Interactive Recharts Telemetry Section */}
      <BiometricCharts
        data={history}
        astronautName={profile?.full_name || 'Cmdr. Alex Novak'}
      />

      {/* Daily Health Summary & AI Observations */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Daily Summary */}
        <div className="rounded-xl border border-space-800 bg-space-900/70 p-5 backdrop-blur-md">
          <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-3 flex items-center space-x-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>Daily Health Clearance Summary</span>
          </h3>
          <div className="space-y-3 text-xs font-mono text-slate-300">
            <div className="flex justify-between pb-2 border-b border-space-800">
              <span className="text-slate-400">Cardiovascular Fitness:</span>
              <span className="text-emerald-400 font-bold">OPTIMAL (94/100)</span>
            </div>
            <div className="flex justify-between pb-2 border-b border-space-800">
              <span className="text-slate-400">Exercise Countermeasure:</span>
              <span className="text-cyan-400 font-bold">COMPLETED (60 min)</span>
            </div>
            <div className="flex justify-between pb-2 border-b border-space-800">
              <span className="text-slate-400">Hydration Equilibrium:</span>
              <span className="text-slate-200">Balanced (2.4L est.)</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Orthostatic Tolerance:</span>
              <span className="text-emerald-400 font-bold">STABLE</span>
            </div>
          </div>
        </div>

        {/* AI Health Analytics Observation */}
        <div className="rounded-xl border border-space-800 bg-space-900/70 p-5 backdrop-blur-md lg:col-span-2">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center space-x-2">
              <Brain className="w-4 h-4 text-cyan-400" />
              <span>AI Autonomous Medical Intelligence (Observation)</span>
            </h3>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800">
              Isolation Forest v1.2
            </span>
          </div>

          <div className="p-3.5 rounded-lg bg-space-950/80 border border-space-800 space-y-2 text-xs font-mono">
            <p className="text-slate-200 leading-relaxed">
              <strong className="text-cyan-300">Physiological Baseline Analysis: </strong> 
              {spo2Status === 'emergency' 
                ? 'CRITICAL ALERT: Multimodal sensor divergence detected. Pulse oximetry reflects severe hypoxia (<88%) while heart rate displays compensatory tachycardia. Automated oxygenation check recommended.' 
                : hrStatus === 'urgent'
                ? 'ATTENTION: Resting cardiovascular trend elevated by +42 bpm relative to individual circadian baseline. Parasympathetic recovery suppression identified.'
                : 'Current continuous biometric telemetry adheres within 1.2 standard deviations of individual circadian baseline. No persistent cardiovascular or thermoregulatory anomalies detected over the preceding 4 hours.'}
            </p>
            <div className="pt-2 border-t border-space-800/80 flex flex-wrap items-center justify-between text-[11px] text-slate-400">
              <span>Model Confidence: <strong className="text-cyan-400">96.4%</strong></span>
              <span>Baseline Comparison: <strong className="text-emerald-400">Matched</strong></span>
              <span className="text-[10px] text-slate-500 italic">Non-diagnostic experimental flight analytics</span>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};

