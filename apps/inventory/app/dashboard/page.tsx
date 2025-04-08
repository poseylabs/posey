"use client";
import React from "react";
import { usePoseyState } from '@posey.ai/state';
import { useRouter } from 'next/navigation';

export default function DashboardPage() {
  const router = useRouter();

  // Use separate selectors for individual state fields to prevent infinite loops
  const user = usePoseyState(state => state.user);
  const logout = usePoseyState(state => state.logout);

  // Memoize complex values derived from state
  const welcomeMessage = React.useMemo(() =>
    `Welcome, ${user?.email || 'User'}`,
    [user?.email]
  );

  const handleLogout = async () => {
    try {
      await logout();
      localStorage.removeItem('authToken');
      router.push('/auth/login');
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  // Dashboard is protected by AuthProvider in the layout
  // No need for additional checks here

  return (
    <div className="p-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-white">Dashboard</h1>
          <p className="text-gray-400 mt-1">{welcomeMessage}</p>
        </div>
        <button
          onClick={handleLogout}
          className="mt-4 md:mt-0 btn btn-outline btn-error"
        >
          Logout
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="card bg-base-200 shadow-xl">
          <div className="card-body">
            <h2 className="card-title">Storage Pods</h2>
            <p>Manage your storage containers</p>
            <div className="card-actions justify-end">
              <button className="btn btn-primary" onClick={() => router.push('/pods')}>View Pods</button>
            </div>
          </div>
        </div>

        <div className="card bg-base-200 shadow-xl">
          <div className="card-body">
            <h2 className="card-title">Items</h2>
            <p>View and manage inventory items</p>
            <div className="card-actions justify-end">
              <button className="btn btn-primary" onClick={() => router.push('/items')}>View Items</button>
            </div>
          </div>
        </div>

        <div className="card bg-base-200 shadow-xl">
          <div className="card-body">
            <h2 className="card-title">Search</h2>
            <p>Find items across all storage pods</p>
            <div className="card-actions justify-end">
              <button className="btn btn-primary" onClick={() => router.push('/search')}>Search</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 