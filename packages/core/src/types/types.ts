import { UserPreferences, UserRole } from './user';
import { LLMMessage, Message } from './conversation';

export interface EmbeddingFunction {
  (params: { text: string; adapter: string }): Promise<number[]>;
}

export enum HumanRelation {
  FAMILY = 'family',
  FRIEND = 'friend',
  COLLEAGUE = 'colleague',
  ACQUAINTANCE = 'acquaintance',
  STRANGER = 'stranger'
}

export enum FamilyRole {
  PARENT = 'parent',
  CHILD = 'child',
  SPOUSE = 'spouse',
  SIBLING = 'sibling',
  GRANDPARENT = 'grandparent',
  AUNT_UNCLE = 'aunt_uncle',
  COUSIN = 'cousin',
  OTHER = 'other'
}

export interface Human {
  id: string;
  name: string;
  relation: HumanRelation;
  dateFirstMet?: Date;
  preferences?: {
    nickname?: string;
    pronouns?: string;
    communicationStyle?: string;
    interests?: string[];
    languages?: string[];
  };
  metadata?: {
    birthday?: Date;
    location?: string;
    occupation?: string;
    contactInfo?: {
      email?: string;
      phone?: string;
    };
    lastInteraction?: Date;
    interactionCount?: number;
    trustLevel?: number; // 0-100
  };
  accessLevel: 'admin' | 'member' | 'guest' | 'none';
}

export interface FamilyMember extends Human {
  familyRole: FamilyRole;
  familyId: string;
  householdId?: string; // For tracking different households within a family
  emergencyContact?: boolean;
  guardianOf?: string[]; // IDs of family members this person is guardian of
  guardianIs?: string[]; // IDs of family members who are guardians of this person
}

export interface Family {
  id: string;
  name: string;
  members: FamilyMember[];
  households: {
    id: string;
    name: string;
    address?: string;
    members: string[]; // Member IDs
  }[];
  sharedMemories: string[]; // Memory IDs
  metadata?: {
    dateCreated: Date;
    traditions?: string[];
    importantDates?: {
      date: Date;
      description: string;
    }[];
  };
}

export enum MemoryCategory {
  ASSISTANT = 'assistant', // Assistant messages
  CORE = 'core',           // Important personal details, preferences
  CONVERSATION = 'conversation', // Regular chat history
  EVENT = 'event',         // Specific events or occasions
  RELATIONSHIP = 'relationship', // Information about relationships
  PREFERENCE = 'preference',  // User preferences and habits
  SYSTEM = 'system',          // System messages, notifications, and errors
  OTHER = 'other'            // Anything else that doesn't fit the above categories
}

export interface MemoryMetadata {
  type?: string;
  source?: string;
  timestamp?: number;
  user_id?: string;
  conversation_id?: string;
  message_id?: string;
  embedding?: number[];
  text?: string;
  metadata?: any;
  requested_actions?: Array<{
    type: string;
    parameters: any;
    reason: string;
  }>;
  [key: string]: any;
}


export interface MemoryOptions {
  accessLevel: 'private' | 'family' | 'public';
  metadata?: MemoryMetadata;
}

export interface AddMemoryParams {
  input: any;
  response: any;
  user_id: string;
  category: MemoryCategory;
  options: MemoryOptions;
}

export interface AddMemoryFunction {
  (params: AddMemoryParams): Promise<void>;
}

export interface AnalyzerService {
  clearAllMemories(): Promise<void>;
  addMemory(input: string, output: string, user_id: string, category: MemoryCategory, metadata?: MemoryOptions): Promise<void>;
  getRelevantMemories(input: string, limit: number): Promise<MemoryRecord[]>;
  getRelevantMemoriesByCategories(
    input: string,
    categories: MemoryCategory[],
    limit?: number,
    user_id?: UUID
  ): Promise<MemoryType[]>;
}

