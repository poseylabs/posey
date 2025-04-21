import React from 'react';

// Define a default link component (simple anchor tag)
const DefaultLink = (props: React.AnchorHTMLAttributes<HTMLAnchorElement>) => <a {...props} />;

interface AdminNavLink {
  label: string;
  href: string;
  isActive?: boolean; // Optional: for highlighting the active link
}

interface AdminNavbarProps {
  links: AdminNavLink[];
  LinkComponent?: React.ElementType;
}

export function AdminNavbar({
  links = [],
  LinkComponent = DefaultLink,
}: AdminNavbarProps) {
  return (
    <div className="navbar bg-base-300 min-h-fit py-1 shadow-md">
      <div className="navbar-center">
        <ul className="menu menu-horizontal px-1">
          {links.map((link) => (
            <li key={link.href}>
              <LinkComponent
                href={link.href}
                className={link.isActive ? 'active' : ''} // DaisyUI uses 'active' class for menu items
              >
                {link.label}
              </LinkComponent>
            </li>
          ))}
        </ul>
      </div>
      {/* Optional: Add navbar-start or navbar-end sections if needed later */}
    </div>
  );
} 