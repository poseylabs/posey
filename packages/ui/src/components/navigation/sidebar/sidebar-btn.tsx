import { PanelRightClose, PanelRightOpen } from 'lucide-react';
import { usePoseyState } from '@posey.ai/state';
import { PoseyState } from '@posey.ai/core';

export default function SidebarButton() {

  const store = usePoseyState();
  const { status, toggleSidebar } = store.select((state: PoseyState) => ({
    status: state.status,
    toggleSidebar: state.toggleSidebar
  }));

  return (
    <button
      // htmlFor="posey-drawer"
      aria-label="open sidebar"
      className="btn btn-square btn-ghost"
      onClick={toggleSidebar}
    >
      {status.isSidebarOpen ? <PanelRightOpen /> : <PanelRightClose />}
    </button>
  );
}
