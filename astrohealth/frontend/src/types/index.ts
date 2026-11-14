export type UserRole = 'astronaut' | 'medical_officer' | 'admin';

export interface User {
  id: string;
  username: string;
  email: string;
  full_name: string;
  role: UserRole;
  callsign?: string;
  rank?: string;
  mission_id?: string;
  astronaut_id?: string;
  is_active: boolean;
  created_at: string;
}

export interface BaselineVitals {
  resting_heart_rate: number;
  resting_hrv: number;
  baseline_spo2: number;
  baseline_body_temp: number;
  resting_systolic_bp: number;
  resting_diastolic_bp: number;
}

export interface Astronaut {
  id: string;
  astronaut_id: string;
  full_name: string;
  user_id?: string;
  mission_id: string;
  age: number;
  sex: string;
  blood_type: string;
  role_description: string;
  assigned_devices: string[];
  baseline_vitals: BaselineVitals;
  medical_clearance_status: string;
  active: boolean;
  created_at: string;
}

export interface Mission {
  id: string;
  mission_code: string;
  mission_name: string;
  target: string;
  launch_date: string;
  planned_duration_days: number;
  commanding_officer: string;
  assigned_crew: string[];
  status: string;
  habitat_compartments: string[];
}

export interface Device {
  id: string;
  device_id: string;
  device_name: string;
  device_type: 'wearable_biometric' | 'environmental_cabin' | 'radiation_dosimeter';
  assigned_to: string;
  firmware_version: string;
  status: 'online' | 'offline' | 'degraded' | 'maintenance';
  battery_level_pct: number;
  signal_strength_dbm: number;
  last_seen?: string;
}

export interface SensorReading {
  id: string;
  astronaut_id: string;
  device_id: string;
  timestamp: string;
  heart_rate: number;
  hrv: number;
  spo2: number;
  body_temp: number;
  temp_measurement_type: string;
  motion_x: number;
  motion_y: number;
  motion_z: number;
  motion_magnitude: number;
  activity_level: string;
  measurement_quality: number;
  is_simulated: boolean;
}

export interface EnvironmentalReading {
  id: string;
  compartment_id: string;
  device_id: string;
  timestamp: string;
  temperature: number;
  humidity: number;
  atmospheric_pressure: number;
  co2_ppm: number;
  voc_index: number;
  radiation_dose_rate_uSv_h: number;
  radiation_cumulative_mSv: number;
  radiation_exposure_estimated: number;
  sensor_status: string;
  is_simulated: boolean;
}

export interface HealthAlert {
  id: string;
  astronaut_id: string;
  source: string;
  category: 'informational' | 'attention_required' | 'urgent_assessment' | 'emergency';
  title: string;
  message: string;
  vital_value?: number;
  threshold_value?: number;
  status: 'active' | 'acknowledged' | 'investigating' | 'resolved';
  created_at: string;
  acknowledged_by?: string;
  acknowledged_at?: string;
}

export interface DailyWellness {
  id: string;
  astronaut_id: string;
  date: string;
  mood_score: number;
  stress_score: number;
  sleep_hours: number;
  sleep_quality_score: number;
  fatigue_score: number;
  workload_rating: number;
  journal_notes?: string;
  supportive_insight?: string;
  created_at: string;
}

export interface SimulatorStatus {
  status: 'running' | 'paused' | 'stopped';
  scenario: string;
  interval_seconds: number;
  target_astronaut_id: string;
  generated_samples_count: number;
  scenario_descriptions: Record<string, string>;
}

export interface AnomalyFeatureContribution {
  feature_name: string;
  feature_value: number;
  shap_value: number;
  contribution_direction: string;
  baseline_value: number;
}

export interface AIPrediction {
  id: string;
  astronaut_id: string;
  timestamp: string;
  model_name: string;
  is_anomaly: boolean;
  anomaly_score: number;
  confidence: number;
  data_quality_score: number;
  contributing_features: AnomalyFeatureContribution[];
  clinical_observation: string;
  model_version: string;
  experimental_disclaimer: string;
}

export interface MedicalReport {
  id: string;
  astronaut_id: string;
  report_type: 'daily' | 'weekly' | 'incident' | 'clearance';
  summary: string;
  clinical_observations: string;
  recommendations: string[];
  vitals_snapshot: Record<string, any>;
  ai_insights: Record<string, any>;
  author_id: string;
  author_name: string;
  created_at: string;
}

