import { FetchResponse } from '../types/network';

const AGENT_API = process.env.NEXT_PUBLIC_AGENT_API_ENDPOINT || 'http://localhost:5555';

export const agentService = {
  async call(message: string) {
    const response: FetchResponse = await fetch(`${AGENT_API}/posey/run`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // Make sure we're sending the auth token
        // @ts-ignore: Handling localStorage in Next.js
        'Authorization': `Bearer ${localStorage.getItem('session_token')}`,
        // If using cookies, ensure credentials are included
        credentials: 'include'
      },
      body: JSON.stringify({
        prompt: message
      })
    });

    if (!response.ok) {
      if (response.status === 403) {
        throw new Error('Not authorized to access this agent');
      }
      throw new Error('Failed to call agent');
    }

    return await response.json();
  }
}; 
