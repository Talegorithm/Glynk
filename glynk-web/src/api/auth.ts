import client from './client';
import type { User, RegisterResponse, LoginResponse } from '../types/auth';

export async function sendVerifyCode(email: string): Promise<void> {
  await client.post('/auth/verify-code', { email });
}

export async function register(data: {
  uid: string;
  email: string;
  code: string;
  name?: string;
}): Promise<RegisterResponse> {
  const res = await client.post<RegisterResponse>('/auth/register', data);
  return res.data;
}

export async function loginByEmail(email: string, code: string): Promise<LoginResponse> {
  const res = await client.post<LoginResponse>('/auth/login', { email, code });
  return res.data;
}

export async function loginByToken(token: string): Promise<User> {
  const res = await client.get<User>('/users/me', {
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.data;
}

export async function getMe(): Promise<User> {
  const res = await client.get<User>('/users/me');
  return res.data;
}
