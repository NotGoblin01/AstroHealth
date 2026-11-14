import axios from 'axios';
import {
  User,
  Astronaut,
  Mission,
  Device,
  SensorReading,
  EnvironmentalReading,
  HealthAlert,
  DailyWellness,
  SimulatorStatus,
  AIPrediction,
  MedicalReport
} from '../types';

const API_BASE_URL = '/api';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to attach JWT token
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('astrohealth_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Authentication Service
export const authApi = {
  login: async (username: string, password: string) => {
    const res = await apiClient.post('/auth/login', { username, password });
    if (res.data.access_token) {
      localStorage.setItem('astrohealth_token', res.data.access_token);
      localStorage.setItem('astrohealth_user', JSON.stringify(res.data.user));
    }
    return res.data;
  },
  getMe: async (): Promise<User> => {
    const res = await apiClient.get<User>('/auth/me');
    return res.data;
  },
  logout: () => {
    localStorage.removeItem('astrohealth_token');
    localStorage.removeItem('astrohealth_user');
  },
  getCurrentUser: (): User | null => {
    const userStr = localStorage.getItem('astrohealth_user');
    if (!userStr) return null;
    try {
      return JSON.parse(userStr);
    } catch {
      return null;
    }
  }
};

// Astronaut Service
export const astronautApi = {
  getAstronauts: async (): Promise<Astronaut[]> => {
    const res = await apiClient.get<Astronaut[]>('/astronauts');
    return res.data;
  },
  getAstronautById: async (astronautId: string): Promise<Astronaut> => {
    const res = await apiClient.get<Astronaut>(`/astronauts/${astronautId}`);
    return res.data;
  },
};

// Missions & Devices Service
export const missionApi = {
  getMissions: async (): Promise<Mission[]> => {
    const res = await apiClient.get<Mission[]>('/missions');
    return res.data;
  },
  getDevices: async (): Promise<Device[]> => {
    const res = await apiClient.get<Device[]>('/devices');
    return res.data;
  }
};

// Telemetry Service
export const telemetryApi = {
  getLatestBiometrics: async (astronautId: string): Promise<SensorReading> => {
    const res = await apiClient.get<SensorReading>(`/telemetry/biometrics/latest/${astronautId}`);
    return res.data;
  },
  getBiometricHistory: async (astronautId: string, limit = 60, minutes?: number): Promise<SensorReading[]> => {
    const params: any = { limit };
    if (minutes) params.minutes = minutes;
    const res = await apiClient.get<SensorReading[]>(`/telemetry/biometrics/history/${astronautId}`, { params });
    return res.data;
  },
  getLatestEnvironmental: async (): Promise<EnvironmentalReading[]> => {
    const res = await apiClient.get<EnvironmentalReading[]>('/telemetry/environmental/latest');
    return res.data;
  },
  getEnvironmentalHistory: async (compartmentId: string, limit = 60): Promise<EnvironmentalReading[]> => {
    const res = await apiClient.get<EnvironmentalReading[]>(`/telemetry/environmental/history/${compartmentId}`, { params: { limit } });
    return res.data;
  },
  getSummary: async () => {
    const res = await apiClient.get('/telemetry/summary');
    return res.data;
  }
};

// Simulator Controls
export const simulatorApi = {
  getStatus: async (): Promise<SimulatorStatus> => {
    const res = await apiClient.get<SimulatorStatus>('/simulator/status');
    return res.data;
  },
  start: async () => {
    const res = await apiClient.post('/simulator/start');
    return res.data;
  },
  pause: async () => {
    const res = await apiClient.post('/simulator/pause');
    return res.data;
  },
  resume: async () => {
    const res = await apiClient.post('/simulator/resume');
    return res.data;
  },
  stop: async () => {
    const res = await apiClient.post('/simulator/stop');
    return res.data;
  },
  setScenario: async (scenario: string) => {
    const res = await apiClient.post('/simulator/scenario', { scenario });
    return res.data;
  },
  setInterval: async (interval_seconds: number) => {
    const res = await apiClient.post('/simulator/interval', { interval_seconds });
    return res.data;
  },
  setTarget: async (astronaut_id: string) => {
    const res = await apiClient.post('/simulator/target', { astronaut_id });
    return res.data;
  }
};

// AI & Clinical Analytics Service
export const aiApi = {
  getLatestPrediction: async (astronautId: string): Promise<AIPrediction> => {
    const res = await apiClient.get<AIPrediction>(`/ai/predictions/latest/${astronautId}`);
    return res.data;
  },
  getCardioTrends: async (astronautId: string, hours = 24) => {
    const res = await apiClient.get(`/ai/trends/cardiovascular/${astronautId}`, { params: { hours } });
    return res.data;
  },
  getBehavioralAnalytics: async (astronautId: string, days = 7) => {
    const res = await apiClient.get(`/ai/behavioral/${astronautId}`, { params: { days } });
    return res.data;
  },
  getForecast: async (astronautId: string, indicator = 'heart_rate', horizonMinutes = 60) => {
    const res = await apiClient.get(`/ai/forecast/${astronautId}`, { params: { indicator, horizon_minutes: horizonMinutes } });
    return res.data;
  }
};

// Medical Reports Service
export const reportsApi = {
  listReports: async (astronautId?: string, reportType?: string): Promise<MedicalReport[]> => {
    const params: any = {};
    if (astronautId) params.astronaut_id = astronautId;
    if (reportType) params.report_type = reportType;
    const res = await apiClient.get<MedicalReport[]>('/reports', { params });
    return res.data;
  },
  createReport: async (reportData: Partial<MedicalReport>): Promise<MedicalReport> => {
    const res = await apiClient.post<MedicalReport>('/reports', reportData);
    return res.data;
  },
  generateAutoReport: async (astronautId: string, reportType = 'daily', hours = 24): Promise<MedicalReport> => {
    const res = await apiClient.post<MedicalReport>('/reports/generate-auto', null, {
      params: { astronaut_id: astronautId, report_type: reportType, hours }
    });
    return res.data;
  },
  getReportById: async (reportId: string): Promise<MedicalReport> => {
    const res = await apiClient.get<MedicalReport>(`/reports/${reportId}`);
    return res.data;
  },
  getReportPdfUrl: (reportId: string): string => {
    return `/api/reports/${reportId}/export/pdf`;
  },
  getReportCsvUrl: (reportId: string): string => {
    return `/api/reports/${reportId}/export/csv`;
  }
};

// Psychological Wellness Service
export const wellnessApi = {
  submitDailyWellness: async (data: Partial<DailyWellness>): Promise<DailyWellness> => {
    const res = await apiClient.post<DailyWellness>('/wellness', data);
    return res.data;
  },
  getWellnessHistory: async (astronautId: string, days = 14): Promise<DailyWellness[]> => {
    const res = await apiClient.get<DailyWellness[]>(`/wellness/history/${astronautId}`, { params: { days } });
    return res.data;
  },
  getLatestWellness: async (astronautId: string): Promise<DailyWellness | null> => {
    const res = await apiClient.get<DailyWellness | null>(`/wellness/latest/${astronautId}`);
    return res.data;
  }
};

// Alerts Service
export const alertsApi = {
  getActiveAlerts: async (): Promise<HealthAlert[]> => {
    const res = await apiClient.get<HealthAlert[]>('/alerts/active');
    return res.data;
  },
  listAlerts: async (category?: string, status?: string): Promise<HealthAlert[]> => {
    const params: any = {};
    if (category) params.category = category;
    if (status) params.status_filter = status;
    const res = await apiClient.get<HealthAlert[]>('/alerts', { params });
    return res.data;
  },
  acknowledgeAlert: async (alertId: string, notes?: string): Promise<HealthAlert> => {
    const res = await apiClient.post<HealthAlert>(`/alerts/${alertId}/acknowledge`, { notes });
    return res.data;
  },
  resolveAlert: async (alertId: string, resolutionNotes: string): Promise<HealthAlert> => {
    const res = await apiClient.post<HealthAlert>(`/alerts/${alertId}/resolve`, null, {
      params: { resolution_notes: resolutionNotes }
    });
    return res.data;
  },
  triggerEmergency: async (astronautId: string, title: string, reason: string, location?: string): Promise<HealthAlert> => {
    const res = await apiClient.post<HealthAlert>('/alerts/emergency', {
      astronaut_id: astronautId,
      title,
      reason,
      location: location || 'Crew Module Alpha'
    });
    return res.data;
  }
};

