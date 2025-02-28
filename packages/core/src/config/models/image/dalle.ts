import { ImageModel } from '@/types';

export const DALLE_NAMESPACE = 'dalle';
export const DALLE_ADAPTER_NAME = 'DALL-E';
export const DALLE_VERSION = '';

export const DALLE_MODELS: ImageModel[] = [
  {
    id: 'dall-e-2',
    name: 'DALL-E 2',
    provider: DALLE_NAMESPACE,
    description: '',
  },
  {
    id: 'dall-e-3',
    name: 'DALL-E 3',
    provider: DALLE_NAMESPACE,
    description: '',
  },
];

export const DEFAULT_DALLE_MODEL = DALLE_MODELS[0];
