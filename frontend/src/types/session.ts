export type SessionType = 'new_problem' | 'follow_up';

export type SessionStatus =
  | 'draft'
  | 'submitted'
  | 'vlm_processing'
  | 'awaiting_doctor'
  | 'doctor_reviewing'
  | 'completed'
  | 'pending_tests'
  | 'vlm_failed';

export type FileType = 'xray' | 'ct' | 'lab_result' | 'ecg' | 'report' | 'other';

export interface UploadedFile {
  file_id: string;
  file_name: string;
  file_type: FileType;
  file_path: string;
  mime_type: string;
  file_size_mb: number;
  upload_timestamp: string;
  uploaded_by: string;
  can_delete: boolean;
}

export interface SessionCreate {
  patient_id: string;
  session_type: SessionType;
  assigned_doctor_id: string;
  chief_complaint: string;
  current_state_description: string;
}

export interface Session extends SessionCreate {
  session_id: string;
  patient_name: string;
  assigned_doctor_name: string;
  nurse_id: string;
  nurse_name: string;
  session_date: string;
  session_status: SessionStatus;
  parent_session_id?: string;
  child_session_id?: string;
  uploaded_files: UploadedFile[];
  vlm_initial_status: string;
  vlm_initial_output?: any;
  vlm_chat_history: any[];
  doctor_id?: string;
  doctor_name?: string;
  diagnosis?: any;
  pending_tests?: any;
  created_at: string;
  created_by: string;
}

export interface Doctor {
  user_id: string;
  full_name: string;
}

