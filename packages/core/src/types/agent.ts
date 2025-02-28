import { LLMModel } from './llm';
import { Capability } from './capabilities';

export interface Agent {
  id: string;
  name: string;
  avatar: string;
  description: string;
  capabilities: Capability[];
  adapter: string;
  model: LLMModel;
  prompts: string[];
}

export interface AgentRequest {
  message: string;
  context?: Record<string, any>;
  metadata?: {
    userId?: string;
    sessionId?: string;
    timestamp?: number;
  };
}

export interface AgentResponse {
  message: string;
  confidence: number;
  metadata?: {
    abilities?: string[];
    duration?: number;
    tokens?: {
      prompt: number;
      completion: number;
      total: number;
    };
    model?: string;
    timestamp?: number;
  };
  error?: {
    code: string;
    message: string;
    details?: Record<string, any>;
  };
}

export interface AgentState {
  memory: Record<string, any>;
  context: Record<string, any>;
  abilities: string[];
  lastUpdated: number;
}

export interface AgentAbility {
  id: string;
  name: string;
  description: string;
  parameters: {
    name: string;
    type: string;
    description: string;
    required: boolean;
    default?: any;
  }[];
}
