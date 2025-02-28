import type { Message } from '@posey.ai/core';

export interface ChatFormData {
  message: string;
  files?: File[];
}

export interface ChatSession {
  user: any;
}

export interface ChatInterfaceProps {
  session: ChatSession;
}

export interface ChatInputProps {
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => void;
  onKeyDown?: (e: React.KeyboardEvent<HTMLTextAreaElement>) => void;
  onSendMessage: (message: { message: string; timestamp: Date }) => void;
  disabled?: boolean;
  placeholder?: string;
  ref?: React.RefObject<HTMLTextAreaElement | null>;
  hasActiveTasks?: boolean;
}

export interface MessageListProps {
  messages: Message[];
}

export interface ChatMessageImageProps {
  src: string;
  alt: string;
}

export interface ChatMessageProps {
  message: Message & {
    content: string | { content: string } | Record<string, any>;
  };
  isPlaying?: boolean;
  onPlay?: () => void;
  onPause?: () => void;
  onExpand?: () => void;
  onDownload?: () => void;
}

export interface ChatMessagesProps {
  messages: Message[];
  isPlaying?: string | null;
  isMuted?: boolean;
  onPlay?: (messageId: string, content: string) => void;
}

export interface ChatMessageContentProps {
  message: Message;
  isPlaying?: string | null;
  isMuted?: boolean;
  onPlay?: (messageId: string, content: string) => void;
}

export interface ChatToolbarProps {
  showSidebar: boolean
  onToggleSidebar: () => void
}
