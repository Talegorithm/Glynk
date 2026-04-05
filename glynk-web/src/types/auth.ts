export interface User {
  uid: string;
  email: string;
  name?: string;
  created_at?: string;
}

export interface RegisterResponse {
  uid: string;
  email: string;
  name?: string;
  token: string;
}

export interface LoginResponse {
  uid: string;
  email: string;
  name?: string;
  token: string;
}
