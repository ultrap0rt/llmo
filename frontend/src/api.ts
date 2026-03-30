import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

export const api = axios.create({
  baseURL: API_URL,
});

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  graph_context?: string;
}

export interface ChatSession {
  session_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages: Message[];
}

export const createSession = async (title: string = 'New Chat') => {
  const response = await api.post<ChatSession>('/sessions/', { title });
  return response.data;
};

export const getSession = async (sessionId: string) => {
  const response = await api.get<ChatSession>(`/sessions/${sessionId}/`);
  return response.data;
};

export const sendMessage = async (sessionId: string, message: string) => {
  const response = await api.post<{ response: string; message_id: string; timestamp: string }>(
    `/sessions/${sessionId}/message/`,
    { message }
  );
  return response.data;
};
