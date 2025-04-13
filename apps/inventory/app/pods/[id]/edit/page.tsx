"use client";

import { useState, useEffect, FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { getSession } from '@posey.ai/core';
import { use } from 'react';

interface StoragePod {
  id: string;
  title: string;
  contents?: string;
  description?: string;
  locationId?: string;
}

interface Location {
  id: string;
  name: string;
}

export default function EditPodPage({ params }: { params: Promise<{ id: string }> }) {
  const unwrappedParams = use(params);
  const podId = unwrappedParams.id;

  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [locations, setLocations] = useState<Location[]>([]);

  const [formData, setFormData] = useState<StoragePod>({
    id: podId,
    title: '',
    contents: '',
    description: '',
    locationId: '',
  });

  useEffect(() => {
    const fetchData = async () => {
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
        const headers = {
          'Authorization': authToken ? `Bearer ${authToken}` : '',
          'Content-Type': 'application/json',
          'X-User-Id': session.user.id || '',
        };
        const fetchOptions = {
          headers,
          credentials: 'include' as RequestCredentials
        };

        // Fetch pod details
        const podResponse = await fetch(`/api/inventory/pods/${podId}`, fetchOptions);

        // Fetch locations
        const locationsResponse = await fetch('/api/inventory/locations', fetchOptions);

        if (podResponse.status === 404) {
          setError('Pod not found');
          setLoading(false);
          return;
        }

        if (podResponse.status === 401 || locationsResponse.status === 401) {
          localStorage.removeItem('authToken');
          router.push('/auth/login');
          return;
        }

        const podData = await podResponse.json();
        const locationsData = await locationsResponse.json();

        if (podData.success) {
          setFormData({
            id: podData.data.id,
            title: podData.data.title || '',
            contents: podData.data.contents || '',
            description: podData.data.description || '',
            locationId: podData.data.locationId || '',
          });
        } else {
          setError(podData.error || 'Failed to fetch pod details');
        }

        if (locationsData.success) {
          setLocations(locationsData.data);
        }

      } catch (error) {
        console.error('Error fetching data:', error);
        setError('An unexpected error occurred');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [podId, router]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      // Get session and auth token
      const session = await getSession();

      if (!session || !session.user) {
        setError('No valid session found');
        router.push('/auth/login');
        return;
      }

      const authToken = localStorage.getItem('authToken');

      // Create a copy of form data to modify before sending
      const podData: Record<string, any> = { ...formData };

      // Only add non-empty fields to the request
      Object.keys(podData).forEach(key => {
        if (podData[key] === '') {
          delete podData[key];
        }
      });

      // Remove the id from the update data
      delete podData.id;

      const response = await fetch(`/api/inventory/pods/${podId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': authToken ? `Bearer ${authToken}` : '',
          'X-User-Id': session.user.id || '',
        },
        credentials: 'include',
        body: JSON.stringify(podData),
      });

      const data = await response.json();

      if (data.success) {
        router.push(`/pods/${podId}`);
      } else {
        setError(data.error || 'Failed to update storage pod');
        if (data.error === 'Unauthorized') {
          router.push('/auth/login');
        }
      }
    } catch (error) {
      console.error('Error updating pod:', error);
      setError('An unexpected error occurred');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-[80vh]">
        <span className="loading loading-spinner loading-lg"></span>
      </div>
    );
  }

  return (
    <div className="container mx-auto max-w-2xl py-8">
      <div className="flex items-center mb-6">
        <Link href={`/pods/${podId}`} className="btn btn-ghost btn-sm mr-4">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Back
        </Link>
        <h1 className="text-3xl font-bold">Edit Storage Pod</h1>
      </div>

      {error && (
        <div className="alert alert-error mb-6">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>{error}</span>
        </div>
      )}

      <div className="card bg-base-100 shadow-md p-4">
        <div className="card-body">
          <form onSubmit={handleSubmit}>
            <div className="form-control mb-4">
              <label className="label">
                <span className="label-text">Pod Name</span>
              </label>
              <input
                type="text"
                name="title"
                value={formData.title}
                onChange={handleChange}
                className="input input-bordered"
                required
                placeholder="e.g., Garage Storage Bin #1"
              />
            </div>

            <div className="form-control mb-4">
              <label className="label">
                <span className="label-text">Contents</span>
              </label>
              <textarea
                name="contents"
                value={formData.contents}
                onChange={handleChange}
                className="textarea textarea-bordered h-24"
                placeholder="What's inside this pod?"
              ></textarea>
            </div>

            <div className="form-control mb-4">
              <label className="label">
                <span className="label-text">Physical Description</span>
              </label>
              <input
                type="text"
                name="description"
                value={formData.description}
                onChange={handleChange}
                className="input input-bordered"
                placeholder="e.g., Black & Yellow Tote"
              />
            </div>

            <div className="form-control mb-4">
              <label className="label">
                <span className="label-text">Location</span>
              </label>
              <select
                name="locationId"
                value={formData.locationId}
                onChange={handleChange}
                className="select select-bordered"
              >
                <option value="">Select a location</option>
                {locations.map(location => (
                  <option key={location.id} value={location.id}>
                    {location.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="card-actions justify-end">
              <Link href={`/pods/${podId}`} className="btn btn-ghost">
                Cancel
              </Link>
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
  );
} 