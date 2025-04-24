import { usePoseyRouter } from './router'
import { useAgent } from './useAgent';
import { useConversation } from './useConversation';

// Re-export the type
export type { UseConversationProps } from './useConversation';

const hooks = {
  usePoseyRouter,
  useConversation,
  useAgent
}

export {
  // All hooks
  hooks,
  // Individual Hooks
  usePoseyRouter,
  useConversation,
  useAgent
}
