import { ListTodoIcon } from 'lucide-react';
import { SidebarCloseIcon, SidebarOpenIcon } from '../sidebar/sidebar-btn';

import { StartChat } from '../../chat/start';
import SidebarButton from '../sidebar/sidebar-btn';
import UserButton from '../../user/user-button';
import { usePoseyState } from '@posey.ai/state';

interface NavbarProps {
  withStartChat?: boolean;
  useHashLinks?: boolean;
  content?: React.ReactNode | boolean | null | 'default';
  LinkComponent?: React.ElementType;
  logo?: string | React.ReactNode;
  iconOpen?: React.ReactNode;
  iconClose?: React.ReactNode;
}

// Define a default link component (simple anchor tag)
const DefaultLink = (props: React.AnchorHTMLAttributes<HTMLAnchorElement>) => <a {...props} />;

export function Navbar({
  withStartChat = true,
  useHashLinks = false,
  content = 'default',
  logo = 'Posey',
  LinkComponent = DefaultLink, // Use the functional component as default
  iconOpen = <SidebarOpenIcon />,
  iconClose = <SidebarCloseIcon />,
}: NavbarProps) {
  // Force re-render on user changes
  const user = usePoseyState((state) => state.user);

  return (
    <div className="navbar bg-base-200 pt-4 pb-4">

      {/* Left side */}
      <div className="flex-1">
        <SidebarButton iconOpen={iconOpen} iconClose={iconClose} />
        <a href="/">
          <span className="text-lg font-bold">{logo}</span>
        </a>
      </div>

      {/* Right side */}
      <div className="flex-none gap-2">
        {withStartChat && (
          <StartChat useHashLinks={useHashLinks} />
        )}
      </div>
      {content === 'default' && (
        <div className="flex-none">
          <LinkComponent href="/tasks" className="btn btn-ghost btn-sm">
            <ListTodoIcon className="w-4 h-4" />
            <span className="hidden md:inline">Tasks</span>
          </LinkComponent>
          <UserButton key={user?.metadata?.profile?.avatar} useHashLinks={useHashLinks} />
        </div>
      )}
      {content !== 'default' && content}
    </div>
  );
}
