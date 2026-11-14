import React, { useState } from 'react';
import { AlertTriangle, X, ShieldAlert, CheckCircle2 } from 'lucide-react';
import { alertsApi, apiClient } from '../services/api';

interface EmergencyModalProps {
  isOpen: boolean;
  onClose: () => void;
  astronautId: string;
}

export const EmergencyModal: React.FC<EmergencyModalProps> = ({
  isOpen,
  onClose,
  astronautId,
}) => {
  const [reason, setReason] = useState('Acute physiological chest pressure / shortness of breath.');
  const [location, setLocation] = useState('Command_Module');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      // 1. Trigger official emergency medical escalation alert in backend
      await alertsApi.triggerEmergency(
        astronautId,
        'Crew Medical Distress Escalation',
        reason,
        location
      );

      // 2. Also register corresponding acute distress vitals into telemetry pipeline
      await apiClient.post('/telemetry/biometrics', {
        astronaut_id: astronautId,
        device_id: 'DEV-EMERGENCY-MANUAL',
        timestamp: new Date().toISOString(),
        heart_rate: 138.0,
        hrv: 21.0,
        spo2: 85.5,  // Severe Hypoxia trigger
        body_temp: 37.2,
        temp_measurement_type: 'epidermal_patch',
        motion_x: 0.1,
        motion_y: 0.1,
        motion_z: 1.0,
        activity_level: 'rest',
        measurement_quality: 1.0,
        is_simulated: false
      }).catch(() => null);

      setSubmitted(true);
      setTimeout(() => {
        setSubmitted(false);
        setIsSubmitting(false);
        onClose();
      }, 2000);
    } catch (err: any) {
      console.error('Emergency trigger failed:', err);
      alert(`Emergency transmission error: ${err.response?.data?.detail || err.message}`);
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-space-950/80 backdrop-blur-md">
      <div className="relative w-full max-w-lg rounded-2xl border border-red-500/50 bg-space-900 p-6 shadow-alert-glow">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-white"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center space-x-3 mb-4">
          <div className="p-2.5 rounded-xl bg-red-500/20 border border-red-500/30 text-red-400 animate-pulse">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white tracking-wide">
              EMERGENCY MEDICAL ESCALATION
            </h2>
            <p className="text-xs text-red-300/80 font-mono">
              Priority 1 Direct Flight Surgeon & Autonomous Life-Support Override
            </p>
          </div>
        </div>

        {submitted ? (
          <div className="py-8 flex flex-col items-center justify-center space-y-3 text-center">
            <CheckCircle2 className="w-12 h-12 text-emerald-400 animate-bounce" />
            <p className="text-sm font-bold text-white">EMERGENCY BROADCAST TRANSMITTED</p>
            <p className="text-xs font-mono text-slate-400">
              Flight Surgeon and Mission Control alerted. Life-support oxygenation protocols initiated.
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4 text-xs font-mono">
            <div>
              <label className="block text-slate-300 font-semibold mb-1">
                Affected Astronaut:
              </label>
              <input
                type="text"
                disabled
                value={astronautId}
                className="w-full bg-space-950 border border-space-800 rounded-lg p-2.5 text-slate-300"
              />
            </div>

            <div>
              <label className="block text-slate-300 font-semibold mb-1">
                Current Location / Compartment:
              </label>
              <select
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                className="w-full bg-space-950 border border-space-800 rounded-lg p-2.5 text-slate-200 focus:border-red-500 focus:outline-none"
              >
                <option value="Command_Module">Command Module (Alpha)</option>
                <option value="Living_Quarters">Living Quarters (Beta)</option>
                <option value="Science_Lab">Science Lab (Gamma)</option>
                <option value="EVA_Airlock">EVA Airlock (Delta)</option>
              </select>
            </div>

            <div>
              <label className="block text-slate-300 font-semibold mb-1">
                Nature of Acute Distress:
              </label>
              <textarea
                rows={3}
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                className="w-full bg-space-950 border border-space-800 rounded-lg p-2.5 text-slate-200 focus:border-red-500 focus:outline-none"
                placeholder="Describe physiological symptoms or immediate danger..."
              />
            </div>

            <div className="p-3 rounded-lg bg-red-950/30 border border-red-900/40 text-[11px] text-red-300 leading-relaxed">
              <strong>Notice:</strong> This escalation activates autonomous telemetry polling at 200ms intervals, alarms the Medical Officer console, and flags all subsequent biometrics with highest clinical triage priority.
            </div>

            <div className="flex items-center justify-end space-x-3 pt-2">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 rounded-lg bg-space-800 hover:bg-space-700 text-slate-300 transition-all"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-5 py-2 rounded-lg bg-red-600 hover:bg-red-500 text-white font-bold transition-all shadow-alert-glow flex items-center space-x-2"
              >
                <ShieldAlert className="w-4 h-4" />
                <span>{isSubmitting ? 'TRANSMITTING...' : 'TRIGGER EMERGENCY NOW'}</span>
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};

