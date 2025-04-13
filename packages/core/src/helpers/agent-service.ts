import { AgentResponse, AgentState, AgentAbility } from '@/types/agent';
import { FetchResponse, JsonFetchResponse } from '@/types/network';
import { Message } from '@posey.ai/core';

interface ErrorResponse {
  message: string;
  code?: string;
  details?: Record<string, any>;
}

interface HealthResponse {
  status: string;
  checks?: Record<string, boolean>;
}

interface AbilitiesResponse {
  abilities: string[];
}

export class AgentService {
  private readonly baseUrl: string;
  private readonly agentName: string;

  constructor(agentName: string) {
    this.baseUrl = process.env.NEXT_PUBLIC_AGENT_API_ENDPOINT || 'http://localhost:5555';
    this.agentName = agentName;
  }

  /**
   * Handles API errors and transforms them into a standard format
   */
  private async handleAgentError(response: FetchResponse): Promise<never> {
    const error = await response.json() as ErrorResponse;
    throw new Error(error.message || 'Agent service request failed');
  }

  /**
   * Sends a message to the agent and gets its response
   */
  async call(payload: {
    messages: Message[];
    conversationId?: string;
    metadata?: Record<string, any>;
    files?: File[];
  }): Promise<JsonFetchResponse> {
    const { messages, conversationId, metadata, files } = payload;

    // Always use FormData as the endpoint expects multipart/form-data
    const formData = new FormData();
    const headers: HeadersInit = {}; // Keep headers for credentials potentially

    // Process messages to ensure metadata is a JSON string if it's an object
    const processedMessages = messages.map(message => ({
      ...message,
      // Use the correct field name 'metadata' from the Message interface
      metadata: (message.metadata !== null && typeof message.metadata === 'object') 
            ? JSON.stringify(message.metadata) 
            : message.metadata
    }));

    // Append JSON data as the 'payload' field, using processed messages
    const jsonData = JSON.stringify({ 
      messages: processedMessages, // Use the processed messages
      conversation_id: conversationId, // Keep sending snake_case as server aliases it
      metadata 
    });
    // Append the JSON string directly, not as a Blob
    formData.append('payload', jsonData);

    // Append files if they exist
    if (files && files.length > 0) {
      files.forEach((file) => {
        formData.append(`files`, file, file.name);
      });
    }

    // Browser sets Content-Type automatically for FormData with boundary
    // No need to set headers['Content-Type']

    const response: FetchResponse = await fetch(`${this.baseUrl}/orchestrator/${this.agentName}/run`, {
      method: 'POST',
      headers: headers, // Pass potentially modified headers (e.g., for credentials)
      credentials: 'include',
      body: formData, // Always send FormData
    });

    if (!response.ok) {
      await this.handleAgentError(response);
    }

    return response.json()
  }

  /**
   * Gets the health status of the agent service
   */
  async checkHealth(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/health`, {
        credentials: 'include',
      });

      if (!response.ok) {
        return false;
      }

      const data = await response.json() as HealthResponse;
      return data.status === 'healthy';
    } catch {
      return false;
    }
  }

  /**
   * Gets the list of available agent abilities
   */
  async getAbilities(): Promise<string[]> {
    const response = await fetch(`${this.baseUrl}/agent/${this.agentName}/abilities`, {
      credentials: 'include',
    });

    if (!response.ok) {
      await this.handleAgentError(response);
    }

    const data = await response.json() as AbilitiesResponse;
    return data.abilities;
  }

  /**
   * Executes a specific ability on the agent
   */
  async executeAbility(
    ability: string,
    params: Record<string, unknown>
  ): Promise<AgentResponse> {
    const response = await fetch(`${this.baseUrl}/agent/${this.agentName}/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        ability,
        params,
      }),
    });

    if (!response.ok) {
      await this.handleAgentError(response);
    }

    return response.json() as Promise<AgentResponse>;
  }

  /**
   * Gets the current state/memory of the agent
   */
  async getAgentState(): Promise<AgentState> {
    const response = await fetch(`${this.baseUrl}/agent/${this.agentName}/state`, {
      credentials: 'include',
    });

    if (!response.ok) {
      await this.handleAgentError(response);
    }

    return response.json() as Promise<AgentState>;
  }

  /**
   * Resets the agent's state/memory
   */
  async resetAgent(): Promise<void> {
    const response = await fetch(`${this.baseUrl}/agent/${this.agentName}/reset`, {
      method: 'POST',
      credentials: 'include',
    });

    if (!response.ok) {
      await this.handleAgentError(response);
    }
  }
}

// Update the singleton to use a default agent
export const agentService = new AgentService('posey');
