export interface Capability {
  name: string;
  description: string;
  type: 'ability' | 'agent';
  parameters?: Record<string, any>;
}
