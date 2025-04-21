import { useMemo } from 'react';
import { AgentResponse, AgentService, AgentState, Message } from '@posey.ai/core';

interface ErrorResponse {
  message: string;
  code?: string;
  details?: Record<string, any>;
}

class Agent {
  private readonly service: AgentService;

  constructor(agentName: string) {
    this.service = new AgentService(agentName);
  }

  private async handleAgentError(response: Response): Promise<never> {
    const error = await response.json() as ErrorResponse;
    throw new Error(error.message || 'Agent service request failed');
  }

  async call(params: {
    messages: Message[];
    conversationId?: string;
    metadata?: Record<string, any>;
    files?: File[];
  }): Promise<AgentResponse> {
    return await this.service.call(params) as AgentResponse;
  }

  async checkHealth(): Promise<boolean> {
    return this.service.checkHealth();
  }

  async getAbilities(): Promise<string[]> {
    return this.service.getAbilities();
  }

  async executeAbility(
    ability: string,
    params: Record<string, unknown>
  ): Promise<AgentResponse> {
    return this.service.executeAbility(ability, params);
  }

  async getState(): Promise<AgentState> {
    return this.service.getAgentState();
  }

  async reset(): Promise<void> {
    return this.service.resetAgent();
  }
}

export function useAgent(agentName: string) {
  return useMemo(() => new Agent(agentName), [agentName]);
} 
