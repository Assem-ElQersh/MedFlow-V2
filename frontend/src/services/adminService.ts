import axiosInstance from '../utils/axios';
import { API_V1_PREFIX } from '../config/api';

export interface LogEntry {
  log_id: string;
  timestamp: string;
  level: 'info' | 'warning' | 'error' | 'success';
  category: 'auth' | 'session' | 'system' | 'vlm' | 'admin';
  message: string;
  user_id?: string;
  user_name?: string;
  user_role?: string;
  session_id?: string;
  patient_id?: string;
  patient_name?: string;
  details?: Record<string, any>;
  ip_address?: string;
}

export interface LogStats {
  total: number;
  by_category: Record<string, number>;
  by_level: Record<string, number>;
}

export interface SystemStatus {
  mongodb: string;
  vlm_service: string;
  vlm_model?: string;
  vlm_device?: string;
  vlm_error?: string;
  timestamp?: string;
}

export const adminService = {
  // Get logs
  getLogs: async (params?: {
    category?: string;
    level?: string;
    limit?: number;
    skip?: number;
  }): Promise<LogEntry[]> => {
    const response = await axiosInstance.get<LogEntry[]>(
      `${API_V1_PREFIX}/admin/logs`,
      { params }
    );
    return response.data;
  },

  // Get log statistics
  getLogsStats: async (): Promise<LogStats> => {
    const response = await axiosInstance.get<LogStats>(
      `${API_V1_PREFIX}/admin/logs/stats`
    );
    return response.data;
  },

  // Get system status
  getSystemStatus: async (): Promise<SystemStatus> => {
    const response = await axiosInstance.get<SystemStatus>(
      `${API_V1_PREFIX}/admin/system/status`
    );
    return response.data;
  },
};
