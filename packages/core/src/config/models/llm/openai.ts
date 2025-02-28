import { LLMModel } from '@/types';

import {
  MAX_TOKENS_LARGE,
  MAX_TOKENS_XL,
  DEFAULT_MODEL_CONTEXT_WINDOW,
  DEFAULT_MODEL_TEMP
} from './model-defaults';

export const OPENAI_NAMESPACE = 'openai';
export const OPENAI_ADAPTER_NAME = 'OpenAI';

// https://platform.openai.com/docs/models
export const OPENAI_MODELS: LLMModel[] = [
  {
    id: 'o3-mini',
    name: 'Chat GPT o3-mini',
    provider: OPENAI_NAMESPACE,
    description: 'o3-mini is our most recent small reasoning model, providing high intelligence at the same cost and latency targets of o1-mini. o3-mini also supports key developer features, like Structured Outputs, function calling, Batch API, and more. Like other models in the o-series, it is designed to excel at science, math, and coding tasks.',
    contextWindow: DEFAULT_MODEL_CONTEXT_WINDOW,
    defaultTemp: DEFAULT_MODEL_TEMP,
    maxTokens: MAX_TOKENS_LARGE,
    ocrCapable: false
  },
  {
    id: 'o1',
    name: 'Chat GPT o1',
    provider: OPENAI_NAMESPACE,
    description: '',
    contextWindow: DEFAULT_MODEL_CONTEXT_WINDOW,
    defaultTemp: DEFAULT_MODEL_TEMP,
    maxTokens: MAX_TOKENS_LARGE,
    ocrCapable: true
  },
  {
    id: 'o1-mini',
    name: 'Chat GPT o1-mini',
    provider: OPENAI_NAMESPACE,
    description: 'The o1 series of large language models are trained with reinforcement learning to perform complex reasoning. o1 models think before they answer, producing a long internal chain of thought before responding to the user. Learn about the capabilities and limitations of o1 models in our reasoning guide. o1-mini: faster and cheaper reasoning model particularly good at coding, math, and science.',
    contextWindow: DEFAULT_MODEL_CONTEXT_WINDOW,
    defaultTemp: DEFAULT_MODEL_TEMP,
    maxTokens: MAX_TOKENS_XL,
    ocrCapable: false
  },
  {
    id: 'gpt-4o',
    name: 'Chat GPT 4o',
    provider: OPENAI_NAMESPACE,
    description: 'multimodal (accepting text or image inputs and outputting text), and it has the same high intelligence as GPT-4 Turbo but is much more efficient—it generates text 2x faster and is 50% cheaper. Additionally, GPT-4o has the best vision and performance across non-English languages of any of our models.',
    contextWindow: DEFAULT_MODEL_CONTEXT_WINDOW,
    defaultTemp: DEFAULT_MODEL_TEMP,
    maxTokens: MAX_TOKENS_LARGE,
    ocrCapable: true
  },
  {
    id: 'gpt-4o-mini',
    name: 'Chat GPT 4o Mini',
    provider: OPENAI_NAMESPACE,
    description: 'GPT-4o mini (“o” for “omni”) is our most advanced model in the small models category, and our cheapest model yet. It is multimodal (accepting text or image inputs and outputting text), has higher intelligence than gpt-3.5-turbo but is just as fast. It is meant to be used for smaller tasks, including vision tasks.',
    contextWindow: DEFAULT_MODEL_CONTEXT_WINDOW,
    defaultTemp: DEFAULT_MODEL_TEMP,
    maxTokens: MAX_TOKENS_LARGE,
    ocrCapable: true
  },
  {
    id: 'gpt-4o-realtime-preview',
    name: 'Chat GPT 4o Realtime Preview',
    provider: OPENAI_NAMESPACE,
    description: '',
    contextWindow: DEFAULT_MODEL_CONTEXT_WINDOW,
    defaultTemp: DEFAULT_MODEL_TEMP,
    maxTokens: MAX_TOKENS_LARGE,
    ocrCapable: true
  },
  {
    id: 'gpt-4o-mini-realtime-preview',
    name: 'Chat GPT 4o Mini Realtime Preview',
    provider: OPENAI_NAMESPACE,
    description: '',
    contextWindow: DEFAULT_MODEL_CONTEXT_WINDOW,
    defaultTemp: DEFAULT_MODEL_TEMP,
    maxTokens: MAX_TOKENS_LARGE,
    ocrCapable: true
  },
  {
    id: 'gpt-4o-audio-preview',
    name: 'Chat GPT 4o Audio Preview',
    provider: OPENAI_NAMESPACE,
    description: '',
    contextWindow: DEFAULT_MODEL_CONTEXT_WINDOW,
    defaultTemp: DEFAULT_MODEL_TEMP,
    maxTokens: MAX_TOKENS_LARGE,
    ocrCapable: true
  }
];

export const DEFAULT_OPENAI_MODEL = OPENAI_MODELS[0];
