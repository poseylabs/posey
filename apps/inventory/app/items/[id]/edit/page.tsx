"use client";

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { getSession } from '@posey.ai/core';

interface Pod {
  id: string;
  title: string;
}

interface Item {
  id: string;
  title: string;
  description?: string;
  quantity: number;
  color?: string;
  size?: string;
  location?: string;
  podId?: string;
}

export default function EditItemPage() {
  const router = useRouter();
  const params = useParams();
  const id = params.id as string;

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [quantity, setQuantity] = useState(1);
  const [color, setColor] = useState('');
  const [size, setSize] = useState('');
  const [location, setLocation] = useState('');
  const [selectedPodId, setSelectedPodId] = useState('');

  const [pods, setPods] = useState<Pod[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const checkAuth = async () => {
      const session = await getSession();
      if (!session?.user) {
        console.error('Unauthorized access, redirecting to login');
        router.push('/login');
        return;
      }

      Promise.all([fetchItem(), fetchPods()]).then(() => {
        setLoading(false);
      }).catch(error => {
        console.error('Error initializing page:', error);
        setError('Failed to load data. Please try again.');
        setLoading(false);
      });
    };

    checkAuth();
  }, [id, router]);

  const fetchItem = async () => {
    try {
      const response = await fetch(`/api/inventory/items/${id}`);
      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Item not found');
        }
        throw new Error('Failed to fetch item');
      }

      const data = await response.json();
      const item = data.data;

      setTitle(item.title || '');
      setDescription(item.description || '');
      setQuantity(item.quantity || 1);
      setColor(item.color || '');
      setSize(item.size || '');
      setLocation(item.location || '');
      setSelectedPodId(item.podId || '');
    } catch (error) {
      console.error('Error fetching item:', error);
      throw error;
    }
  };

  const fetchPods = async () => {
    try {
      const response = await fetch('/api/inventory/pods');
      if (!response.ok) {
        throw new Error('Failed to fetch pods');
      }
      const data = await response.json();
      setPods(data.data || []);
    } catch (error) {
      console.error('Error fetching pods:', error);
      throw error;
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!title.trim()) {
      setError('Title is required');
      return;
    }

    setSubmitting(true);
    setError('');

    try {
      const itemData: Item = {
        id,
        title,
        description,
        quantity,
        color: color || undefined,
        size: size || undefined,
        location: location || undefined,
        podId: selectedPodId || undefined,
      };

      const response = await fetch(`/api/inventory/items/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(itemData),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.message || 'Failed to update item');
      }

      router.push(`/items/${id}`);
    } catch (error) {
      console.error('Error updating item:', error);
      setError(error instanceof Error ? error.message : 'An unknown error occurred');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <div className="container mx-auto py-12 text-center">Loading...</div>;
  }

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="max-w-2xl mx-auto">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <div className="text-sm breadcrumbs">
              <ul>
                <li><Link href="/items">Items</Link></li>
                <li><Link href={`/items/${id}`}>{title}</Link></li>
                <li>Edit</li>
              </ul>
            </div>
            <h1 className="text-2xl font-bold mt-2">Edit Item</h1>
          </div>
          <Link href={`/items/${id}`} className="btn btn-sm btn-outline">
            Cancel
          </Link>
        </div>

        <div className="card bg-base-100 shadow-md">
          <div className="card-body">
            {error && (
              <div className="alert alert-error mb-4">
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleSubmit}>
              <div className="form-control mb-4">
                <label className="label">
                  <span className="label-text">Title</span>
                </label>
                <input
                  type="text"
                  className="input input-bordered"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Item name"
                  required
                />
              </div>

              <div className="form-control mb-4">
                <label className="label">
                  <span className="label-text">Description</span>
                </label>
                <textarea
                  className="textarea textarea-bordered h-24"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Item description (optional)"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div className="form-control">
                  <label className="label">
                    <span className="label-text">Quantity</span>
                  </label>
                  <input
                    type="number"
                    className="input input-bordered"
                    value={quantity}
                    onChange={(e) => setQuantity(parseInt(e.target.value) || 1)}
                    min="1"
                    required
                  />
                </div>

                <div className="form-control">
                  <label className="label">
                    <span className="label-text">Color</span>
                  </label>
                  <input
                    type="text"
                    className="input input-bordered"
                    value={color}
                    onChange={(e) => setColor(e.target.value)}
                    placeholder="Optional"
                  />
                </div>

                <div className="form-control">
                  <label className="label">
                    <span className="label-text">Size</span>
                  </label>
                  <input
                    type="text"
                    className="input input-bordered"
                    value={size}
                    onChange={(e) => setSize(e.target.value)}
                    placeholder="Optional"
                  />
                </div>

                <div className="form-control">
                  <label className="label">
                    <span className="label-text">Location</span>
                  </label>
                  <input
                    type="text"
                    className="input input-bordered"
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                    placeholder="Position within pod (optional)"
                  />
                </div>
              </div>

              <div className="form-control mb-6">
                <label className="label">
                  <span className="label-text">Pod</span>
                </label>
                <select
                  className="select select-bordered"
                  value={selectedPodId}
                  onChange={(e) => setSelectedPodId(e.target.value)}
                >
                  <option value="">None (Unassigned)</option>
                  {pods.map((pod) => (
                    <option key={pod.id} value={pod.id}>
                      {pod.title}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-control mt-6">
                <button
                  type="submit"
                  className={`btn btn-primary ${submitting ? 'loading' : ''}`}
                  disabled={submitting}
                >
                  {submitting ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
} 