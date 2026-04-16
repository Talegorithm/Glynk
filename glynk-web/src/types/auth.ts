export interface User {
  entity_id: string;
  display_name?: string;
  email?: string;
  kind?: string;
  state?: string;
  created_at?: string;
}

export interface RegisterResponse {
  entity_id: string;
  token: string;
}

export interface LoginResponse {
  entity_id: string;
  display_name?: string;
  email?: string;
}
