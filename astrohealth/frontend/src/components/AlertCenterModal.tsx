import React, { useState, useEffect } from 'react';
import {
  Bell,
  AlertTriangle,
  ShieldAlert,
  Info,
  CheckCircle2,
  X,
  Clock,
  UserCheck,
  Send
} from 'lucide-react';
import { HealthAlert, UserRole } from '../types';
import { alertsApi, authApi } from '../services/api';

interface AlertCenterModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAlertCountChange?: (count: number) => void;
}

export const AlertCenterModal: React.FC<AlertCenterModalProps> = ({
  isOpen,
  onClose,
  onAlertCountChange
}) => {
  const [alerts, setAlerts] = useState<HealthAlert[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [selectedAlert, setSelectedAlert] = useState<HealthAlert | null>(null);
  const [resolutionNote, setResolutionNote] = useState<string>('');
  const [ackNote, setAckNote] = useState<string>('');
  const [isResolving, setIsResolving] = useState<boolean>(false);

  const currentUser = authApi.getCurrentUser();
  const isMedOfficerOrAdmin = currentUser?.role === 'medical_officer' || currentUser?.role === 'admin';

  const fetchActiveAlerts = async () => {
    try {
      setLoading(true);
      const active = await alertsApi.getActiveAlerts();
      setAlerts(active);
      if (onAlertCountChange) onAlertCountChange(active.length);
    } catch (e) {
      console.error('Failed to load active alerts', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchActiveAlerts();
    }
  }, [isOpen]);

  const handleAcknowledge = async (alertId: string) => {
    try {
      await alertsApi.acknowledgeAlert(alertId, ackNote || 'Acknowledged by flight surgeon on duty.');
      setAckNote('');
      fetchActiveAlerts();
      alert('Alert successfully acknowledged.');
    } catch (err: any) {
      alert(`Error acknowledging alert: ${err.response?.data?.detail || err.message}`);
    }
  };

  const handleResolve = async (alertId: string) => {
    if (!resolutionNote.trim()) {
      alert('Please provide clinical resolution notes.');
      return;
    }
    try {
      setIsResolving(true);
      await alertsApi.resolveAlert(alertId, resolutionNote);
      setResolutionNote('');
      setSelectedAlert(null);
      fetchActiveAlerts();
      alert('Alert successfully resolved.');
    } catch (err: any) {
      alert(`Error resolving alert: ${err.response?.data?.detail || err.message}`);
    } finally {
      setIsResolving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-700 w-full max-w-2xl rounded-2xl p-6 shadow-2xl relative max-h-[85vh] flex flex-col">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-white"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Modal Header */}
        <div className="flex items-center space-x-3 mb-6 pb-4 border-b border-slate-800">
          <div className="p-2.5 bg-rose-500/10 text-rose-400 rounded-xl border border-rose-500/20">
            <Bell className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-white">Mission Health & Safety Alert Engine</h3>
            <p className="text-xs text-slate-400">
              Active biometric, cabin life support, and manual distress notifications ({alerts.length} active)
            </p>
          </div>
        </div>

        {/* Alerts List */}
        <div className="flex-1 overflow-y-auto space-y-3 pr-1">
          {alerts.length > 0 ? (
            alerts.map((alert) => {
              const isEmergency = alert.category === 'emergency';
              const isUrgent = alert.category === 'urgent_assessment';

              return (
                <div
                  key={alert.id}
                  className={`p-4 rounded-xl border transition ${
                    isEmergency
                      ? 'bg-rose-950/20 border-rose-500/50'
                      : isUrgent
                      ? 'bg-amber-950/20 border-amber-500/40'
                      : 'bg-slate-950/60 border-slate-800'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <div className="flex items-center space-x-2">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-extrabold uppercase ${
                            isEmergency
                              ? 'bg-rose-500 text-white'
                              : isUrgent
                              ? 'bg-amber-500 text-slate-950'
                              : 'bg-blue-600 text-white'
                          }`}
                        >
                          {alert.category.replace('_', ' ')}
                        </span>
                        <span className="text-xs text-slate-400 font-mono">
                          Target: {alert.astronaut_id}
                        </span>
                      </div>
                      <h4 className="text-sm font-bold text-white mt-1.5">{alert.title}</h4>
                      <p className="text-xs text-slate-300 mt-1">{alert.message}</p>
                    </div>

                    <div className="text-right text-[11px] text-slate-400 flex items-center space-x-1 shrink-0">
                      <Clock className="w-3 h-3" />
                      <span>{new Date(alert.created_at).toLocaleTimeString()}</span>
                    </div>
                  </div>

                  {/* Actions Bar for Medical Officers and Admins */}
                  {isMedOfficerOrAdmin && (
                    <div className="mt-3 pt-3 border-t border-slate-800/80 flex items-center justify-between">
                      <span className="text-[11px] text-slate-400">
                        Status: <strong className="text-slate-200 capitalize">{alert.status}</strong>
                        {alert.acknowledged_by && ` (Ack: ${alert.acknowledged_by})`}
                      </span>

                      <div className="space-x-2">
                        {alert.status === 'active' && (
                          <button
                            onClick={() => handleAcknowledge(alert.id)}
                            className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded border border-slate-700 transition"
                          >
                            Acknowledge
                          </button>
                        )}
                        <button
                          onClick={() => setSelectedAlert(alert)}
                          className="px-2.5 py-1 bg-emerald-600/30 hover:bg-emerald-600/50 text-emerald-300 border border-emerald-500/40 text-xs font-semibold rounded transition"
                        >
                          Resolve...
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              );
            })
          ) : (
            <div className="py-12 text-center text-slate-500 bg-slate-950/40 rounded-xl border border-dashed border-slate-800">
              <CheckCircle2 className="w-10 h-10 mx-auto mb-2 text-emerald-500/50" />
              <p className="text-sm">All crew biometrics and habitat parameters are NOMINAL.</p>
              <p className="text-xs text-slate-500 mt-1">Zero active clinical or life-support alerts.</p>
            </div>
          )}
        </div>

        {/* Resolution Dialog Subsection */}
        {selectedAlert && (
          <div className="mt-4 pt-4 border-t border-slate-800 bg-slate-950 p-4 rounded-xl border border-emerald-500/30">
            <h4 className="text-xs font-bold text-emerald-400 uppercase mb-2">
              Clinical Resolution Entry &bull; {selectedAlert.id}
            </h4>
            <textarea
              rows={2}
              placeholder="Enter official medical resolution justification..."
              value={resolutionNote}
              onChange={(e) => setResolutionNote(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-emerald-500 mb-3"
            />
            <div className="flex justify-end space-x-2">
              <button
                onClick={() => setSelectedAlert(null)}
                className="px-3 py-1 text-xs text-slate-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                onClick={() => handleResolve(selectedAlert.id)}
                disabled={isResolving}
                className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-lg transition"
              >
                {isResolving ? 'Resolving...' : 'Confirm Resolution'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

