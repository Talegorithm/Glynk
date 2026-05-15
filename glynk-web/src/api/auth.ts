import client from './client';
import type { User, RegisterResponse, LoginResponse } from '../types/auth';

export async function register(data: {
  display_name?: string;
  email: string;
  password: string;
  code: string;
}): Promise<RegisterResponse> {
  const res = await client.post<RegisterResponse>('/auth/register', data);
  return res.data;
}

export async function requestRegisterCode(email: string): Promise<{ ok: boolean }> {
  const res = await client.post<{ ok: boolean }>('/auth/register/request-code', { email });
  return res.data;
}

export async function loginWithPassword(data: {
  email: string;
  password: string;
}): Promise<LoginResponse> {
  const res = await client.post<LoginResponse>('/auth/login', data);
  return res.data;
}

export async function loginByToken(token: string): Promise<LoginResponse> {
  const res = await client.get<LoginResponse>('/auth/me', {
    headers: { Authorization: `Bearer ${token}` },
  });
  return { ...res.data, token };
}

export async function getMe(): Promise<User> {
  const res = await client.get<User>('/auth/me');
  return res.data;
}
