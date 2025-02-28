export interface LLMModel {
  id: string;
  name: string;
  provider: string;
  description: string;
  contextWindow: number;
  defaultTemp?: number;
  maxTokens?: number;
  ocrCapable?: boolean;
}

export interface LLMAdapter {
  default: LLMModel;
  models: LLMModel[];
  name: string;
}


export interface LLMConfig {
  adapters: {
    [key: string]: LLMAdapter;
  },
}
