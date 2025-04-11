'use client';
import { Send } from 'lucide-react';
import { useState } from 'react';
import { usePoseyRouter } from '../../hooks/router';
import { useConversation } from '../../hooks/useConversation';

const defaultClass = "input input-bordered text-neutral-content flex items-center gap-2 border-1 w-full";

export function StartChat({
  className = defaultClass,
  placeholder = "Ask me anything...",
  useHashLinks = false
}: {
  className?: string;
  placeholder?: string;
  useHashLinks?: boolean;
}) {
  const { linkTo } = usePoseyRouter({ useHashLinks });
  const [input, setInput] = useState('');
  const { startConversation } = useConversation();

  if (!className) {
    className = defaultClass;
  }

  const handleStartConversation = async (message: string) => {
    if (!message.trim()) return;

    try {
      // Clear input immediately
      setInput('');

      // Start the conversation and get the ID
      const conversation = await startConversation(message);

      if (conversation?.id) {
        console.log('CONVERSATION STARTING!', conversation);

        // Just navigate to the new page - let the page handle fetching the conversation
        linkTo(`/chat/${conversation.id}`);

        // Don't update global state here - let the page component do it
        // This completely avoids the race condition
      } else {
        console.error('Error starting conversation: No conversation ID returned');
      }
    } catch (error) {
      console.error('Error starting conversation:', error);
    }
  }

  const handleKeyUp = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleStartConversation(e.currentTarget.value);
    }
  }

  return (
    <label className={className}>
      <input
        type="text"
        className="grow"
        placeholder={placeholder}
        value={input}
        onChange={(e) => setInput(e.target.value || '')}
        onKeyUp={handleKeyUp}
      />
      <button
        className="btn btn-ghost btn-sm"
        onClick={() => handleStartConversation(input)}
        disabled={!input.trim()}
      >
        <Send className="stroke-accent w-5 h-5" />
      </button>
    </label>
  );
}
