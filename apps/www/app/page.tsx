'use client';
import { DrawerContent, Navbar } from '@posey.ai/ui';
import { AuthProvider } from '@/app/providers/auth';
import ChatHero from '@/app/components/chat-hero';

export default function Chat() {
  return (
    <AuthProvider authRequired={true}>
      <DrawerContent>
        <Navbar withStartChat={false} />
        <ChatHero />
      </DrawerContent>
    </AuthProvider>
  );
}
