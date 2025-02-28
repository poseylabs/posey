import { LLMModel } from '@/types';
import {
  MAX_TOKENS_MEDIUM,
  DEFAULT_MODEL_CONTEXT_WINDOW,
  DEFAULT_MODEL_TEMP
} from './model-defaults';
import ollama from 'ollama/browser';

export const OLLAMA_NAMESPACE = 'ollama';
export const OLLAMA_ADAPTER_NAME = 'Ollama';

// Function to fetch available Ollama models
export async function getOllamaModels(): Promise<LLMModel[]> {

  try {
    const response = await ollama.list();
    return response.models.map(model => ({
      id: model.name,
      name: model.name,
      provider: OLLAMA_NAMESPACE,
      description: `Local Ollama model: ${model.name}`,
      contextWindow: DEFAULT_MODEL_CONTEXT_WINDOW,
      defaultTemp: DEFAULT_MODEL_TEMP,
      maxTokens: MAX_TOKENS_MEDIUM,
      ocrCapable: true
    }));
  } catch (error) {
    console.error('Error fetching Ollama models:', error);
    return [];
  }
}

// Export a default model for initial state
export const DEFAULT_OLLAMA_MODEL: LLMModel = {
  id: 'llama2',  // Using a common default
  name: 'Llama 2',
  provider: OLLAMA_NAMESPACE,
  description: 'Default Ollama model',
  contextWindow: DEFAULT_MODEL_CONTEXT_WINDOW,
  defaultTemp: DEFAULT_MODEL_TEMP,
  maxTokens: MAX_TOKENS_MEDIUM,
  ocrCapable: true
};
