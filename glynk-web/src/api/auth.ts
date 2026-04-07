import client from './client';
import type { User, RegisterResponse, LoginResponse } from '../types/auth';

export async function register(data: {
  uid: string;
  email?: string;
}): Promise<RegisterResponse> {
  const res = await client.post<RegisterResponse>('/users', data);
  return res.data;
}

export async function loginByToken(token: string): Promise<LoginResponse> {
  const res = await client.post<LoginResponse>('/users/login', { token });
  return res.data;
}

export async function getMe(): Promise<User> {
  const res = await client.get<User>('/users/me');
  return res.data;
}