export interface MemoryPayload {
  content: string;
  metadata?: Record<string, any>;
  agent_id: string;
  context_type: string;
  embedding_model?: string;
  classification?: MemoryClassification;
  source_type?: 'user_interaction' | 'system_event' | 'agent_observation' | 'integration_event';
  importance_score?: number;
  timestamp?: string;
  response?: any;
  user_id?: string;
  category?: MemoryCategory;
  input?: string;
  output?: string;
  importance?: number;
  retention?: string;
  tags?: string[];
}

export interface MemoryRecord {
  input: string;
  output: string;
}

export interface AbilityProcessor {
  /** The current input/request to process */
  input: string;
  /** The formatted messages for the LLM */
  messages?: LLMMessage[];
  /** Full message history for context */
  threadMessages?: Message[];
  /** System prompt override for this request */
  systemPrompt?: string;
  /** Additional context prompt for this request */
  contextPrompt?: string;
  /** Conversation ID for tracking */
  conversationId?: string;
  /** User ID making the request */
  user_id?: string;
  /** User's role/permissions */
  userRole?: UserRole;
  /** Relevant memories for context */
  memories?: any[];
  /** Media attachments */
  media?: Array<{
    type: string;
    url?: string;
    metadata?: any;
  }>;
}

// Promise<{ response: string, targetLang: string, conversationId: string }>
export interface AbilityProcessReturn {
  response: string,
  targetLang?: string,
  conversationId: string | undefined,
  parameters?: Record<string, any>
}

export interface ModelClient {
  generateResponse(input: string): Promise<{ message: { generated_text: string }[] }>;
  loadModel(modelName: string): Promise<void>;
  unloadModel(modelName: string): Promise<void>;
}

export interface ModelConfig {
  // name: string;
  // parameters: Record<string, unknown>;
}

export interface PersonaConfig {
  name: string;
  traits: string[];
  background: string;
}

export interface ThoughtAdapter {
  initialize(): Promise<void>;
  close(): Promise<void>;
  generateEmbedding(text: string): Promise<number[]>;
  process(params: AbilityProcessor): Promise<{
    response: any;
    conversationId?: string;
    analyzerStatus?: any;
    memories?: any[];
  }>;
  generateConversationTitle(messages: Message[]): string;
  getModelInfo(): {
    name: string;
    provider: string;
    contextWindow: number;
  };
  setModel(model: string): void;
  analyzeContentUsage?(messages: LLMMessage[]): Promise<number>;
}

export interface SpeechOptions {
  voice?: string;
  language?: string;
  seed?: number;
  text?: string;
  stream?: boolean;
  voiceSettings?: {
    stability?: number;
    similarityBoost?: number;
    useSpeakerBoost?: boolean;
  };
}

export interface SpeechAdapter {
  getVoices(): Promise<Voice[]>;
  synthesize(text: string, options?: SpeechOptions): Promise<ArrayBuffer | ReadableStream>;
}

export interface SpeechResponse {
  type: 'stream' | 'buffer';
  data: ReadableStream | ArrayBuffer;
}

export interface Voice {
  id: string;
  name: string;
  language: string;
  voice_id: string;
}

export interface TranslatorAgent {
  detectLanguage(text: string): Promise<string>;
  translate(text: string, fromLang: string, toLang: string): Promise<string>;
  validateTranslation(text: string, translation: string): Promise<boolean>;
}

export interface TranslationResult {
  detectedLanguage: string;
  translatedText: string;
  confidence: number;
  targetLanguage?: string;
  error?: boolean;
}

export interface TranslatorConfig {
  apiUrl?: string;
  skipApiCheck?: boolean;
  sourceLanguage?: string;
  targetLanguage?: string;
  model?: string;
  adapter?: string;
}

export interface TranslatorAdapter {
  translate(text: string, from: string, to: string): Promise<TranslationResult>;
  detectLanguage(text: string): Promise<string>;
}

