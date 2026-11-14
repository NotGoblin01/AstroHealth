import React, { useState, useEffect } from 'react';
import {
  Brain,
  Moon,
  Smile,
  Zap,
  BookOpen,
  Send,
  Lock,
  Calendar,
  Sparkles,
  TrendingDown,
  CheckCircle2,
  Info
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

import { DailyWellness, User } from '../types';
import { wellnessApi, authApi } from '../services/api';

export const WellnessPage: React.FC = () => {
  const [currentUser, setCurrentUser] = useState<User | null>(authApi.getCurrentUser());
  const [astronautId, setAstronautId] = useState<string>(currentUser?.astronaut_id || 'ASTRO-001');

  // Form inputs
  const [moodScore, setMoodScore] = useState<number>(8);
  const [stressScore, setStressScore] = useState<number>(3);
  const [sleepHours, setSleepHours] = useState<number>(7.5);
  const [sleepQuality, setSleepQuality] = useState<number>(8);
  const [fatigueScore, setFatigueScore] = useState<number>(3);
  const [workloadRating, setWorkloadRating] = useState<number>(5);
  const [journalNotes, setJournalNotes] = useState<string>('');

  const [history, setHistory] = useState<DailyWellness[]>([]);
  const [latestInsight, setLatestInsight] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [submitSuccess, setSubmitSuccess] = useState<boolean>(false);

  const fetchWellnessData = async () => {
    try {
      const logs = await wellnessApi.getWellnessHistory(astronautId, 14);
      setHistory(logs.reverse());
      if (logs.length > 0 && logs[logs.length - 1].supportive_insight) {
        setLatestInsight(logs[logs.length - 1].supportive_insight || null);
      }
    } catch (e) {
      console.error('Error fetching wellness logs', e);
    }
  };

  useEffect(() => {
    fetchWellnessData();
  }, [astronautId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSubmitting(true);
      const todayStr = new Date().toISOString().split('T')[0];
      const entry = {
        astronaut_id: astronautId,
        date: todayStr,
        mood_score: moodScore,
        stress_score: stressScore,
        sleep_hours: sleepHours,
        sleep_quality_score: sleepQuality,
        fatigue_score: fatigueScore,
        workload_rating: workloadRating,
        journal_notes: journalNotes
      };

      const result = await wellnessApi.submitDailyWellness(entry);
      setLatestInsight(result.supportive_insight || null);
      setSubmitSuccess(true);
      setTimeout(() => setSubmitSuccess(false), 4000);
      fetchWellnessData();
    } catch (err: any) {
      alert(`Error submitting wellness assessment: ${err.response?.data?.detail || err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-4 md:p-8 space-y-8 font-sans">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900/90 border border-slate-800 p-6 rounded-2xl shadow-xl backdrop-blur-md">
        <div className="flex items-center space-x-4">
          <div className="p-3 bg-violet-500/10 border border-violet-500/30 rounded-xl text-violet-400">
            <Brain className="w-8 h-8" />
          </div>
          <div>
            <div className="flex items-center space-x-3">
              <h1 className="text-2xl font-bold tracking-tight text-white">
                Psychological Wellness & Circadian Recovery
              </h1>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-violet-500/20 text-violet-400 border border-violet-500/30 flex items-center space-x-1">
                <Lock className="w-3 h-3" />
                <span>CONFIDENTIAL CREW RECORD</span>
              </span>
            </div>
            <p className="text-sm text-slate-400 mt-1">
              Daily autonomous mood evaluation &bull; Sleep architecture tracking &bull; Non-diagnostic supportive guidance
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3 text-xs text-slate-400 bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800">
          <Calendar className="w-4 h-4 text-cyan-400" />
          <span className="hidden sm:inline">Active Subject:</span>
          <div className="flex items-center space-x-1">
            {['ASTRO-001', 'ASTRO-002', 'ASTRO-003'].map((id) => (
              <button
                key={id}
                type="button"
                onClick={() => setAstronautId(id)}
                className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold transition ${
                  astronautId === id
                    ? 'bg-violet-600 text-white shadow-sm'
                    : 'bg-slate-900 text-slate-400 hover:text-white'
                }`}
              >
                {id}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Content Grid: Assessment Form + AI Insight & Trend Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Daily Wellness Input Form */}
        <div className="lg:col-span-6 bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl space-y-6">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center space-x-2">
              <Smile className="w-5 h-5 text-cyan-400" />
              <h3 className="text-lg font-bold text-white">Daily Wellness Assessment</h3>
            </div>
            <span className="text-xs text-slate-400">Takes ~60 seconds</span>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Mood Slider */}
            <div>
              <div className="flex justify-between items-center text-xs mb-1.5">
                <span className="font-semibold text-slate-300">Mood Valence (1 = Depressed, 10 = Flourishing)</span>
                <span className="font-bold text-cyan-400 text-sm">{moodScore} / 10</span>
              </div>
              <input
                type="range"
                min="1"
                max="10"
                value={moodScore}
                onChange={(e) => setMoodScore(Number(e.target.value))}
                className="w-full h-2 bg-slate-950 rounded-lg appearance-none cursor-pointer accent-cyan-500"
              />
            </div>

            {/* Stress Slider */}
            <div>
              <div className="flex justify-between items-center text-xs mb-1.5">
                <span className="font-semibold text-slate-300">Perceived Stress (1 = Relaxed, 10 = Acute Strain)</span>
                <span className="font-bold text-amber-400 text-sm">{stressScore} / 10</span>
              </div>
              <input
                type="range"
                min="1"
                max="10"
                value={stressScore}
                onChange={(e) => setStressScore(Number(e.target.value))}
                className="w-full h-2 bg-slate-950 rounded-lg appearance-none cursor-pointer accent-amber-500"
              />
            </div>

            {/* Sleep Hours and Quality */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Sleep Duration (Hours)
                </label>
                <div className="flex items-center space-x-2">
                  <Moon className="w-4 h-4 text-blue-400" />
                  <input
                    type="number"
                    step="0.5"
                    min="0"
                    max="18"
                    value={sleepHours}
                    onChange={(e) => setSleepHours(Number(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-cyan-500"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Sleep Quality (1-10)
                </label>
                <div className="flex items-center space-x-2">
                  <Zap className="w-4 h-4 text-violet-400" />
                  <input
                    type="number"
                    min="1"
                    max="10"
                    value={sleepQuality}
                    onChange={(e) => setSleepQuality(Number(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-cyan-500"
                    required
                  />
                </div>
              </div>
            </div>

            {/* Fatigue and Workload */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Fatigue Level (1-10)
                </label>
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={fatigueScore}
                  onChange={(e) => setFatigueScore(Number(e.target.value))}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-cyan-500"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Mission Workload (1-10)
                </label>
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={workloadRating}
                  onChange={(e) => setWorkloadRating(Number(e.target.value))}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-cyan-500"
                  required
                />
              </div>
            </div>

            {/* Confidential Journal Notes */}
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center space-x-1.5">
                <BookOpen className="w-4 h-4 text-slate-400" />
                <span>Personal Journal Notes (Encrypted)</span>
              </label>
              <textarea
                rows={3}
                placeholder="Optional notes regarding dreams, sensory deprivation, workload or team dynamics..."
                value={journalNotes}
                onChange={(e) => setJournalNotes(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-cyan-500"
              />
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full py-2.5 px-4 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-semibold text-sm rounded-lg shadow-lg shadow-cyan-600/20 transition flex items-center justify-center space-x-2"
            >
              {submitting ? (
                <span>Logging Assessment...</span>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  <span>Submit Daily Assessment</span>
                </>
              )}
            </button>

            {submitSuccess && (
              <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl flex items-center space-x-2 text-emerald-400 text-xs">
                <CheckCircle2 className="w-4 h-4" />
                <span>Wellness assessment successfully recorded and processed.</span>
              </div>
            )}
          </form>
        </div>

        {/* Right Column: AI Supportive Guidance & Multi-Day Wellness Trends */}
        <div className="lg:col-span-6 space-y-6">
          {/* Supportive AI Observation Card */}
          <div className="bg-gradient-to-br from-slate-900 to-slate-900/60 border border-violet-500/30 p-6 rounded-2xl shadow-xl relative overflow-hidden">
            <div className="flex items-center space-x-2 text-violet-400 mb-3">
              <Sparkles className="w-5 h-5" />
              <h3 className="text-base font-bold text-white">AI Supportive Hygiene Insights</h3>
            </div>
            <p className="text-sm text-slate-300 leading-relaxed">
              {latestInsight ||
                'No significant behavioral strain detected. Circadian rhythm and sleep architecture remain within standard Mars-transit envelope.'}
            </p>
            <div className="mt-4 pt-3 border-t border-slate-800 flex items-center space-x-2 text-[11px] text-slate-500">
              <Info className="w-3.5 h-3.5 text-slate-400" />
              <span>Automated supportive insights &bull; Non-diagnostic mission hygiene guidance</span>
            </div>
          </div>

          {/* Sleep & Fatigue Trends Chart */}
          <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h4 className="text-base font-bold text-white">Sleep Duration & Fatigue Trajectory</h4>
                <p className="text-xs text-slate-400">14-Day Circadian History</p>
              </div>
            </div>
            <div className="h-56 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={history} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="sleepGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.5} />
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 10 }} />
                  <YAxis stroke="#64748b" tick={{ fontSize: 10 }} />
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }} />
                  <Legend />
                  <Area type="monotone" dataKey="sleep_hours" stroke="#3b82f6" fill="url(#sleepGrad)" name="Sleep Hours" />
                  <Line type="monotone" dataKey="fatigue_score" stroke="#f43f5e" strokeWidth={2} dot={false} name="Fatigue (1-10)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Stress & Mood Balance */}
          <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h4 className="text-base font-bold text-white">Mood Valence vs Perceived Stress</h4>
                <p className="text-xs text-slate-400">Psychological resilience correlation</p>
              </div>
            </div>
            <div className="h-56 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={history} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 10 }} />
                  <YAxis domain={[1, 10]} stroke="#64748b" tick={{ fontSize: 10 }} />
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }} />
                  <Legend />
                  <Line type="monotone" dataKey="mood_score" stroke="#06b6d4" strokeWidth={2} name="Mood (1-10)" />
                  <Line type="monotone" dataKey="stress_score" stroke="#f59e0b" strokeWidth={2} name="Stress (1-10)" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

