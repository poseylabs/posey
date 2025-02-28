import { useCallback } from "react";
import { ChatMessage } from "./message";
import { usePoseyState } from '@posey.ai/state';
import { Message } from "@posey.ai/core";

export function MessageList({
  messages = []
}: {
  messages?: Message[]
}) {

  if (messages.length === 0) {
    return <div className="message-list max-h-1">No messages</div>;
  }

  return (
    <div className="message-list max-h-1 w-full flex flex-col">
      {messages.map((message, index) => (
        <ChatMessage
          key={message.id || index}
          message={message}
          isSpeaking={null}
          onPlayPause={() => { }}
        />
      ))}
    </div>
  );
}
