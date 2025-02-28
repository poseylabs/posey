import { LLMModel } from '@/types';

import {
  MAX_TOKENS_SMALL,
  DEFAULT_MODEL_CONTEXT_WINDOW,
  DEFAULT_MODEL_TEMP
} from './model-defaults';

export const ANTHROPIC_NAMESPACE = 'anthropic';
export const ANTHROPIC_ADAPTER_NAME = 'Anthropic';

// https://docs.anthropic.com/en/docs/about-claude/models
export const ANTHROPIC_MODELS: LLMModel[] = [
  {
    id: 'claude-3-5-sonnet-latest',
    name: 'Claude 3.5 Sonnet',
    provider: ANTHROPIC_NAMESPACE,
    description: 'Most intelligent model. Highest level of intelligence and capability. Multilingual. Vision Message Batches API.',
    contextWindow: DEFAULT_MODEL_CONTEXT_WINDOW,
    defaultTemp: DEFAULT_MODEL_TEMP,
    maxTokens: MAX_TOKENS_SMALL,
    ocrCapable: true
  },
  {
    id: 'claude-3-5-haiku-latest',
    name: 'Claude 3.5 Haiku',
    provider: ANTHROPIC_NAMESPACE,
    description: 'Our fastest model. Intelligence at blazing speeds',
    contextWindow: DEFAULT_MODEL_CONTEXT_WINDOW,
    defaultTemp: DEFAULT_MODEL_TEMP,
    maxTokens: MAX_TOKENS_SMALL,
    ocrCapable: true
  },
];

export const DEFAULT_ANTHROPIC_MODEL = ANTHROPIC_MODELS[0];
