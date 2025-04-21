import { usePoseyState } from '@posey.ai/state';
import { useEffect, useState } from "react";
import { usePoseyRouter } from '../../hooks/router';

const FALLBACK_IMG = 'https://img.daisyui.com/images/stock/photo-1534528741775-53994a69daeb.webp'

export default function UserButton({
  useHashLinks = false
}: {
  useHashLinks?: boolean;
}) {
  const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || 'http://localhost:8888'

  // Subscribe to the full user object to ensure updates
  const user = usePoseyState((state) => state.user);
  const logout = usePoseyState((state) => state.logout);

  // Remove local state management since we're using store directly
  const { linkTo } = usePoseyRouter({ useHashLinks });

  const handleLogout = () => {
    logout()
  }

  const liClass = "p-2 m-0";
  const buttonClass = "btn btn-ghost btn-sm";
  const dividerClass = "divider divider-secondary px-6 m-0 mt-1 mb-2";

  const buttonLink = (href: string) => {
    linkTo(href)
  }

  return (
    <>
      <div className="dropdown dropdown-end">
        <div tabIndex={0} role="button" className="btn btn-ghost btn-circle avatar">
          <div className="w-10 rounded-full">
            <img
              alt="User avatar"
              src={user?.metadata?.profile?.avatar || FALLBACK_IMG}
            />
          </div>
        </div>

        <ul
          tabIndex={0}
          className="dropdown-content bg-base-100 rounded-box z-[1] mt-3 w-52 p-2 shadow"
        >

          <li>
            <div className={dividerClass}>Bookmarks</div>
            <ul>
              <li className={liClass}>
                <button className={buttonClass} onClick={() => buttonLink('/favorites/messages')}>
                  Messages
                  {/* <a href="/favorites/messages">Messages</a> */}
                </button>
              </li>
              <li className={liClass}>
                <button className={buttonClass} onClick={() => buttonLink('/favorites/images')}>
                  Images
                </button>
              </li>
              {/* <li className={liClass}><a href="/favorites/videos">Saved Videos</a></li> */}
              {/* <li className={liClass}><a href="/favorites/songs">Saved Songs</a></li> */}
            </ul>

          </li>

          <li>
            <div className={dividerClass}>Settings</div>
            <ul>
              {user?.role === 'admin' && (
                <li className={liClass}>
                  <button className={buttonClass} onClick={() => buttonLink('/admin')}>Admin</button>
                </li>
              )}
              {user?.id && (
                <li className={liClass}>
                  <button className={buttonClass} onClick={handleLogout}>Logout</button>
                </li>
              )}
              {!user?.id && (
                <li className={liClass}>
                  <button className={buttonClass} onClick={() => buttonLink(`${baseUrl}/auth/login`)}>Login</button>
                </li>
              )}
            </ul>
          </li>

        </ul>
      </div>
    </>
  );
}
