import { Capability } from '../types';

export const SYSTEM_CAPABILITIES: Capability[] = [
  {
    name: 'image_generation',
    description: 'Generate images from text descriptions',
    type: 'ability',
    parameters: {
      adapters: ['dalle', 'stable-diffusion', 'flux']
    }
  },
  {
    name: 'translation',
    description: 'Translate text between languages',
    type: 'ability',
    parameters: {
      supportedLanguages: ['en', 'vi']
    }
  },
  {
    name: 'speech',
    description: 'Convert text to speech',
    type: 'ability',
    parameters: {
      voices: ['default', 'male', 'female']
    }
  },
  {
    name: "internet_search",
    description: "Search the internet for current information",
    type: "ability",
    parameters: {
      adapters: ["default"],
      maxRetries: 3,
      rateLimitDelay: 1000
    }
  },
  // Add other capabilities
]; 
