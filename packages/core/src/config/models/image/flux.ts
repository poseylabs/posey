import { ImageModel } from '@/types';

export const FLUX_NAMESPACE = 'flux';
export const FLUX_ADAPTER_NAME = 'Flux';
export const FLUX_VERSION = 'v1';

export const FLUX_MODELS: ImageModel[] = [
  {
    id: 'flux-pro-1.1-ultra',
    name: 'Flux Pro 1.1 Ultra',
    path: `${FLUX_VERSION}/flux-pro-1.1-ultra`,
    provider: FLUX_NAMESPACE,
    description: 'Most intelligent model. Highest level of intelligence and capability. Multilingual. Vision Message Batches API.',
  },
  {
    id: 'flux-pro-1.1',
    name: 'Flux Pro 1.1',
    path: `${FLUX_VERSION}/flux-pro-1.1`,
    provider: FLUX_NAMESPACE,
    description: 'Our fastest model. Intelligence at blazing speeds',
  },
  {
    id: 'flux-pro',
    name: 'Flux Pro',
    path: `${FLUX_VERSION}/flux-pro`,
    provider: FLUX_NAMESPACE,
    description: 'Our fastest model. Intelligence at blazing speeds',
  },
  {
    id: 'flux-dev',
    name: 'Flux Dev',
    path: `${FLUX_VERSION}/flux-dev`,
    provider: FLUX_NAMESPACE,
    description: 'Our fastest model. Intelligence at blazing speeds',
  },
  {
    id: 'flux-pro-1.0-fill',
    name: 'Flux Pro 1.0 Fill',
    path: `${FLUX_VERSION}/flux-pro-1.0-fill`,
    provider: FLUX_NAMESPACE,
    description: 'Our fastest model. Intelligence at blazing speeds',
  },
  {
    id: 'flux-pro-1.0-canny',
    name: 'Flux Pro 1.0 Canny',
    path: `${FLUX_VERSION}/flux-pro-1.0-canny`,
    provider: FLUX_NAMESPACE,
    description: 'Our fastest model. Intelligence at blazing speeds',
  },
  {
    id: 'flux-pro-1.0-depth',
    name: 'Flux Pro 1.0 Depth',
    path: `${FLUX_VERSION}/flux-pro-1.0-depth`,
    provider: FLUX_NAMESPACE,
    description: 'Our fastest model. Intelligence at blazing speeds',
  },
];

export const DEFAULT_FLUX_MODEL = FLUX_MODELS[0];
