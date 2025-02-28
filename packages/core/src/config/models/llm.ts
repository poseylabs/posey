// Models
import {
  ANTHROPIC_MODELS,
  ANTHROPIC_NAMESPACE,
  ANTHROPIC_ADAPTER_NAME,
  DEFAULT_ANTHROPIC_MODEL
} from './llm/anthropic';

import {
  OPENAI_MODELS,
  OPENAI_NAMESPACE,
  OPENAI_ADAPTER_NAME,
  DEFAULT_OPENAI_MODEL
} from './llm/openai';

import {
  OLLAMA_NAMESPACE,
  getOllamaModels,
} from './llm/ollama';

// Types
import { LLMAdapter, LLMConfig, LLMModel } from '@/types/llm';
import { IMAGE_CONFIG } from './image';

// Model Config
export const LLM_MODELS: LLMModel[] = [
  ...ANTHROPIC_MODELS,
  ...OPENAI_MODELS,
];

export const getLLMModelById = (id: string): LLMModel | undefined => {
  return LLM_MODELS.find(model => model.id === id);
};

export const defaultModel: any = getLLMModelById('claude-3-5-sonnet-latest');

export const LLM_ADAPTERS: { [key: string]: LLMAdapter } = {
  [ANTHROPIC_NAMESPACE]: {
    default: DEFAULT_ANTHROPIC_MODEL,
    models: ANTHROPIC_MODELS,
    name: ANTHROPIC_ADAPTER_NAME,
  },
  [OPENAI_NAMESPACE]: {
    default: DEFAULT_OPENAI_MODEL,
    models: OPENAI_MODELS,
    name: OPENAI_ADAPTER_NAME,
  }
};

export const DEFAULT_LLM_ADAPTER = LLM_ADAPTERS[ANTHROPIC_NAMESPACE];

// Model Config
export const LLM_CONFIG: LLMConfig = {
  adapters: {
    ...LLM_ADAPTERS,
    default: DEFAULT_LLM_ADAPTER
  }
}

export async function getAllLLMModels(): Promise<LLMModel[]> {
  const ollamaModels = await getOllamaModels();
  return [...LLM_MODELS, ...ollamaModels];
}

export async function getUpdatedLLMAdapters(): Promise<{ [key: string]: LLMAdapter }> {
  const ollamaModels = await getOllamaModels();
  return {
    ...LLM_ADAPTERS,
    [OLLAMA_NAMESPACE]: {
      ...LLM_ADAPTERS[OLLAMA_NAMESPACE],
      models: ollamaModels,
    }
  };
}

export const ModelsConfig = {
  llm: LLM_CONFIG,
  image: IMAGE_CONFIG
}
