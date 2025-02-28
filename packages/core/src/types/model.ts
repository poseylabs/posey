import { ImageConfig } from './image';
import { LLMConfig } from './llm'

export interface ModelsConfig {
  llm: LLMConfig;
  image: ImageConfig;
}