// MEMORY

export interface MemoryClassification {
  category: string;
  confidence: number;
  subcategories: string[];
  importance_score: number;  // 1-10
  retention_period?: string;  // "1d", "1w", "1m", "permanent"
  tags: string[];
}

export interface MemoryClassificationRequest {
  content: string;
  context: Record<string, any>;
  category?: MemoryCategory;
}

// Add these types if they don't exist already
export interface MemoryTimeRange {
  start?: Date;
  end?: Date;
}

export interface MemorySearchQuery {
  query: string;
  agent_id?: UUID5;
  context_type?: string;
  limit?: number;  // 1-50
  min_relevance_score?: number;  // 0-1.0
  time_range?: MemoryTimeRange;
  user_id?: string;
  include_shared?: boolean;
  filters?: any;
  sort?: any;
}

export interface ConversationThread {
  id: string;
  user_id: string;
  messages: Message[];
}

export type UUID = string;
export type UUID4 = string;
export type UUID5 = string;

export interface MemoryEntry {
  content: string;
  metadata: Record<string, any>;
  agent_id: UUID5;
  user_id?: string | UUID;
  context_type: string;
  embedding_model?: string;
  classification: MemoryClassification;
  source_type: string;
  timestamp: string;
  is_first_interaction?: boolean;
}

export interface MemoryResponse {
  id: string;
  content: string;
  timestamp: string;
  agent_id: string;
  user_id: string;
  context_type: string;
  source_type: string;
  relevance_score: number;
  metadata: {
    sentiment?: 'positive' | 'negative' | 'neutral';
    memory_type?: 'fact' | 'experience' | 'preference' | 'skill';
    confidence_score?: number;
    priority_level?: 'high' | 'medium' | 'low';
  };
  classification?: {
    category?: string;
    tags?: string[];
    importance_score?: number;
  };
  categories?: string[];
  importance_score?: number;
  privacy_level?: 'public' | 'private' | 'shared';
  retention_period?: number;
  is_shared?: boolean;
  image_url?: string;
  delegated_results?: MemoryResponse[];
}

export interface MemorySearchMetadata {
  minImportance?: number;
  categories?: string[];
  include_shared?: boolean;
  context_type?: string;
  min_relevance_score?: number;
  source_type?: string;
  user_preferences?: UserPreferences;
  conversation_id?: string;
  image_config?: {
    adapter?: string;
    model?: string;
    available_parameters?: {
      negativePrompt?: string;
      aspectRatio?: string;
      seed?: string;
      style_preset?: string;
      strength?: string;
      guidance_scale?: string;
      width?: string;
      height?: string;
      reference_image?: string;
    };
  };
}

// export interface MemoryAnalysisRequest {
//   query: string;
//   user_id: string;
//   agent_id?: string;
//   limit?: number;
//   conversation_history?: ConversationMessage[];
//   metadata?: Record<string, any>;
// }

export interface ConversationMessage {
  id: string;
  conversation_id: string;
  content: string;
  sender: string;
  sender_type: string;
  metadata: Record<string, any>;
  timestamp: string;
}

export interface MemoryAnalysisRequest {
  content?: string;
  query?: string;
  user_id: string;
  agent_id: string;
  context?: any[];
  limit?: number;
  metadata?: MemorySearchMetadata | MemoryMetadata;
  conversation_history?: Array<{ role: string, content: string }>;
}

export interface ContentAnalysisResponse {
  success: boolean;
  message: string;
  error?: string | null;
  stored: boolean;
  search_results: any[];
  // agent_delegation?: Array<{
  //   type: string;
  //   result?: {
  //     status: string;
  //     url?: string;
  //     metadata?: any;
  //   };
  // }>;
  agent_delegation?: any;
  delegation_results?: any;
  analysis: {
    stored: boolean;
    search_results: any[];
    agent_delegation?: any;
    analysis: any;
    metadata: any;
  };
  data?: any;
  metadata: any;
}

