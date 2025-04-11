'use client';
import { Inter } from "next/font/google";
import Link from "next/link";
import React from 'react';

import {
  LayoutDashboard as DashboardIcon,
  Box as PodIcon,
  List as ItemsIcon,
  Search as SearchIcon,
  Bolt as SettingsIcon,
  Database as DatabaseIcon,
} from 'lucide-react';

export default function Sidebar() {
  const closeDrawer = () => {
    const drawerCheckbox = document.getElementById('menu-drawer') as HTMLInputElement | null;
    if (drawerCheckbox) {
      drawerCheckbox.checked = false;
    }
  };

  const handleMenuClick = (event: React.MouseEvent<HTMLUListElement>) => {
    if ((event.target as HTMLElement).closest('a')) {
      closeDrawer();
    }
  };

  const iconSize = 23;
  const IconClass = 'mb-2';

  const menuItems = [
    {
      icon: <DashboardIcon size={iconSize} className={IconClass} />,
      label: 'Dashboard',
      href: '/dashboard'
    },
    {
      icon: <PodIcon size={iconSize} className={IconClass} />,
      label: 'Storage Pods',
      href: '/pods'
    },
    {
      icon: <ItemsIcon size={iconSize} className={IconClass} />,
      label: 'Items',
      href: '/items'
    },
    {
      icon: <SearchIcon size={iconSize} className={IconClass} />,
      label: 'Search',
      href: '/search'
    },
    {
      icon: <SettingsIcon size={iconSize} className={IconClass} />,
      label: 'Settings',
      href: '/settings'
    }
  ];

  return (
    <aside className="drawer-side z-50 w-80 h-full">
      <label
        htmlFor="menu-drawer"
        aria-label="close sidebar"
        className="drawer-overlay pointer-events-auto"
      ></label>
      <ul
        className="menu p-4 w-full min-h-full bg-base-200 text-base-content relative"
        onClick={handleMenuClick}
      >
        <li>
          <h2 className="menu-title text-lg font-bold mb-4">Inventory Manager</h2>
        </li>
        {menuItems.map((item) => (
          <li key={item.href} className="mb-2 mt-2">
            <Link href={item.href} className="flex items-left">
              {item.icon}
              <span className="ml-2">{item.label}</span>
            </Link>
          </li>
        ))}
        {/* 
        <li>
          <Link href="/dashboard" className="flex items-left">
            
            <span className="ml-2">Dashboard</span>
          </Link>
        </li>
        <li>
          <Link href="/pods" className="py-3">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8M10 14a2 2 0 100-4 2 2 0 000 4z" />
            </svg>
            Storage Pods
          </Link>
        </li>
        <li>
          <Link href="/items" className="py-3">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
            </svg>
            Items
          </Link>
        </li>
        <li>
          <Link href="/search" className="py-3">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            Search
          </Link>
        </li>
        <div className="divider"></div>
        <li>
          <Link href="/settings" className="py-3">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            Database Settings
          </Link>
        </li> */}
      </ul>
    </aside>
  );
}
