import axiosInstance from '../utils/axios';
import { API_V1_PREFIX } from '../config/api';
import {
  Patient,
  PatientSearchResult,
  PatientCreateRequest,
  PatientUpdateRequest,
} from '../types/patient';

export const patientService = {
  // Search patients
  searchPatients: async (query: string, limit: number = 20): Promise<PatientSearchResult[]> => {
    const response = await axiosInstance.get<PatientSearchResult[]>(
      `${API_V1_PREFIX}/patients/search`,
      { params: { q: query, limit } }
    );
    return response.data;
  },

  // Get patient by ID
  getPatient: async (patientId: string): Promise<Patient> => {
    const response = await axiosInstance.get<Patient>(
      `${API_V1_PREFIX}/patients/${patientId}`
    );
    return response.data;
  },

  // Create patient
  createPatient: async (patient: PatientCreateRequest): Promise<Patient> => {
    const response = await axiosInstance.post<Patient>(
      `${API_V1_PREFIX}/patients`,
      patient
    );
    return response.data;
  },

  // Update patient
  updatePatient: async (
    patientId: string,
    updates: PatientUpdateRequest
  ): Promise<Patient> => {
    const response = await axiosInstance.put<Patient>(
      `${API_V1_PREFIX}/patients/${patientId}`,
      updates
    );
    return response.data;
  },

  // Get patient portfolio (patient + sessions)
  getPatientPortfolio: async (patientId: string): Promise<any> => {
    const response = await axiosInstance.get(
      `${API_V1_PREFIX}/patients/${patientId}/portfolio`
    );
    return response.data;
  },
};

