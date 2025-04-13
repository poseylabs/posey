'use client';
import { StartChat } from '@posey.ai/ui';

export default function Chat() {
  return (
    <section className="grid bg-slate-400">
      <div className="w-full p-4">
        <StartChat
          placeholder="Hello, I'm Posey, how can I help you today?"
          useHashLinks={false}
        />
      </div>
    </section>
  );
}
