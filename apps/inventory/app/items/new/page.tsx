"use client";

import { useState, useEffect, useRef, useCallback } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { getSession } from '@posey.ai/core';
import BarcodeLookup from '../../../components/barcode-lookup';

interface Pod {
  id: string;
  title: string;
}

interface ProductData {
  title: string;
  description: string;
  brand?: string;
  category?: string;
  upc: string;
  source: string;
}

export default function NewItemPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const podId = searchParams.get('podId');

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [quantity, setQuantity] = useState(1);
  const [selectedPodId, setSelectedPodId] = useState(podId || '');
  const [pods, setPods] = useState<Pod[]>([]);
  const [loadingPods, setLoadingPods] = useState<boolean>(true);
  const [errorPods, setErrorPods] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [showBarcodeScanner, setShowBarcodeScanner] = useState(false);

  // State for food-specific fields
  const [isFood, setIsFood] = useState(false);
  const [expirationDate, setExpirationDate] = useState('');
  const [addDate, setAddDate] = useState(''); // Consider defaulting or setting server-side
  const [cost, setCost] = useState<string | number>('');
  const [brand, setBrand] = useState('');
  const [upc, setUpc] = useState('');

  const fetchPods = useCallback(async () => {
    setLoadingPods(true);
    setErrorPods(null);
    try {
      // Get session and auth token
      const session = await getSession();
      const authToken = localStorage.getItem('authToken');

      // Use the same headers pattern as in pods/page.tsx
      const response = await fetch('/api/inventory/pods', {
        headers: {
          'Authorization': authToken ? `Bearer ${authToken}` : '',
          'Content-Type': 'application/json',
          'X-User-Id': session?.user?.id || '',
        },
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error('Failed to fetch pods');
      }

      const data = await response.json();
      console.log('Fetched pods:', data.data);
      setPods(data.data || []);

      if (podId) {
        const matchingPod = data.data?.find((pod: Pod) => pod.id === podId);
        if (!matchingPod) {
          console.warn('No exact match found, trying case-insensitive comparison');
          const insensitiveMatch = data.data?.find(
            (pod: Pod) => pod.id.toLowerCase() === podId.toLowerCase()
          );
          console.warn('Case-insensitive match:', insensitiveMatch);
        }
      }
    } catch (error) {
      console.error('Error fetching pods:', error);
      setErrorPods('Failed to load pods. Please try again.');
    } finally {
      setLoadingPods(false);
    }
  }, [podId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!title.trim()) {
      setError('Title is required');
      return;
    }

    setSubmitting(true);
    setError('');

    try {
      const itemData: { [key: string]: any } = {
        title,
        description,
        quantity,
        podId: selectedPodId || null,
        upc: upc || null,
        metadata: {}
      };

      if (isFood) itemData.metadata.isFood = true;
      if (expirationDate) itemData.metadata.expirationDate = expirationDate;
      if (addDate) itemData.metadata.addDate = addDate;
      if (cost) itemData.metadata.cost = cost;
      if (brand) itemData.metadata.brand = brand;

      const response = await fetch('/api/inventory/items', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(itemData),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.message || 'Failed to create item');
      }

      // Navigate to the new item or back to the pod if we came from there
      if (podId) {
        router.push(`/pods/${podId}`);
      } else {
        router.push('/items');
      }
    } catch (error) {
      console.error('Error creating item:', error);
      setError(error instanceof Error ? error.message : 'An unknown error occurred');
    } finally {
      setSubmitting(false);
    }
  };

  const toggleBarcodeScanner = () => {
    setShowBarcodeScanner(prevShow => !prevShow);

    // Clear any existing errors when toggling
    if (error.includes('camera') || error.includes('barcode')) {
      setError('');
    }
  };

  const handleProductFound = (productData: ProductData) => {
    setTitle(productData.title || '');
    setDescription(
      [
        productData.description || '',
        productData.brand ? `Brand: ${productData.brand}` : '',
        productData.category ? `Category: ${productData.category}` : '',
        `UPC: ${productData.upc}`,
        `Source: ${productData.source}`
      ].filter(Boolean).join('\n\n')
    );
    // Pre-fill brand and UPC if available
    if (productData.brand) {
      setBrand(productData.brand);
    }
    if (productData.upc) {
      setUpc(productData.upc);
    }
    // Instead of directly changing the state, use our toggle function
    if (showBarcodeScanner) {
      toggleBarcodeScanner();
    }
  };

  useEffect(() => {
    fetchPods();
  }, [fetchPods]);

  useEffect(() => {
    console.log('loadingPods', loadingPods);
  }, [loadingPods]);

  useEffect(() => {
    console.log('errorPods', errorPods);
  }, [errorPods]);

  useEffect(() => {
    const checkAuth = async () => {
      const session = await getSession();
      if (!session?.user) {
        console.error('Unauthorized access, redirecting to login');
        router.push('/login');
        return;
      }

      fetchPods();
    };

    checkAuth();
  }, [fetchPods, router]);

  useEffect(() => {
    console.log('podId', podId);
    if (podId) {
      setSelectedPodId(podId);
    }
  }, [podId]);

  useEffect(() => {
    console.log('selectedPodId', selectedPodId);
  }, [selectedPodId])

  if (loadingPods) {
    return <div className="container mx-auto py-12 text-center">Loading...</div>;
  }

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="max-w-2xl mx-auto">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-2xl font-bold">Add New Item</h1>
          <Link href={podId ? `/pods/${podId}` : '/items'} className="btn btn-sm btn-outline">
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

            <div className="mb-6">
              <button
                type="button"
                className="btn btn-secondary w-full"
                onClick={toggleBarcodeScanner}
              >
                {showBarcodeScanner ? 'Hide Barcode Scanner' : 'Scan Product Barcode'}
              </button>
            </div>

            {showBarcodeScanner && (
              <div key={`scanner-container-${Date.now()}`}>
                <BarcodeLookup onProductFound={handleProductFound} />
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

              <div className="form-control mb-4">
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

              {/* Is Food Toggle */}
              <div className="form-control mb-4">
                <label className="label cursor-pointer">
                  <span className="label-text">Is this item food?</span>
                  <input
                    type="checkbox"
                    className="toggle toggle-primary"
                    checked={isFood}
                    onChange={(e) => setIsFood(e.target.checked)}
                  />
                </label>
              </div>

              {/* Conditional Food Fields */}
              {isFood && (
                <div className="p-4 border border-base-300 rounded-md mb-4">
                  <h3 className="text-lg font-semibold mb-2">Food Details</h3>
                  <div className="form-control mb-4">
                    <label className="label">
                      <span className="label-text">Brand</span>
                    </label>
                    <input
                      type="text"
                      className="input input-bordered"
                      value={brand}
                      onChange={(e) => setBrand(e.target.value)}
                      placeholder="Brand name (optional)"
                    />
                  </div>
                  <div className="form-control mb-4">
                    <label className="label">
                      <span className="label-text">UPC</span>
                    </label>
                    <input
                      type="text"
                      className="input input-bordered"
                      value={upc}
                      onChange={(e) => setUpc(e.target.value)}
                      placeholder="UPC Code (optional)"
                    />
                  </div>
                  <div className="form-control mb-4">
                    <label className="label">
                      <span className="label-text">Cost</span>
                    </label>
                    <input
                      type="number"
                      className="input input-bordered"
                      value={cost}
                      onChange={(e) => setCost(e.target.value)}
                      placeholder="Cost (optional)"
                      step="0.01" // Allow cents
                      min="0"
                    />
                  </div>
                  <div className="form-control mb-4">
                    <label className="label">
                      <span className="label-text">Expiration Date</span>
                    </label>
                    <input
                      type="datetime-local"
                      className="input input-bordered"
                      value={expirationDate}
                      onChange={(e) => setExpirationDate(e.target.value)}
                    />
                  </div>
                  <div className="form-control mb-4">
                    <label className="label">
                      <span className="label-text">Date Added</span>
                    </label>
                    <input
                      type="datetime-local"
                      className="input input-bordered"
                      value={addDate}
                      onChange={(e) => setAddDate(e.target.value)}
                    />
                    {/* Consider defaulting this or setting server-side */}
                  </div>
                </div>
              )}

              <div className="form-control mb-6">
                <label className="label">
                  <span className="label-text">Pod Selection</span>
                </label>
                <select
                  className="select select-bordered"
                  value={selectedPodId}
                  onChange={(e) => {
                    console.log('Selected pod ID from dropdown:', e.target.value);
                    setSelectedPodId(e.target.value);
                  }}
                >
                  <option value="">None (Unassigned)</option>
                  {pods.map((pod) => (
                    <option key={pod.id} value={pod.id} data-pod-title={pod.title}>
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
                  {submitting ? 'Creating...' : 'Create Item'}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
} 