import axios from 'axios';

const API_ENDPOINT = process?.env?.NEXT_PUBLIC_API_ENDPOINT || 'http://localhost:8888/api';

// Simplified sync version of uuid that works in browser but is less secure
export function uuid(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

// Secure async version of uuidv4 that generates a UUID on server
export async function uuidv4(): Promise<string> {
  try {
    const response = await axios.get(`${API_ENDPOINT}/crypto/uuid/v4`);
    if (response.data.success && response.data.uuid) {
      return response.data.uuid;
    }
    throw new Error('Failed to generate UUID v4');
  } catch (error) {
    console.error('Error generating UUID v4:', error);
    // Fallback to client-side generation if API fails
    return uuid()
  }
}

// Secure async version of uuidv5 that generates a UUID on server
export async function uuidv5(name: string, namespace?: string): Promise<string> {
  try {
    const params = new URLSearchParams({ name });
    if (namespace) {
      params.append('namespace', namespace);
    }
    const response = await axios.get(`${API_ENDPOINT}/crypto/uuid/v5?${params.toString()}`);
    if (response.data.success && response.data.uuid) {
      return response.data.uuid;
    }
    throw new Error('Failed to generate UUID v5');
  } catch (error) {
    console.error('Error generating UUID v5:', error);
    throw error;
  }
}
