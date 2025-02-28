export interface ImageGenerationOptions {
  width?: number;
  height?: number;
  steps?: number;
  cfgScale?: number;
  samples?: number;
  guidanceScale?: number;
  negativePrompt?: string;
  quality?: string;
  style?: string;
  seed?: number;
  image?: string;
  strength?: number;
  aspectRatio?: string;
  outputFormat?: string;
  sampler?: string;
  output_format?: string;
  style_preset?: string;
}

export interface ImageGenerationResponse {
  imageUrl: string;
  agentResponse?: string;
  suggestedPrompt?: string;
  metadata?: Record<string, any>;
}

export interface ImageModel {
  id: string;
  name: string;
  provider: string;
  description: string;
  path?: string;
}

export interface ImageAdapter {
  default: ImageModel;
  models: ImageModel[];
  name: string;
}

export interface ImageConfig {
  adapters: {
    [key: string]: ImageAdapter;
  };
}

export interface ImageDefaults {
  adapter?: string;
  model?: string;
  defaultOptions?: ImageGenerationOptions;
}
