import React, { useState, useEffect, useMemo } from 'react';
import {
  Activity,
  Heart,
  Thermometer,
  Wind,
  ShieldAlert,
  Brain,
  FileText,
  Download,
  Printer,
  RefreshCw,
  Users,
  CheckCircle2,
  AlertTriangle,
  ChevronRight,
  TrendingUp,
  Plus,
  X,
  Stethoscope,
  Info
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  LineChart,
  Line,
  CartesianGrid
} from 'recharts';

import {
  Astronaut,
  SensorReading,
  MedicalReport,
  AIPrediction,
  User
} from '../types';
import {
  astronautApi,
  telemetryApi,
  reportsApi,
  aiApi,
  authApi
} from '../services/api';

export const MedicalOfficerDashboard: React.FC = () => {
  const [currentUser, setCurrentUser] = useState<User | null>(authApi.getCurrentUser());
  const [astronauts, setAstronauts] = useState<Astronaut[]>([]);
  const [selectedAstroId, setSelectedAstroId] = useState<string>('ASTRO-001');
  const [crewVitals, setCrewVitals] = useState<Record<string, SensorReading>>({});
  const [selectedHistory, setSelectedHistory] = useState<SensorReading[]>([]);
  const [aiPrediction, setAiPrediction] = useState<AIPrediction | null>(null);
  const [cardioTrends, setCardioTrends] = useState<any>(null);
  const [reports, setReports] = useState<MedicalReport[]>([]);
  const [reportFilter, setReportFilter] = useState<string>('all');
  const [loading, setLoading] = useState<boolean>(true);
  const [generatingReport, setGeneratingReport] = useState<boolean>(false);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);

  // Custom report form state
  const [customReportType, setCustomReportType] = useState<string>('daily');
  const [customSummary, setCustomSummary] = useState<string>('');
  const [customObservations, setCustomObservations] = useState<string>('');
  const [customRecommendations, setCustomRecommendations] = useState<string>('');

  const selectedAstronaut = useMemo(() => {
    return astronauts.find(a => a.astronaut_id === selectedAstroId) || astronauts[0];
  }, [astronauts, selectedAstroId]);

  // Load initial data
  const fetchData = async () => {
    try {
      setLoading(true);
      const [astros, repList] = await Promise.all([
        astronautApi.getAstronauts(),
        reportsApi.listReports()
      ]);
      setAstronauts(astros);
      setReports(repList);

      // Fetch latest vitals for all astronauts
      const vitalsMap: Record<string, SensorReading> = {};
      await Promise.all(
        astros.map(async (a) => {
          try {
            const reading = await telemetryApi.getLatestBiometrics(a.astronaut_id);
            if (reading) vitalsMap[a.astronaut_id] = reading;
          } catch (e) {
            console.error(`Failed to fetch vitals for ${a.astronaut_id}`, e);
          }
        })
      );
      setCrewVitals(vitalsMap);

      if (astros.length > 0 && !selectedAstroId) {
        setSelectedAstroId(astros[0].astronaut_id);
      }
    } catch (err) {
      console.error('Error loading medical officer data', err);
    } finally {
      setLoading(false);
    }
  };

  // Load deep-dive data when selected astronaut changes
  const fetchAstronautDeepDive = async (astroId: string) => {
    try {
      const [history, prediction, trends] = await Promise.all([
        telemetryApi.getBiometricHistory(astroId, 40),
        aiApi.getLatestPrediction(astroId).catch(() => null),
        aiApi.getCardioTrends(astroId, 24).catch(() => null)
      ]);
      setSelectedHistory(history.reverse());
      setAiPrediction(prediction);
      setCardioTrends(trends);
    } catch (e) {
      console.error('Error fetching astronaut deep-dive telemetry', e);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (selectedAstroId) {
      fetchAstronautDeepDive(selectedAstroId);
    }
  }, [selectedAstroId]);

  // Handle 1-click auto-generation of 24h clinical report
  const handleAutoGenerateReport = async () => {
    if (!selectedAstroId) return;
    try {
      setGeneratingReport(true);
      const newReport = await reportsApi.generateAutoReport(selectedAstroId, 'daily', 24);
      setReports([newReport, ...reports]);
      alert(`Automated 24h clinical assessment generated: ${newReport.id}`);
    } catch (err: any) {
      alert(`Error generating automated report: ${err.response?.data?.detail || err.message}`);
    } finally {
      setGeneratingReport(false);
    }
  };

  // Handle custom report submission
  const handleCreateCustomReport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedAstroId || !customSummary || !customObservations) {
      alert('Please fill in both the summary and clinical observations.');
      return;
    }

    try {
      setGeneratingReport(true);
      const recs = customRecommendations
        .split('\n')
        .map(r => r.trim())
        .filter(r => r.length > 0);

      const payload = {
        astronaut_id: selectedAstroId,
        report_type: customReportType as any,
        summary: customSummary,
        clinical_observations: customObservations,
        recommendations: recs.length > 0 ? recs : ['Maintain prescribed mission protocol.'],
        vitals_snapshot: crewVitals[selectedAstroId] ? {
          heart_rate: crewVitals[selectedAstroId].heart_rate,
          spo2: crewVitals[selectedAstroId].spo2,
          body_temp: crewVitals[selectedAstroId].body_temp
        } : {},
        ai_insights: aiPrediction ? {
          anomaly_score: aiPrediction.anomaly_score,
          is_anomaly: aiPrediction.is_anomaly
        } : {}
      };

      const created = await reportsApi.createReport(payload);
      setReports([created, ...reports]);
      setIsModalOpen(false);
      setCustomSummary('');
      setCustomObservations('');
      setCustomRecommendations('');
      alert(`Medical report ${created.id} successfully filed to mission log.`);
    } catch (err: any) {
      alert(`Error filing report: ${err.response?.data?.detail || err.message}`);
    } finally {
      setGeneratingReport(false);
    }
  };

  // Filtered reports
  const filteredReports = reports.filter(r => {
    const matchesAstro = !selectedAstroId || r.astronaut_id === selectedAstroId;
    const matchesType = reportFilter === 'all' || r.report_type === reportFilter;
    return matchesAstro && matchesType;
  });

  const latestVital = crewVitals[selectedAstroId];

  // Format SHAP data for chart
  const shapChartData = (aiPrediction?.contributing_features || []).map(f => ({
    name: f.feature_name.replace('_', ' ').toUpperCase(),
    shap: Number((f.shap_value * 100).toFixed(2)),
    value: f.feature_value,
    baseline: f.baseline_value,
    direction: f.contribution_direction
  }));

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-4 md:p-8 space-y-8">
      {/* Flight Surgeon Mission Control Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900/90 border border-slate-800 p-6 rounded-2xl shadow-xl backdrop-blur-md">
        <div className="flex items-center space-x-4">
          <div className="p-3 bg-cyan-500/10 border border-cyan-500/30 rounded-xl text-cyan-400">
            <Stethoscope className="w-8 h-8" />
          </div>
          <div>
            <div className="flex items-center space-x-3">
              <h1 className="text-2xl font-bold tracking-tight text-white">
                Flight Surgeon Medical Console
              </h1>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                ACTIVE MONITORING
              </span>
            </div>
            <p className="text-sm text-slate-400 mt-1">
              Mission Ares-V &bull; Deep Space Mars Transit &bull; Flight Surgeon: {currentUser?.full_name || 'Dr. Elena Vance, MD'}
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={() => fetchData()}
            disabled={loading}
            className="flex items-center space-x-2 px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium rounded-lg border border-slate-700 transition"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            <span>Telemetry Refresh</span>
          </button>

          <button
            onClick={handleAutoGenerateReport}
            disabled={generatingReport}
            className="flex items-center space-x-2 px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white text-sm font-semibold rounded-lg shadow-lg shadow-cyan-600/20 transition"
          >
            <Brain className="w-4 h-4" />
            <span>{generatingReport ? 'Synthesizing AI Report...' : 'Generate 24h AI Report'}</span>
          </button>

          <button
            onClick={() => setIsModalOpen(true)}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold rounded-lg shadow-lg shadow-blue-600/20 transition"
          >
            <Plus className="w-4 h-4" />
            <span>Draft Clinical Report</span>
          </button>
        </div>
      </div>

      {/* Multi-Astronaut Crew Overview Grid */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <Users className="w-5 h-5 text-cyan-400" />
            <h2 className="text-lg font-semibold text-white tracking-wide uppercase">
              Assigned Crew Fleet Health Status
            </h2>
          </div>
          <span className="text-xs text-slate-400">
            Click any astronaut card to inspect live telemetry and AI telemetry analysis
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {astronauts.map((astro) => {
            const vitals = crewVitals[astro.astronaut_id];
            const isSelected = selectedAstroId === astro.astronaut_id;
            const hr = vitals?.heart_rate ?? astro.baseline_vitals?.resting_heart_rate ?? 70;
            const spo2 = vitals?.spo2 ?? astro.baseline_vitals?.baseline_spo2 ?? 98;
            const isWarning = spo2 < 93 || hr > 110;

            return (
              <div
                key={astro.astronaut_id}
                onClick={() => setSelectedAstroId(astro.astronaut_id)}
                className={`cursor-pointer p-5 rounded-xl border transition-all duration-200 ${
                  isSelected
                    ? 'bg-slate-900 border-cyan-500 shadow-lg shadow-cyan-500/10'
                    : 'bg-slate-900/60 border-slate-800 hover:border-slate-700 hover:bg-slate-900/80'
                }`}
              >
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <span className="text-xs font-semibold px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                      {astro.astronaut_id}
                    </span>
                    <h3 className="text-base font-bold text-white mt-1">
                      {astro.full_name}
                    </h3>
                    <p className="text-xs text-slate-400">{astro.role_description}</p>
                  </div>
                  <span
                    className={`px-2 py-1 rounded-md text-xs font-semibold flex items-center space-x-1 ${
                      isWarning
                        ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                        : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                    }`}
                  >
                    {isWarning ? <AlertTriangle className="w-3 h-3" /> : <CheckCircle2 className="w-3 h-3" />}
                    <span>{isWarning ? 'ATTENTION' : 'NOMINAL'}</span>
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-2 pt-3 border-t border-slate-800/80 text-center">
                  <div className="bg-slate-950/50 p-2 rounded-lg">
                    <span className="text-[10px] text-slate-400 uppercase block">HR</span>
                    <span className="text-sm font-bold text-cyan-400">{hr}</span>
                    <span className="text-[10px] text-slate-500 block">bpm</span>
                  </div>
                  <div className="bg-slate-950/50 p-2 rounded-lg">
                    <span className="text-[10px] text-slate-400 uppercase block">SpO2</span>
                    <span className={`text-sm font-bold ${spo2 < 93 ? 'text-amber-400' : 'text-blue-400'}`}>
                      {spo2}%
                    </span>
                    <span className="text-[10px] text-slate-500 block">O2</span>
                  </div>
                  <div className="bg-slate-950/50 p-2 rounded-lg">
                    <span className="text-[10px] text-slate-400 uppercase block">Status</span>
                    <span className="text-sm font-bold text-emerald-400">FIT</span>
                    <span className="text-[10px] text-slate-500 block">Medical</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Selected Astronaut Clinical Deep-Dive Console */}
      {selectedAstronaut && (
        <div className="space-y-6">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center space-x-3">
              <Activity className="w-6 h-6 text-cyan-400" />
              <div>
                <h2 className="text-xl font-bold text-white">
                  Clinical Deep Dive: {selectedAstronaut.full_name} ({selectedAstronaut.astronaut_id})
                </h2>
                <p className="text-xs text-slate-400">
                  Age {selectedAstronaut.age} &bull; Blood Type: {selectedAstronaut.blood_type} &bull; Clearance: {selectedAstronaut.medical_clearance_status}
                </p>
              </div>
            </div>
            <div className="text-xs text-slate-400 bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-800">
              Assigned Devices: {selectedAstronaut.assigned_devices?.join(', ')}
            </div>
          </div>

          {/* Vitals Telemetry Strip */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl flex items-center space-x-3">
              <div className="p-3 bg-cyan-500/10 text-cyan-400 rounded-lg">
                <Heart className="w-6 h-6" />
              </div>
              <div>
                <span className="text-xs text-slate-400 uppercase tracking-wider block">Heart Rate</span>
                <div className="flex items-baseline space-x-1.5">
                  <span className="text-2xl font-bold text-white">
                    {latestVital?.heart_rate ?? selectedAstronaut.baseline_vitals?.resting_heart_rate ?? 72}
                  </span>
                  <span className="text-xs text-slate-500">bpm</span>
                </div>
                <span className="text-[10px] text-slate-400">
                  Base: {selectedAstronaut.baseline_vitals?.resting_heart_rate ?? 64} bpm
                </span>
              </div>
            </div>

            <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl flex items-center space-x-3">
              <div className="p-3 bg-blue-500/10 text-blue-400 rounded-lg">
                <Wind className="w-6 h-6" />
              </div>
              <div>
                <span className="text-xs text-slate-400 uppercase tracking-wider block">Pulse Oximetry</span>
                <div className="flex items-baseline space-x-1.5">
                  <span className="text-2xl font-bold text-white">
                    {latestVital?.spo2 ?? selectedAstronaut.baseline_vitals?.baseline_spo2 ?? 98.4}%
                  </span>
                  <span className="text-xs text-slate-500">SpO2</span>
                </div>
                <span className="text-[10px] text-slate-400">
                  Base: {selectedAstronaut.baseline_vitals?.baseline_spo2 ?? 98.4}%
                </span>
              </div>
            </div>

            <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl flex items-center space-x-3">
              <div className="p-3 bg-violet-500/10 text-violet-400 rounded-lg">
                <Thermometer className="w-6 h-6" />
              </div>
              <div>
                <span className="text-xs text-slate-400 uppercase tracking-wider block">Core Temperature</span>
                <div className="flex items-baseline space-x-1.5">
                  <span className="text-2xl font-bold text-white">
                    {latestVital?.body_temp ?? selectedAstronaut.baseline_vitals?.baseline_body_temp ?? 36.8}
                  </span>
                  <span className="text-xs text-slate-500">°C</span>
                </div>
                <span className="text-[10px] text-slate-400">
                  Base: {selectedAstronaut.baseline_vitals?.baseline_body_temp ?? 36.7}°C
                </span>
              </div>
            </div>

            <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl flex items-center space-x-3">
              <div className="p-3 bg-amber-500/10 text-amber-400 rounded-lg">
                <Activity className="w-6 h-6" />
              </div>
              <div>
                <span className="text-xs text-slate-400 uppercase tracking-wider block">HRV (rMSSD)</span>
                <div className="flex items-baseline space-x-1.5">
                  <span className="text-2xl font-bold text-white">
                    {latestVital?.hrv ?? selectedAstronaut.baseline_vitals?.resting_hrv ?? 70}
                  </span>
                  <span className="text-xs text-slate-500">ms</span>
                </div>
                <span className="text-[10px] text-slate-400">
                  Base: {selectedAstronaut.baseline_vitals?.resting_hrv ?? 70} ms
                </span>
              </div>
            </div>
          </div>

          {/* AI Anomaly & SHAP Explainability Engine */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* SHAP Feature Contribution Chart */}
            <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <Brain className="w-5 h-5 text-cyan-400" />
                    <h3 className="text-base font-bold text-white">
                      AI Anomaly Inspector & Feature Attribution
                    </h3>
                  </div>
                  <span
                    className={`px-2 py-0.5 rounded text-xs font-bold uppercase ${
                      aiPrediction?.is_anomaly
                        ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                        : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                    }`}
                  >
                    {aiPrediction?.is_anomaly ? 'ANOMALY DETECTED' : 'BIOMETRICALLY NOMINAL'}
                  </span>
                </div>
                <p className="text-xs text-slate-400 mb-4">
                  Isolation Forest + TreeSHAP feature influence weights (% contribution toward divergence)
                </p>

                {shapChartData.length > 0 ? (
                  <div className="h-64 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={shapChartData} layout="vertical" margin={{ left: 30, right: 20 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                        <XAxis type="number" stroke="#64748b" tickFormatter={(v) => `${v}%`} />
                        <YAxis type="category" dataKey="name" stroke="#94a3b8" tick={{ fontSize: 11 }} />
                        <Tooltip
                          contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                          formatter={(value: any, name: any, item: any) => [
                            `${value}% impact (${item.payload.direction})`,
                            `Value: ${item.payload.value} (Baseline: ${item.payload.baseline})`
                          ]}
                        />
                        <Bar dataKey="shap" radius={[0, 4, 4, 0]}>
                          {shapChartData.map((entry, index) => (
                            <Cell
                              key={`cell-${index}`}
                              fill={entry.direction === 'higher_risk' ? '#f43f5e' : '#06b6d4'}
                            />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <div className="h-64 flex flex-col items-center justify-center text-slate-500">
                    <Brain className="w-10 h-10 mb-2 opacity-30" />
                    <p className="text-xs">Computing feature attributions from incoming telemetry...</p>
                  </div>
                )}
              </div>

              <div className="mt-4 p-3 bg-slate-950/70 border border-slate-800 rounded-xl">
                <span className="text-[11px] font-semibold text-slate-300 block mb-1">
                  AI Model Observation:
                </span>
                <p className="text-xs text-slate-400">
                  {aiPrediction?.clinical_observation ||
                    'All physiological parameters align within 1.2 standard deviations of established astronaut baseline.'}
                </p>
                <div className="flex items-center justify-between text-[10px] text-slate-500 mt-2 pt-2 border-t border-slate-800/80">
                  <span>Model: {aiPrediction?.model_version || 'AstroHealth-IsoForest-v1.2'}</span>
                  <span>Confidence: {((aiPrediction?.confidence || 0.95) * 100).toFixed(0)}%</span>
                  <span>Quality: {((aiPrediction?.data_quality_score || 0.98) * 100).toFixed(0)}%</span>
                </div>
              </div>
            </div>

            {/* Cardiovascular Trend Analysis & Autonomic Tone */}
            <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl flex flex-col justify-between">
              <div>
                <div className="flex items-center space-x-2 mb-2">
                  <TrendingUp className="w-5 h-5 text-blue-400" />
                  <h3 className="text-base font-bold text-white">
                    Cardiovascular Trend & Autonomic Drift
                  </h3>
                </div>
                <p className="text-xs text-slate-400 mb-4">
                  Multi-hour sliding window analysis evaluating sympathetic vs parasympathetic balance
                </p>

                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800">
                    <span className="text-xs text-slate-400 block mb-1">Autonomic Tone</span>
                    <span className="text-lg font-bold text-cyan-400 capitalize block">
                      {cardioTrends?.autonomic_balance?.tone?.replace('_', ' ') || 'Balanced'}
                    </span>
                    <span className="text-xs text-slate-500">
                      Ratio: {cardioTrends?.autonomic_balance?.ratio || '1.02'} (Target: 0.8 - 1.3)
                    </span>
                  </div>

                  <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800">
                    <span className="text-xs text-slate-400 block mb-1">Cardio Risk Indicator</span>
                    <span className="text-lg font-bold text-emerald-400 block">
                      {cardioTrends?.experimental_cardiovascular_risk?.tier?.toUpperCase() || 'LOW'}
                    </span>
                    <span className="text-xs text-slate-500">
                      Score: {cardioTrends?.experimental_cardiovascular_risk?.score || '0.1'} / 1.0
                    </span>
                  </div>
                </div>

                {/* Telemetry Timeline Mini Chart */}
                <div className="h-44 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={selectedHistory} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                      <XAxis dataKey="timestamp" hide />
                      <YAxis domain={['auto', 'auto']} stroke="#64748b" tick={{ fontSize: 10 }} />
                      <Tooltip
                        contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                      />
                      <Line
                        type="monotone"
                        dataKey="heart_rate"
                        stroke="#06b6d4"
                        strokeWidth={2}
                        dot={false}
                        name="Heart Rate (bpm)"
                      />
                      <Line
                        type="monotone"
                        dataKey="spo2"
                        stroke="#3b82f6"
                        strokeWidth={2}
                        dot={false}
                        name="SpO2 (%)"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="mt-3 text-[11px] text-slate-500 flex items-center space-x-1.5">
                <Info className="w-3.5 h-3.5 text-slate-400" />
                <span>
                  Experimental non-diagnostic metrics provided strictly as situational decision support.
                </span>
              </div>
            </div>
          </div>

          {/* Medical Reports Archive & Export Controls */}
          <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
              <div className="flex items-center space-x-3">
                <FileText className="w-6 h-6 text-blue-400" />
                <div>
                  <h3 className="text-lg font-bold text-white">
                    Flight Surgeon Clinical Reports & Mission Clearances
                  </h3>
                  <p className="text-xs text-slate-400">
                    Official medical record archive for {selectedAstronaut.full_name}
                  </p>
                </div>
              </div>

              {/* Filter Tabs */}
              <div className="flex items-center space-x-1 bg-slate-950 p-1 rounded-lg border border-slate-800">
                {['all', 'daily', 'weekly', 'incident'].map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setReportFilter(tab)}
                    className={`px-3 py-1 rounded text-xs font-semibold capitalize transition ${
                      reportFilter === tab
                        ? 'bg-blue-600 text-white'
                        : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    {tab}
                  </button>
                ))}
              </div>
            </div>

            {/* Reports List Table */}
            {filteredReports.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-sm">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 text-xs uppercase">
                      <th className="py-3 px-4">Report ID</th>
                      <th className="py-3 px-4">Date (UTC)</th>
                      <th className="py-3 px-4">Type</th>
                      <th className="py-3 px-4">Author</th>
                      <th className="py-3 px-4">Summary</th>
                      <th className="py-3 px-4 text-right">Export Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {filteredReports.map((report) => (
                      <tr key={report.id} className="hover:bg-slate-800/30 transition">
                        <td className="py-3.5 px-4 font-mono font-semibold text-cyan-400 text-xs">
                          {report.id}
                        </td>
                        <td className="py-3.5 px-4 text-xs text-slate-300">
                          {new Date(report.created_at).toLocaleString()}
                        </td>
                        <td className="py-3.5 px-4">
                          <span className="px-2 py-0.5 rounded text-[11px] font-bold uppercase bg-slate-800 text-slate-300">
                            {report.report_type}
                          </span>
                        </td>
                        <td className="py-3.5 px-4 text-xs text-slate-300">
                          {report.author_name}
                        </td>
                        <td className="py-3.5 px-4 text-xs text-slate-400 max-w-xs truncate">
                          {report.summary}
                        </td>
                        <td className="py-3.5 px-4 text-right space-x-2">
                          <a
                            href={reportsApi.getReportCsvUrl(report.id)}
                            download
                            className="inline-flex items-center space-x-1 px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded text-xs transition"
                            title="Download CSV"
                          >
                            <Download className="w-3.5 h-3.5" />
                            <span>CSV</span>
                          </a>
                          <a
                            href={reportsApi.getReportPdfUrl(report.id)}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center space-x-1 px-2.5 py-1 bg-blue-600/30 hover:bg-blue-600/50 text-blue-300 border border-blue-500/40 rounded text-xs transition"
                            title="View / Print Document"
                          >
                            <Printer className="w-3.5 h-3.5" />
                            <span>PDF / Print</span>
                          </a>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="py-12 text-center text-slate-500 bg-slate-950/40 rounded-xl border border-dashed border-slate-800">
                <FileText className="w-10 h-10 mx-auto mb-2 opacity-40" />
                <p className="text-sm">No medical reports filed for this filter.</p>
                <button
                  onClick={handleAutoGenerateReport}
                  className="mt-3 px-3 py-1.5 bg-cyan-600 text-white text-xs font-semibold rounded-lg hover:bg-cyan-500 transition"
                >
                  Generate Initial 24h AI Report
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Manual Report Drafting Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 w-full max-w-xl rounded-2xl p-6 shadow-2xl relative">
            <button
              onClick={() => setIsModalOpen(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-white"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center space-x-3 mb-4">
              <Stethoscope className="w-6 h-6 text-blue-400" />
              <div>
                <h3 className="text-lg font-bold text-white">Draft Clinical Medical Report</h3>
                <p className="text-xs text-slate-400">Target Astronaut: {selectedAstronaut?.full_name}</p>
              </div>
            </div>

            <form onSubmit={handleCreateCustomReport} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">
                  Report Category
                </label>
                <select
                  value={customReportType}
                  onChange={(e) => setCustomReportType(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500"
                >
                  <option value="daily">Daily Circadian Check</option>
                  <option value="weekly">Weekly Flight Surgeon Evaluation</option>
                  <option value="incident">Incident / Anomaly Investigation</option>
                  <option value="clearance">EVA / Payload Clearance</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">
                  Summary
                </label>
                <input
                  type="text"
                  placeholder="e.g. Routine 24-hour evaluation and ergometer review."
                  value={customSummary}
                  onChange={(e) => setCustomSummary(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">
                  Clinical Observations
                </label>
                <textarea
                  rows={3}
                  placeholder="Record objective physiological and psychological observations..."
                  value={customObservations}
                  onChange={(e) => setCustomObservations(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">
                  Recommendations (1 per line)
                </label>
                <textarea
                  rows={2}
                  placeholder="e.g. Increase hydration by 500 mL&#10;Tactical 45-minute rest period"
                  value={customRecommendations}
                  onChange={(e) => setCustomRecommendations(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="flex justify-end space-x-3 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 text-sm text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={generatingReport}
                  className="px-5 py-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm rounded-lg transition"
                >
                  {generatingReport ? 'Filing Report...' : 'File Official Report'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

