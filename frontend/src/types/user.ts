export type UserRole = 'admin' | 'doctor' | 'nurse';

export interface User {
  user_id: string;
  username: string;
  email?: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  last_login?: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

