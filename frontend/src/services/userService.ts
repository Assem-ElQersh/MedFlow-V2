import axiosInstance from '../utils/axios';
import { API_V1_PREFIX } from '../config/api';

export const userService = {
  // Get all doctors (for dropdown in session creation)
  getDoctors: async (): Promise<any[]> => {
    // This endpoint should be added to backend
    // For now, we'll return empty array and implement it later
    try {
      const response = await axiosInstance.get(`${API_V1_PREFIX}/users?role=doctor`);
      return response.data;
    } catch (error) {
      // Return empty for now
      return [];
    }
  },
};

