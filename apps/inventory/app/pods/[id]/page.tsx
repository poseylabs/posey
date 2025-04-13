"use client";

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { getSession } from '@posey.ai/core';
import { use } from 'react';

interface Item {
  id: string;
  title: string;
  description?: string;
  quantity: number;
}

interface StoragePod {
  id: string;
  title: string;
  contents?: string;
  description?: string;
  locationId?: string;
  location?: {
    id: string;
    name: string;
    address?: string;
    city?: string;
    state?: string;
  };
  items: Item[];
  childPods: StoragePod[];
  parentId?: string;
  parent?: StoragePod;
}

export default function PodDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const unwrappedParams = use(params);
  const podId = unwrappedParams.id;

  const router = useRouter();
  const [pod, setPod] = useState<StoragePod | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    const fetchPodDetails = async () => {
      setLoading(true);
      try {
        // Validate session first
        const session = await getSession();

        if (!session || !session.user) {
          console.error('No valid session found');
          router.push('/auth/login');
          return;
        }

        // Get auth token from localStorage
        const authToken = localStorage.getItem('authToken');

        const response = await fetch(`/api/inventory/pods/${podId}`, {
          headers: {
            'Authorization': authToken ? `Bearer ${authToken}` : '',
            'Content-Type': 'application/json',
            'X-User-Id': session.user.id || '',
          },
          credentials: 'include'
        });

        if (response.status === 401) {
          localStorage.removeItem('authToken'); // Clear invalid token
          router.push('/auth/login');
          return;
        }

        if (response.status === 404) {
          setError('Pod not found');
          setLoading(false);
          return;
        }

        const data = await response.json();

        if (data.success) {
          setPod(data.data);
        } else {
          setError(data.error || 'Failed to fetch pod details');
        }
      } catch (error) {
        console.error('Error fetching pod details:', error);
        setError('An unexpected error occurred');
      } finally {
        setLoading(false);
      }
    };

    fetchPodDetails();
  }, [podId, router]);

  const handleDelete = async () => {
    if (!deleteConfirm) {
      setDeleteConfirm(true);
      return;
    }

    setDeleting(true);
    try {
      const session = await getSession();
      const authToken = localStorage.getItem('authToken');

      const response = await fetch(`/api/inventory/pods/${podId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': authToken ? `Bearer ${authToken}` : '',
          'Content-Type': 'application/json',
          'X-User-Id': session?.user?.id || '',
        },
        credentials: 'include'
      });

      const data = await response.json();

      if (data.success) {
        router.push('/pods');
      } else {
        setError(data.error || 'Failed to delete pod');
        setDeleteConfirm(false);
      }
    } catch (error) {
      console.error('Error deleting pod:', error);
      setError('An unexpected error occurred');
      setDeleteConfirm(false);
    } finally {
      setDeleting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-[80vh]">
        <span className="loading loading-spinner loading-lg"></span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto max-w-4xl py-8">
        <div className="alert alert-error">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>{error}</span>
        </div>
        <div className="flex justify-center mt-6">
          <Link href="/pods" className="btn btn-primary">
            Back to Pods
          </Link>
        </div>
      </div>
    );
  }

  if (!pod) {
    return (
      <div className="container mx-auto max-w-4xl py-8">
        <div className="alert alert-warning">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <span>Pod not found</span>
        </div>
        <div className="flex justify-center mt-6">
          <Link href="/pods" className="btn btn-primary">
            Back to Pods
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto max-w-4xl py-8">
      <div className="flex items-center mb-6">
        <Link href="/pods" className="btn btn-ghost btn-sm mr-4">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Back to Pods
        </Link>
        {pod.parentId && (
          <Link href={`/pods/${pod.parentId}`} className="btn btn-ghost btn-sm mr-4">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
            </svg>
            Parent Pod
          </Link>
        )}
      </div>

      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">{pod.title}</h1>
        <div className="flex gap-2">
          <Link href={`/pods/${pod.id}/edit`} className="btn btn-outline">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
            Edit
          </Link>
          <button
            className={`btn ${deleteConfirm ? 'btn-error' : 'btn-outline'} ${deleting ? 'loading' : ''}`}
            onClick={handleDelete}
            disabled={deleting || pod.items.length > 0 || pod.childPods.length > 0}
          >
            {!deleting && (
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            )}
            {deleteConfirm ? 'Confirm Delete' : 'Delete'}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="card bg-base-100 shadow-md">
          <div className="card-body">
            <h2 className="card-title">Details</h2>
            <div className="space-y-3 mt-2">
              {pod.contents && (
                <div>
                  <span className="font-semibold block">Contents:</span>
                  <p>{pod.contents}</p>
                </div>
              )}

              {pod.description && (
                <div>
                  <span className="font-semibold block">Description:</span>
                  <p>{pod.description}</p>
                </div>
              )}

              {pod.location && (
                <div>
                  <span className="font-semibold block">Location:</span>
                  <p>{pod.location.name}</p>
                  {pod.location.address && (
                    <p className="text-sm text-gray-500">
                      {pod.location.address}
                      {pod.location.city && pod.location.state && `, ${pod.location.city}, ${pod.location.state}`}
                    </p>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="card bg-base-100 shadow-md">
          <div className="card-body">
            <div className="flex justify-between items-center">
              <h2 className="card-title">Items ({pod.items.length})</h2>
              <Link href={`/items/new?podId=${pod.id}`} className="btn btn-sm btn-outline">
                Add Item
              </Link>
            </div>

            {pod.items.length > 0 ? (
              <ul className="mt-3 space-y-2">
                {pod.items.map(item => (
                  <li key={item.id} className="border-b pb-2">
                    <Link href={`/items/${item.id}`} className="hover:underline">
                      <div className="flex justify-between">
                        <span>{item.title}</span>
                        <span className="badge">{item.quantity}</span>
                      </div>
                      {item.description && (
                        <p className="text-sm text-gray-500 truncate">{item.description}</p>
                      )}
                    </Link>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="text-center py-4 text-gray-500">
                <p>No items in this pod</p>
              </div>
            )}

            {pod.items.length > 5 && (
              <div className="card-actions justify-end mt-2">
                <Link href={`/items?podId=${pod.id}`} className="btn btn-sm btn-ghost">
                  View All Items
                </Link>
              </div>
            )}
          </div>
        </div>

        <div className="card bg-base-100 shadow-md">
          <div className="card-body">
            <div className="flex justify-between items-center">
              <h2 className="card-title">Sub-Pods ({pod.childPods.length})</h2>
              <Link href={`/pods/new?parentId=${pod.id}`} className="btn btn-sm btn-outline">
                Add Sub-Pod
              </Link>
            </div>

            {pod.childPods.length > 0 ? (
              <ul className="mt-3 space-y-2">
                {pod.childPods.map(childPod => (
                  <li key={childPod.id} className="border-b pb-2">
                    <Link href={`/pods/${childPod.id}`} className="hover:underline">
                      <div className="flex justify-between">
                        <span>{childPod.title}</span>
                        <div className="flex space-x-2">
                          <span className="badge">{childPod.childPods.length} pods</span>
                          <span className="badge">{childPod.items.length} items</span>
                        </div>
                      </div>
                      {childPod.description && (
                        <p className="text-sm text-gray-500 truncate">{childPod.description}</p>
                      )}
                    </Link>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="text-center py-4 text-gray-500">
                <p>No sub-pods</p>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="card bg-base-100 shadow-md mb-6">
        <div className="card-body">
          <h2 className="card-title">QR Code</h2>
          <div className="flex flex-col items-center justify-center p-4">
            <div className="bg-white p-4 rounded-md">
              <img
                src={`https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(window.location.href)}`}
                alt="Pod QR Code"
                className="w-40 h-40"
              />
            </div>
            <p className="text-sm mt-2">Scan to view this pod</p>
            <Link href={`/pods/${pod.id}/label`} className="btn btn-sm btn-outline mt-4">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
              </svg>
              Print Label
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
} 