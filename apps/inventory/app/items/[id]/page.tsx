"use client";

import { useState, useEffect, useCallback } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { getSession } from '@posey.ai/core';

interface Item {
  id: string;
  title: string;
  description?: string;
  quantity: number;
  color?: string;
  size?: string;
  location?: string;
  createdAt: string;
  updatedAt: string;
  podId?: string;
  pod?: {
    id: string;
    title: string;
  };
}

export default function ItemDetailPage() {
  const router = useRouter();
  const params = useParams();
  const id = params.id as string;

  const [item, setItem] = useState<Item | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);

  const fetchItem = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    try {
      const response = await fetch(`/api/inventory/items/${id}`);
      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Item not found');
        }
        throw new Error('Failed to fetch item');
      }

      const data = await response.json();
      setItem(data.data);
    } catch (error) {
      console.error('Error fetching item:', error);
      setError(error instanceof Error ? error.message : 'An unknown error occurred');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    const checkAuth = async () => {
      const session = await getSession();
      if (!session?.user) {
        console.error('Unauthorized access, redirecting to login');
        router.push('/login');
        return;
      }
    };

    checkAuth();
  }, [router]);

  useEffect(() => {
    if (id) {
      fetchItem();
    }
  }, [id, fetchItem]);

  const handleDelete = async () => {
    if (!id) return;
    try {
      const response = await fetch(`/api/inventory/items/${id}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Failed to delete item');
      }

      // Redirect to items list or pod detail if this item was in a pod
      if (item?.podId) {
        router.push(`/pods/${item.podId}`);
      } else {
        router.push('/items');
      }
    } catch (error) {
      console.error('Error deleting item:', error);
      setError(error instanceof Error ? error.message : 'An unknown error occurred');
      setShowDeleteModal(false);
    }
  };

  if (loading) {
    return <div className="container mx-auto py-12 text-center">Loading item details...</div>;
  }

  if (error) {
    return (
      <div className="container mx-auto py-12 text-center">
        <div className="alert alert-error max-w-md mx-auto">
          <span>{error}</span>
        </div>
        <div className="mt-4">
          <Link href="/items" className="btn btn-outline">
            Back to Items
          </Link>
        </div>
      </div>
    );
  }

  if (!item) {
    return (
      <div className="container mx-auto py-12 text-center">
        <h2 className="text-xl mb-4">Item not found</h2>
        <Link href="/items" className="btn btn-outline">
          Back to Items
        </Link>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="max-w-2xl mx-auto">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <div className="text-sm breadcrumbs">
              <ul>
                <li><Link href="/items">Items</Link></li>
                <li>{item.title}</li>
              </ul>
            </div>
            <h1 className="text-2xl font-bold mt-2">{item.title}</h1>
          </div>
          <div className="flex gap-2">
            <Link href={`/items/${id}/edit`} className="btn btn-sm btn-outline">
              Edit
            </Link>
            <button
              onClick={() => setShowDeleteModal(true)}
              className="btn btn-sm btn-error btn-outline"
            >
              Delete
            </button>
          </div>
        </div>

        <div className="card bg-base-100 shadow-md">
          <div className="card-body">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="font-semibold mb-2">Details</h3>
                {item.description && (
                  <p className="mb-4">{item.description}</p>
                )}

                <div className="stat-group grid grid-cols-2 gap-2">
                  <div className="stat bg-base-200 rounded-lg p-3">
                    <div className="stat-title text-xs">Quantity</div>
                    <div className="stat-value text-xl">{item.quantity}</div>
                  </div>

                  {item.size && (
                    <div className="stat bg-base-200 rounded-lg p-3">
                      <div className="stat-title text-xs">Size</div>
                      <div className="stat-value text-xl">{item.size}</div>
                    </div>
                  )}

                  {item.color && (
                    <div className="stat bg-base-200 rounded-lg p-3">
                      <div className="stat-title text-xs">Color</div>
                      <div className="stat-value text-xl">{item.color}</div>
                    </div>
                  )}
                </div>
              </div>

              <div>
                <h3 className="font-semibold mb-2">Location</h3>
                {item.pod ? (
                  <div className="bg-base-200 p-4 rounded-lg">
                    <p className="font-medium">
                      Stored in <Link href={`/pods/${item.pod.id}`} className="link">{item.pod.title}</Link>
                    </p>
                    {item.location && <p className="text-sm mt-1">{item.location}</p>}
                  </div>
                ) : (
                  <div className="bg-base-200 p-4 rounded-lg">
                    <p>Not assigned to any pod</p>
                    {item.location && <p className="text-sm mt-1">{item.location}</p>}
                  </div>
                )}

                <div className="mt-4">
                  <h3 className="font-semibold mb-2">Date Information</h3>
                  <div className="text-sm">
                    <p>Created: {new Date(item.createdAt).toLocaleString()}</p>
                    <p>Last updated: {new Date(item.updatedAt).toLocaleString()}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
        <div className="modal modal-open">
          <div className="modal-box">
            <h3 className="font-bold text-lg">Confirm Deletion</h3>
            <p className="py-4">
              Are you sure you want to delete <span className="font-bold">{item.title}</span>?
              This action cannot be undone.
            </p>
            <div className="modal-action">
              <button onClick={() => setShowDeleteModal(false)} className="btn btn-outline">
                Cancel
              </button>
              <button onClick={handleDelete} className="btn btn-error">
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
} 