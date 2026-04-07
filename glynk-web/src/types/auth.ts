export interface User {
  uid: string;
  email?: string;
  created_at?: string;
}

export interface RegisterResponse {
  uid: string;
  token: string;
}

export interface LoginResponse {
  uid: string;
  email?: string;
}
