import axiosInstance from '../utils/axios';
import { API_V1_PREFIX } from '../config/api';

export interface DashboardStats {
  total_patients: number;
  
  // Nurse stats
  active_sessions?: number;
  created_today?: number;
  pending_review?: number;
  
  // Doctor stats
  assigned_to_me?: number;
  currently_reviewing?: number;
  completed_today?: number;
  total_assigned?: number;
  
  // Admin stats
  total_users?: number;
  total_sessions?: number;
}

export const dashboardService = {
  // Get dashboard statistics
  getStats: async (): Promise<DashboardStats> => {
    const response = await axiosInstance.get<DashboardStats>(
      `${API_V1_PREFIX}/dashboard/stats`
    );
    return response.data;
  },
};

