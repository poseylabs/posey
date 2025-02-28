interface HeadersInit {
  [key: string]: string;
}

// Add these type declarations at the top
declare global {
  interface Window {
    document: Document;
  }
}

const API_BASE = process.env.NEXT_PUBLIC_AGENT_API_ENDPOINT || 'http://localhost:5555';
/**
 * Helper class for making API requests
 * 
 * @example
 * const api = new ApiHelper();
 * const response = await api.get('/conversations');
 * console.log(response);
 */
export class ApiHelper {
  apiBase: string;
  private accessToken?: string;

  constructor({
    apiBase = API_BASE,
    accessToken
  }: {
    apiBase?: string;
    accessToken?: string;
  }) {
    this.apiBase = apiBase;
    this.accessToken = accessToken;
  }

  setAccessToken(token: string) {
    this.accessToken = token;
  }

  clearAccessToken() {
    this.accessToken = undefined;
  }

  private async getHeaders(): Promise<HeadersInit> {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    if (this.accessToken) {
      headers['Authorization'] = `Bearer ${this.accessToken}`;
    }

    return headers;
  }

  async get(path: string) {
    const headers = await this.getHeaders();
    const response = await fetch(`${this.apiBase}${path}`, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      console.log('API Error:', { response, url: `${this.apiBase}${path}` });
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  async post(path: string, body: any) {
    const headers = await this.getHeaders();
    const response = await fetch(`${this.apiBase}${path}`, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  async put(path: string, body: any) {
    const headers = await this.getHeaders();
    const response = await fetch(`${this.apiBase}${path}`, {
      method: 'PUT',
      headers,
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  async delete(path: string) {
    const headers = await this.getHeaders();
    const response = await fetch(`${this.apiBase}${path}`, {
      method: 'DELETE',
      headers,
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }
}
