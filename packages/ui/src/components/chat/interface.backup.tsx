'use client';
import { useCallback, useEffect, useRef, useState } from 'react';
import { usePoseyState } from '@posey.ai/state';
import { Conversation, ConversationStatus } from '@posey.ai/core';

import { Navbar } from '../navigation/navbar/navbar';
import { ChatInput } from './input';
import { MessageList } from './messages/message-list';
import { ChatFormData } from '../../types';
import { DrawerContent } from '../layout/drawer-content';
import { ChatStatus } from './chat-status';
import { useAgent } from '../../hooks';
import { useConversation } from '../../hooks/useConversation';

import './interface.css';

export function ChatInterface({
  conversation
}: {
  conversation: Conversation
}) {
  // State
  const [input, setInput] = useState('');
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [status, setStatus] = useState<string>('idle');
  const [statusMessage, setStatusMessage] = useState<string>('');

  // Get the entire chat object instead of just currentConversation
  const chat = usePoseyState((state) => state.chat);
  const currentConversation = chat.currentConversation;

  // Log the current conversation
  console.log('Current conversation in ChatInterface:', {
    from_state: currentConversation,
    from_props: conversation
  });


  // Set title and ID based on current conversation
  const conversationId = currentConversation?.id || '';
  const conversationTitle = currentConversation?.title || 'New Conversation';

  // Refs
  const titleInputRef = useRef<HTMLInputElement>(null);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  const handleTitleClick = useCallback(() => {
    setIsEditingTitle(true);
    setTimeout(() => {
      titleInputRef.current?.focus();
      titleInputRef.current?.select();
    }, 0);
  }, []);

  const updateConversation = useCallback(async (id: string, updates: Partial<Conversation>) => {
    // TODO: update conversation
  }, []);

  const handleTitleUpdate = useCallback(async (title: string) => {
    if (!conversationId) return;

    try {
      await updateConversation(conversationId, { title });
      setIsEditingTitle(false);
    } catch (error) {
      console.error('Error updating conversation:', error);
    }
  }, [conversationId, conversationTitle, updateConversation]);

  // const handleTitleKeyDown = useCallback((e: React.KeyboardEvent<HTMLInputElement>) => {
  //   if (e.key === 'Enter') {
  //     handleTitleUpdate(e.target);
  //   } else if (e.key === 'Escape') {
  //     setIsEditingTitle(false);
  //   }
  // }, [handleTitleUpdate]);

  const handleSubmit = async (data: ChatFormData) => {
    try {
      setStatus('loading');
      setStatusMessage('Sending message to agent...');

      // await callAgent(data.message);

      setInput('');
      setStatus('idle');
      setStatusMessage('');
    } catch (error) {
      console.error('Error sending message:', error);
      setStatus('error');
      setStatusMessage('Failed to send message. Please try again.');
    }
  };

  // Handle new conversations
  useEffect(() => {
    const handleNewConversation = async () => {
      if (
        currentConversation?.status === ConversationStatus.NEW &&
        currentConversation?.messages?.length &&
        currentConversation.messages.length > 0
      ) {
        console.log('new conversation', currentConversation);
        // try {
        //   setStatus('loading');
        //   setStatusMessage('Processing your message...');

        //   // Get the first message (user's initial prompt)
        //   const firstMessage = currentConversation.messages?.[0];

        //   // Call agent with the initial message
        // await callAgent(firstMessage?.content || '');

        //   setStatus('idle');
        //   setStatusMessage('');
        // } catch (error) {
        //   console.error('Error processing new conversation:', error);
        //   setStatus('error');
        //   setStatusMessage('Failed to process message. Please try again.');
        // }
      }
    };

    handleNewConversation();
  }, [currentConversation?.id, currentConversation?.status]);

  const setConversationTitle = (title: string) => {
    handleTitleUpdate(title);
  }

  return (
    <DrawerContent>
      <div className="chat-header">
        <Navbar />
        <div className="px-4 flex items-center">
          title...
          {/* {isEditingTitle ? (
            <input
              ref={titleInputRef}
              type="text"
              className="text-2xl font-bold bg-transparent border-b border-gray-300 focus:border-primary focus:outline-none w-full"
              value={conversationTitle}
              onChange={(e) => setConversationTitle(e.target.value)}
              // onBlur={handleTitleUpdate}
              onKeyDown={handleTitleKeyDown}
            />
          ) : (
            <h1 
              className="text-2xl font-bold cursor-pointer hover:text-primary transition-colors"
              onClick={handleTitleClick}
              title="Click to edit title"
            >
              {conversationTitle}
            </h1>
          )} */}
        </div>
      </div>

      <div
        ref={scrollAreaRef}
        className="chat-content-main pl-4 overflow-y-auto min-h-0 max-h-full"
      >
        <MessageList />
      </div>
      <div className="chat-footer text-center p-4">
        {status !== 'idle' && statusMessage && <ChatStatus
          status={status}
          message={statusMessage}
        />}
        <ChatInput
          onSubmit={handleSubmit}
          value={input}
        />
      </div>
    </DrawerContent>
  );
}
