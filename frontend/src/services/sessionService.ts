import axiosInstance from '../utils/axios';
import { API_V1_PREFIX } from '../config/api';
import { Session, SessionCreate, UploadedFile, FileType } from '../types/session';

export const sessionService = {
  // Create session
  createSession: async (session: SessionCreate): Promise<Session> => {
    const response = await axiosInstance.post<Session>(
      `${API_V1_PREFIX}/sessions`,
      session
    );
    return response.data;
  },

  // Get session
  getSession: async (sessionId: string): Promise<Session> => {
    const response = await axiosInstance.get<Session>(
      `${API_V1_PREFIX}/sessions/${sessionId}`
    );
    return response.data;
  },

  // Update session
  updateSession: async (sessionId: string, updates: Partial<SessionCreate>): Promise<Session> => {
    const response = await axiosInstance.put<Session>(
      `${API_V1_PREFIX}/sessions/${sessionId}`,
      updates
    );
    return response.data;
  },

  // Upload file
  uploadFile: async (
    sessionId: string,
    file: File,
    fileType: FileType
  ): Promise<UploadedFile> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('file_type', fileType);

    const response = await axiosInstance.post<UploadedFile>(
      `${API_V1_PREFIX}/sessions/${sessionId}/files`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },

  // Delete file
  deleteFile: async (sessionId: string, fileId: string): Promise<void> => {
    await axiosInstance.delete(`${API_V1_PREFIX}/sessions/${sessionId}/files/${fileId}`);
  },

  // Get file URL
  getFileUrl: async (sessionId: string, fileId: string): Promise<string> => {
    const response = await axiosInstance.get<{ url: string }>(
      `${API_V1_PREFIX}/sessions/${sessionId}/files/${fileId}/url`
    );
    return response.data.url;
  },

  // Submit session
  submitSession: async (sessionId: string): Promise<Session> => {
    const response = await axiosInstance.post<Session>(
      `${API_V1_PREFIX}/sessions/${sessionId}/submit`
    );
    return response.data;
  },

  // Delete session
  deleteSession: async (sessionId: string): Promise<void> => {
    await axiosInstance.delete(`${API_V1_PREFIX}/sessions/${sessionId}`);
  },
};

