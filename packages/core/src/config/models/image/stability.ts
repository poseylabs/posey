import { ImageModel } from '@/types';

export const STABILITY_NAMESPACE = 'stability';
export const STABILITY_ADAPTER_NAME = 'Stable Diffusion';
export const STABILITY_VERSION = '';

export const STABILITY_MODELS: ImageModel[] = [
  {
    id: 'ultra',
    name: 'Stable Diffusion Ultra',
    provider: STABILITY_NAMESPACE,
    description: '',
  },
  {
    id: 'core',
    name: 'Stable Diffusion Core',
    provider: STABILITY_NAMESPACE,
    description: '',
  },
  {
    id: 'stable-diffusion-3.5',
    name: 'Stable Diffusion 3.5',
    provider: STABILITY_NAMESPACE,
    description: '',
  },
];

export const DEFAULT_STABILITY_MODEL = STABILITY_MODELS[0];
