import axiosInstance from '../utils/axios';
import { API_V1_PREFIX } from '../config/api';
import { Session } from '../types/session';

export interface SessionSummary {
  session_id: string;
  patient_id: string;
  patient_name: string;
  session_date: string;
  session_type: string;
  session_status: string;
  chief_complaint: string;
  assigned_doctor_name: string;
}

export interface Diagnosis {
  primary_diagnosis: string;
  severity: 'mild' | 'moderate' | 'severe';
  medications: Medication[];
  recommendations: string;
  follow_up_required: boolean;
  follow_up_reason?: string;
  follow_up_date?: string;
  doctor_notes: string;
}

export interface Medication {
  name: string;
  dosage: string;
  duration: string;
  instructions: string;
}

export interface PendingTests {
  required: boolean;
  tests_requested: string[];
  instructions_to_patient: string;
}

export const doctorService = {
  // Get doctor queue
  getQueue: async (assignedToMe: boolean = false, status: string = 'awaiting_doctor'): Promise<SessionSummary[]> => {
    const response = await axiosInstance.get<SessionSummary[]>(
      `${API_V1_PREFIX}/doctor/queue`,
      { params: { assigned_to_me: assignedToMe, status } }
    );
    return response.data;
  },

  // Get session for review
  getSessionForReview: async (sessionId: string): Promise<Session> => {
    const response = await axiosInstance.get<Session>(
      `${API_V1_PREFIX}/doctor/sessions/${sessionId}/review`
    );
    return response.data;
  },

  // Chat with VLM
  chatWithVLM: async (sessionId: string, message: string): Promise<any> => {
    const response = await axiosInstance.post(
      `${API_V1_PREFIX}/doctor/sessions/${sessionId}/vlm-chat`,
      { content: message }
    );
    return response.data;
  },

  // Submit diagnosis
  submitDiagnosis: async (sessionId: string, diagnosis: Diagnosis): Promise<void> => {
    await axiosInstance.put(
      `${API_V1_PREFIX}/doctor/sessions/${sessionId}/diagnosis`,
      diagnosis
    );
  },

  // Set pending tests
  setPendingTests: async (sessionId: string, pendingTests: PendingTests): Promise<void> => {
    await axiosInstance.put(
      `${API_V1_PREFIX}/doctor/sessions/${sessionId}/pending-tests`,
      pendingTests
    );
  },

  // Close session
  closeSession: async (sessionId: string): Promise<any> => {
    const response = await axiosInstance.post(
      `${API_V1_PREFIX}/doctor/sessions/${sessionId}/close`
    );
    return response.data;
  },
};