export interface MemoryType extends Omit<MemoryResponse, 'timestamp'> {
  timestamp: Date;
  importance?: number;
  tags?: string[];
}

export interface MemoryStats {
  total_memories: number;
  memories_by_category: Record<string, number>;
  memories_by_importance: Record<number, number>;
  memories_by_source: Record<string, number>;
  average_importance: number;
  expiring_soon: number;
  recently_added: number;
}

export interface MemoryConsolidation {
  source_memories: string[];
  consolidated_content: string;
  consolidated_classification: MemoryClassification;
}

export interface QdrantThreadPayload extends Record<string, unknown> {
  id: string;
  user_id: string;
  messages: Message[];
}

export interface BatchMemoryEntry {
  memories: MemoryEntry[];
  process_async: boolean;
}


export interface Brain {
  close: () => Promise<void>;
  getModelInfo: () => { name: string };
  getCurrentModel: () => string;
  initialize: () => Promise<void>;
  process(params: {
    input: string;
    messages: LLMMessage[];
    agentPrompt?: string;
    systemPrompt: string;
    conversationId?: string;
    contextPrompt?: string;
    user_id: string;
  }): Promise<BrainResponse>;
  updateConfig: (config: { model: string; adapter: string; systemPrompt?: string | undefined }) => Promise<void>;
  generateConversationTitle: (messages: any[]) => string;
  systemPrompt?: string | undefined;
}

export interface BrainResponse {
  response: {
    content: string;
    metadata?: {
      type?: string;
      media?: Array<{
        type: string;
        url: string;
        metadata: {
          prompt: string;
          [key: string]: any;
        };
      }>;
      model?: string;
      references?: any[];
      analysis?: any;
    };
  };
  conversationId: string;
  parameters?: {
    capability?: string;
    options?: Record<string, unknown>;
  };
}

export interface SessionUser {
  id?: string;
  name?: string;
  email?: string;
  role?: UserRole;
  preferences?: UserPreferences;
}


// AGENTS

export interface AgentCapability {
  name: string;
  description?: string;
  isEnabled: () => boolean;
  parameters?: {
    [key: string]: {
      type: string;
      description: string;
      required: boolean;
    };
  };
  process: (query: string, options?: any) => Promise<any>;
}

export interface AgentMetadata {
  name: string;
  capabilities: AgentCapability[];
  specializationLevel: number;
  requiresData: boolean;
  estimatedDuration: number;
  reliabilityScore: number;
  interactionContext: string[];
}

export interface AgentCommunication {
  id: string;
  timestamp: string;
  sender: string;
  receiver: string;
  type: 'task_request' | 'task_update' | 'task_complete' | 'error';
  payload?: {
    task_id?: string;
    action: string;
    parameters?: Record<string, unknown>;
    status?: string;
    result?: unknown;
    error?: string;
  };
  priority: 'high' | 'medium' | 'low';
  requires_response: boolean;
}

export interface AbilityCapability {
  name: string;
  description: string;
  parameters?: {
    [key: string]: {
      type: string;
      description: string;
      required: boolean;
    };
  };
}

export interface AbilityMetadata {
  name: string;
  description: string;
  capabilities: AbilityCapability[];
  status: 'available' | 'busy' | 'offline';
}

export interface AgentServerResponse {
  success: boolean;
  error?: string;
  data?: any;
}

export interface MemoryOperationStatus {
  success: boolean;
  operation_type: 'store' | 'search' | 'none';
  details: {
    content_stored?: string;
    importance_score?: number;
    categories?: string[];
    reasoning?: string;
  }
}
export interface ContentAnalysis {
  shouldContinue: boolean;
  delegateTo: {
    ability: {
      name: string;
      parameters: any;
    };
    agent?: {
      name: string;
      id: string;
    };
  };
  response: Message;
}
