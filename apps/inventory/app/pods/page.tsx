"use client";

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { getSession } from '@posey.ai/core';

interface StoragePod {
  id: string;
  title: string;
  contents?: string;
  description?: string;
  locationId?: string;
  location?: {
    id: string;
    name: string;
  };
  size?: string;
  items: any[];
  childPods: StoragePod[];
}

export default function PodsPage() {
  const router = useRouter();
  const [pods, setPods] = useState<StoragePod[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedParentId, setSelectedParentId] = useState<string | null>(null);
  const [breadcrumbs, setBreadcrumbs] = useState<{ id: string, title: string }[]>([{ id: '', title: 'Root' }]);

  const fetchPods = async (parentId: string | null = null) => {
    setLoading(true);
    try {
      // Validate session first
      const session = await getSession();

      if (!session || !session.user) {
        console.error('No valid session found');
        router.push('/auth/login');
        return;
      }

      const url = parentId
        ? `/api/inventory/pods?parentId=${parentId}`
        : '/api/inventory/pods';

      // Get auth token from session and localStorage
      const authToken = localStorage.getItem('authToken');

      const response = await fetch(url, {
        headers: {
          'Authorization': authToken ? `Bearer ${authToken}` : '',
          'Content-Type': 'application/json',
          'X-User-Id': session.user.id || '',
        },
        credentials: 'include'
      });

      if (response.status === 401) {
        console.error('Unauthorized access, redirecting to login');
        localStorage.removeItem('authToken'); // Clear invalid token
        router.push('/auth/login');
        return;
      }

      const data = await response.json();

      console.log('Got list of pods', data?.data);

      if (data.success) {
        setPods(data.data);
      } else {
        console.error('Error response from API:', data);
        if (data.error === 'Unauthorized') {
          router.push('/auth/login');
        }
      }
    } catch (error) {
      console.error('Error fetching pods:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPods(selectedParentId);
  }, [selectedParentId]);

  const navigateToPod = async (podId: string, podTitle: string) => {
    setSelectedParentId(podId);

    // Update breadcrumbs
    const newBreadcrumbs = [...breadcrumbs];
    const existingIndex = newBreadcrumbs.findIndex(b => b.id === podId);

    if (existingIndex !== -1) {
      // If we're going back in the breadcrumb chain, remove everything after this point
      setBreadcrumbs(newBreadcrumbs.slice(0, existingIndex + 1));
    } else {
      // Add the new pod to the breadcrumb trail
      setBreadcrumbs([...newBreadcrumbs, { id: podId, title: podTitle }]);
    }
  };

  const navigateToRoot = () => {
    setSelectedParentId(null);
    setBreadcrumbs([{ id: '', title: 'Root' }]);
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-[80vh]">
        <span className="loading loading-spinner loading-lg"></span>
      </div>
    );
  }

  return (
    <div className="container mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Storage Pods</h1>
        <Link href="/pods/new" className="btn btn-primary">
          Add New Pod
        </Link>
      </div>

      {/* Breadcrumbs */}
      <div className="text-sm breadcrumbs mb-6">
        <ul>
          {breadcrumbs.map((crumb, index) => (
            <li key={crumb.id || 'root'}>
              <a
                onClick={() => index === 0 ? navigateToRoot() : navigateToPod(crumb.id, crumb.title)}
                className="cursor-pointer hover:underline"
              >
                {crumb.title}
              </a>
            </li>
          ))}
        </ul>
      </div>

      {pods.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {pods.map((pod) => (
            <div key={pod.id} className="card bg-base-100 shadow-md">
              <div className="card-body">
                <h2 className="card-title">{pod.title}</h2>
                {pod.contents && <p>{pod.contents}</p>}

                <div className="grid grid-cols-2 gap-2 mt-2">
                  {pod.location && (
                    <div className="flex items-center gap-1">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                      <span className="text-sm">{pod.location.name}</span>
                    </div>
                  )}

                  {pod.description && (
                    <div className="flex items-center gap-1">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
                      </svg>
                      <span className="text-sm">{pod.description}</span>
                    </div>
                  )}

                  {pod.size && (
                    <div className="flex items-center gap-1">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5v-4m0 4h-4m4 0l-5-5" />
                      </svg>
                      <span className="text-sm">{pod.size}</span>
                    </div>
                  )}
                </div>

                <div className="flex justify-between mt-4">
                  <div className="badge badge-outline">{pod.childPods.length} sub-pods</div>
                  <div className="badge badge-outline">{pod.items.length} items</div>
                </div>

                <div className="card-actions mt-4">
                  <button
                    className="btn btn-primary btn-sm flex-1"
                    onClick={() => navigateToPod(pod.id, pod.title)}
                  >
                    Open
                  </button>

                  <Link href={`/pods/${pod.id}`} className="btn btn-outline btn-sm flex-1">
                    Details
                  </Link>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-10">
          <h3 className="text-xl mb-2">No Storage Pods Found</h3>
          <p className="mb-4">
            {selectedParentId ? "This pod doesn't contain any sub-pods." : "You haven't created any storage pods yet."}
          </p>
          <Link href="/pods/new" className="btn btn-primary">
            Create Your First Pod
          </Link>
        </div>
      )}
    </div>
  );
} 