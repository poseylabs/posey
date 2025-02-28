// Models
import {
  FLUX_ADAPTER_NAME,
  FLUX_MODELS,
  FLUX_NAMESPACE,
  DEFAULT_FLUX_MODEL
} from './image/flux';

import {
  DALLE_ADAPTER_NAME,
  DALLE_MODELS,
  DALLE_NAMESPACE,
  DEFAULT_DALLE_MODEL
} from './image/dalle';

import {
  STABILITY_ADAPTER_NAME,
  STABILITY_MODELS,
  STABILITY_NAMESPACE,
  DEFAULT_STABILITY_MODEL
} from './image/stability';

import { ImageAdapter, ImageConfig } from '@/types/image';

export const IMAGE_MODELS = {
  flux: FLUX_MODELS,
  dalle: DALLE_MODELS,
  stability: STABILITY_MODELS
} as const;

export const IMAGE_ADAPTERS: { [key: string]: ImageAdapter } = {
  [DALLE_NAMESPACE]: {
    default: DEFAULT_DALLE_MODEL,
    models: DALLE_MODELS,
    name: DALLE_ADAPTER_NAME,
  },
  [FLUX_NAMESPACE]: {
    default: DEFAULT_FLUX_MODEL,
    models: FLUX_MODELS,
    name: FLUX_ADAPTER_NAME,
  },
  [STABILITY_NAMESPACE]: {
    default: DEFAULT_STABILITY_MODEL,
    models: STABILITY_MODELS,
    name: STABILITY_ADAPTER_NAME,
  }
}

export const DEFAULT_IMAGE_ADAPTER_NAME = FLUX_NAMESPACE;
export const DEFAULT_IMAGE_ADAPTER: ImageAdapter = IMAGE_ADAPTERS[FLUX_NAMESPACE];

// Model Config
export const IMAGE_CONFIG: ImageConfig = {
  adapters: {
    ...IMAGE_ADAPTERS,
    default: DEFAULT_IMAGE_ADAPTER
  },
}


