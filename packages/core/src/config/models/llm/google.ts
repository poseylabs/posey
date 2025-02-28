import { LLMModel } from '@/types';

import {
  DEFAULT_MODEL_TEMP
} from './model-defaults';

export const GOOGLE_NAMESPACE = 'google';
export const GOOGLE_ADAPTER_NAME = 'Google';

// https://ai.google.dev/gemini-api/docs/models/gemini
export const GOOGLE_MODELS: LLMModel[] = [
  {
    id: 'gemini-2.0-flash',
    name: 'Gemini 2.0 Flash',
    provider: GOOGLE_NAMESPACE,
    description: 'Next-gen features and improved capabilities, including superior speed, native tool use, multimodal generation, and a 1M token context window.',
    contextWindow: 1048576, // 1M tokens
    defaultTemp: DEFAULT_MODEL_TEMP,
    maxTokens: 8192,
    ocrCapable: true
  },
  {
    id: 'gemini-2.0-flash-lite',
    name: 'Gemini 2.0 Flash-Lite',
    provider: GOOGLE_NAMESPACE,
    description: 'A Gemini 2.0 Flash model optimized for cost efficiency and low latency.',
    contextWindow: 1048576, // 1M tokens
    defaultTemp: DEFAULT_MODEL_TEMP,
    maxTokens: 8192,
    ocrCapable: true
  },
  {
    id: 'gemini-1.5-flash',
    name: 'Gemini 1.5 Flash',
    provider: GOOGLE_NAMESPACE,
    description: 'Fast and versatile multimodal model for scaling across diverse tasks.',
    contextWindow: 1048576, // 1M tokens
    defaultTemp: DEFAULT_MODEL_TEMP,
    maxTokens: 8192,
    ocrCapable: true
  },
  {
    id: 'gemini-1.5-pro',
    name: 'Gemini 1.5 Pro',
    provider: GOOGLE_NAMESPACE,
    description: 'Mid-size multimodal model optimized for complex reasoning tasks. Can process large amounts of data including 2 hours of video, 19 hours of audio, or 2,000 pages of text.',
    contextWindow: 2097152, // 2M tokens
    defaultTemp: DEFAULT_MODEL_TEMP,
    maxTokens: 8192,
    ocrCapable: true
  },
  {
    id: 'gemini-1.5-flash-8b',
    name: 'Gemini 1.5 Flash-8B',
    provider: GOOGLE_NAMESPACE,
    description: 'Small model designed for lower intelligence tasks with high throughput requirements.',
    contextWindow: 1048576, // 1M tokens
    defaultTemp: DEFAULT_MODEL_TEMP,
    maxTokens: 8192,
    ocrCapable: true
  }
];

export const DEFAULT_GOOGLE_MODEL = GOOGLE_MODELS[0]; 
