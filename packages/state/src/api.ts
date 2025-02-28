import { Message } from '@posey.ai/core';
import axios from 'axios';

const AGENT_API_URL = `${process.env.NEXT_PUBLIC_AGENT_API_ENDPOINT}`;

interface Conversation {
  id: string;
  messages: Message[];
}

export const api = {
  // Conversation endpoints
  getAllConversations: async () => {
    const response = await axios.get(`${AGENT_API_URL}/conversations`);
    return response.data;
  },

  saveConversation: async (conversation: Conversation) => {
    const response = await axios.post(`${AGENT_API_URL}/conversations`, conversation);
    return response.data;
  },

  saveMessage: async (message: Message) => {
    const response = await axios.post(`${AGENT_API_URL}/messages`, message);
    return response.data;
  },

  updateConversation: async (id: string, updates: Partial<Conversation>) => {
    const response = await axios.put(`${AGENT_API_URL}/conversations/${id}`, updates);
    return response.data;
  },

  // Memory endpoints
  getMemoryContext: async (vector: number[]) => {
    const response = await axios.get(`${AGENT_API_URL}/memory/context`, {
      params: { vector }
    });
    return response.data;
  },

  getEnhancedContext: async (query: string, user_id: string, limit = 5) => {
    const response = await axios.get(`${AGENT_API_URL}/memory/enhanced-context`, {
      params: { query, user_id: user_id, limit }
    });
    return response.data;
  }
};