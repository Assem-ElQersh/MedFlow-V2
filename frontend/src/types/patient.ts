export type SexEnum = 'male' | 'female';
export type SmokingStatusEnum = 'never' | 'former' | 'current' | 'unknown';

export interface Medication {
  name: string;
  dosage: string;
  frequency: string;
  start_date?: string;
  instructions?: string;
}

export interface SurgicalProcedure {
  procedure: string;
  date: string;
  notes?: string;
}

export interface SmokingDetails {
  pack_years?: number;
  quit_date?: string;
}

export interface PatientBase {
  name: string;
  national_id: string;
  date_of_birth: string;
  phone_primary: string;
  phone_secondary?: string;
  email?: string;
  address?: string;
  sex: SexEnum;
  chronic_diseases: string[];
  allergies: string[];
  current_medications: Medication[];
  surgical_history: SurgicalProcedure[];
  smoking_status: SmokingStatusEnum;
  smoking_details?: SmokingDetails;
}

export interface Patient extends PatientBase {
  patient_id: string;
  age: number;
  registration_date: string;
  last_updated: string;
  last_updated_by: string;
  total_sessions: number;
  last_session_id?: string;
  last_session_date?: string;
}

export interface PatientSearchResult {
  patient_id: string;
  name: string;
  age: number;
  phone_primary: string;
  national_id: string;
  last_session_date?: string;
  total_sessions: number;
}

export interface PatientCreateRequest extends PatientBase {}

export interface PatientUpdateRequest extends Partial<PatientBase> {}

