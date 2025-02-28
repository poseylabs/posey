import Link from 'next/link';
import { ListTodoIcon } from 'lucide-react';

import { StartChat } from '../../chat/start';
import SidebarButton from '../sidebar/sidebar-btn';
import UserButton from '../../user/user-button';
import { usePoseyState } from '@posey.ai/state';

export function Navbar({
  withStartChat = true,
  useHashLinks = false
}: {
  withStartChat?: boolean,
  useHashLinks?: boolean
}) {
  // Force re-render on user changes
  const user = usePoseyState((state) => state.user);

  return (
    <div className="navbar bg-base-200 pt-4 pb-4">

      {/* Left side */}
      <div className="flex-1">
        <SidebarButton />
        <a href="/">
          <span className="text-lg font-bold">Posey</span>
        </a>
      </div>

      {/* Right side */}
      <div className="flex-none gap-2">
        {withStartChat && (
          <StartChat useHashLinks={useHashLinks} />
        )}
      </div>
      <div className="flex-none">
        <Link href="/tasks" className="btn btn-ghost btn-sm">
          <ListTodoIcon className="w-4 h-4" />
          <span className="hidden md:inline">Tasks</span>
        </Link>
        <UserButton key={user?.metadata?.profile?.avatar} useHashLinks={useHashLinks} />
      </div>
    </div>
  );
}
