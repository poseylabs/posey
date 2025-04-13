"use client";

import { useState, useEffect, FormEvent } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { getSession } from '@posey.ai/core';

interface StoragePod {
  id: string;
  title: string;
}

interface Location {
  id: string;
  name: string;
  description?: string;
  address?: string;
  address2?: string;
  city?: string;
  state?: string;
  zip?: string;
  country?: string;
  latitude?: number;
  longitude?: number;
}

export default function NewPodPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const parentIdParam = searchParams.get('parentId');

  const [parentPods, setParentPods] = useState<StoragePod[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showLocationModal, setShowLocationModal] = useState(false);
  const [creatingLocation, setCreatingLocation] = useState(false);
  const [newLocation, setNewLocation] = useState({
    name: '',
    description: '',
    address: '',
    address2: '',
    city: '',
    state: '',
    zip: '',
    country: '',
    latitude: null as number | null,
    longitude: null as number | null
  });
  const [gettingLocation, setGettingLocation] = useState(false);
  const [showAddressFields, setShowAddressFields] = useState(false);

  const [formData, setFormData] = useState({
    title: '',
    contents: '',
    description: '',
    locationId: '',
    parentId: parentIdParam || '',
  });

  // If parentId changes in URL, update form data
  useEffect(() => {
    if (parentIdParam) {
      setFormData(prev => ({ ...prev, parentId: parentIdParam }));

      // Fetch parent pod details to get its location
      const fetchParentPodDetails = async () => {
        try {
          // Validate session first
          const session = await getSession();

          if (!session || !session.user) {
            console.error('No valid session found');
            return;
          }

          // Get auth token from localStorage
          const authToken = localStorage.getItem('authToken');
          const headers = {
            'Authorization': authToken ? `Bearer ${authToken}` : '',
            'Content-Type': 'application/json',
            'X-User-Id': session.user.id || '',
          };

          const response = await fetch(`/api/inventory/pods/${parentIdParam}`, {
            headers,
            credentials: 'include'
          });

          if (response.status === 401) {
            return;
          }

          const data = await response.json();

          if (data.success && data.data.locationId) {
            // Set the locationId to match the parent pod's location
            setFormData(prev => ({ ...prev, locationId: data.data.locationId }));
          }
        } catch (error) {
          console.error('Error fetching parent pod details:', error);
        }
      };

      fetchParentPodDetails();
    }
  }, [parentIdParam]);

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

        console.log('Using user ID for API calls:', session.user.id);

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

        // Fetch parent pods
        const podsResponse = await fetch('/api/inventory/pods', fetchOptions);

        // Fetch locations
        const locationsResponse = await fetch('/api/inventory/locations', fetchOptions);

        if (podsResponse.status === 401 || locationsResponse.status === 401) {
          localStorage.removeItem('authToken');
          router.push('/auth/login');
          return;
        }

        const podsData = await podsResponse.json();
        const locationsData = await locationsResponse.json();

        if (podsData.success) {
          setParentPods(podsData.data);
        }

        if (locationsData.success) {
          setLocations(locationsData.data);
        }

      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [router]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleLocationChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const { value } = e.target;

    if (value === 'new') {
      setShowLocationModal(true);
      setShowAddressFields(false);
      setNewLocation({
        name: '',
        description: '',
        address: '',
        address2: '',
        city: '',
        state: '',
        zip: '',
        country: '',
        latitude: null,
        longitude: null
      });
    } else {
      setFormData(prev => ({ ...prev, locationId: value }));
    }
  };

  const handleNewLocationChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setNewLocation(prev => ({ ...prev, [name]: value }));
  };

  const handleLatLngChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    const numValue = value === '' ? null : parseFloat(value);
    setNewLocation(prev => ({ ...prev, [name]: numValue }));
  };

  const getCurrentLocation = () => {
    if (!navigator.geolocation) {
      setError('Geolocation is not supported by your browser');
      return;
    }

    setGettingLocation(true);

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setNewLocation(prev => ({
          ...prev,
          latitude: position.coords.latitude,
          longitude: position.coords.longitude
        }));
        setGettingLocation(false);
      },
      (error) => {
        setError(`Unable to retrieve your location: ${error.message}`);
        setGettingLocation(false);
      },
      { enableHighAccuracy: true }
    );
  };

  const createNewLocation = async () => {
    if (!newLocation.name.trim()) {
      setError('Location name is required');
      return null;
    }

    setCreatingLocation(true);

    try {
      const session = await getSession();

      if (!session || !session.user) {
        setError('No valid session found');
        router.push('/auth/login');
        return null;
      }

      const authToken = localStorage.getItem('authToken');

      const response = await fetch('/api/inventory/locations', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': authToken ? `Bearer ${authToken}` : '',
          'X-User-Id': session.user.id || '',
        },
        credentials: 'include',
        body: JSON.stringify(newLocation),
      });

      const data = await response.json();

      if (data.success) {
        const newLocationData = data.data;
        setLocations(prev => [...prev, newLocationData]);
        setFormData(prev => ({ ...prev, locationId: newLocationData.id }));
        setShowLocationModal(false);
        setNewLocation({
          name: '',
          description: '',
          address: '',
          address2: '',
          city: '',
          state: '',
          zip: '',
          country: '',
          latitude: null,
          longitude: null
        });
        return newLocationData.id;
      } else {
        setError(data.error || 'Failed to create location');
        return null;
      }
    } catch (error) {
      console.error('Error creating location:', error);
      setError('Failed to create location');
      return null;
    } finally {
      setCreatingLocation(false);
    }
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

      const response = await fetch('/api/inventory/pods', {
        method: 'POST',
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
        router.push('/pods');
      } else {
        setError(data.error || 'Failed to create storage pod');
        if (data.error === 'Unauthorized') {
          router.push('/auth/login');
        }
      }
    } catch (error) {
      console.error('Error creating pod:', error);
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
    <div className="container mx-auto max-w-2xl">
      <div className="flex items-center mb-6">
        <Link href="/pods" className="btn btn-ghost btn-sm mr-4">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Back
        </Link>
        <h1 className="text-3xl font-bold">Create New Storage Pod</h1>
      </div>

      {error && (
        <div className="alert alert-error mb-6">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>{error}</span>
        </div>
      )}

      {/* Location Modal */}
      {showLocationModal && (
        <div className="modal modal-open">
          <div className="modal-box">
            <h3 className="font-bold text-lg mb-4">Add New Location</h3>

            <div className="form-control mb-4">
              <label className="label">
                <span className="label-text">Location Name</span>
              </label>
              <input
                type="text"
                name="name"
                value={newLocation.name}
                onChange={handleNewLocationChange}
                className="input input-bordered"
                required
                placeholder="e.g., Garage, Basement, Kitchen"
              />
            </div>

            <div className="form-control mb-4">
              <label className="label">
                <span className="label-text">Description (Optional)</span>
              </label>
              <input
                type="text"
                name="description"
                value={newLocation.description}
                onChange={handleNewLocationChange}
                className="input input-bordered"
                placeholder="Any details about this location"
              />
            </div>

            <div className="grid grid-cols-2 gap-4 mb-4">
              <div className="form-control">
                <label className="label">
                  <span className="label-text">Latitude</span>
                </label>
                <input
                  type="number"
                  name="latitude"
                  value={newLocation.latitude === null ? '' : newLocation.latitude}
                  onChange={handleLatLngChange}
                  className="input input-bordered"
                  step="any"
                  placeholder="e.g. 40.7128"
                />
              </div>

              <div className="form-control">
                <label className="label">
                  <span className="label-text">Longitude</span>
                </label>
                <input
                  type="number"
                  name="longitude"
                  value={newLocation.longitude === null ? '' : newLocation.longitude}
                  onChange={handleLatLngChange}
                  className="input input-bordered"
                  step="any"
                  placeholder="e.g. -74.0060"
                />
              </div>
            </div>

            <div className="flex justify-center mb-4 gap-2">
              <button
                type="button"
                className={`btn btn-outline flex-1 ${gettingLocation ? 'loading' : ''}`}
                onClick={getCurrentLocation}
                disabled={gettingLocation}
              >
                {!gettingLocation && (
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
                  </svg>
                )}
                {gettingLocation ? 'Getting Location...' : 'Get Current Location'}
              </button>

              <button
                type="button"
                className={`btn btn-outline flex-1 ${showAddressFields ? 'btn-active' : ''}`}
                onClick={() => setShowAddressFields(!showAddressFields)}
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M4 4a2 2 0 012-2h8a2 2 0 012 2v12a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 0h8v12H6V4z" />
                  <path fillRule="evenodd" d="M10 10a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
                </svg>
                Enter Address
              </button>
            </div>

            {/* Collapsible address fields */}
            {showAddressFields && (
              <div className="border border-base-300 bg-base-100 rounded-md p-4 mb-4">
                <h4 className="font-medium mb-3">Address Details</h4>

                <div className="form-control mb-4">
                  <label className="label">
                    <span className="label-text">Address</span>
                  </label>
                  <input
                    type="text"
                    name="address"
                    value={newLocation.address}
                    onChange={handleNewLocationChange}
                    className="input input-bordered"
                    placeholder="Street address"
                  />
                </div>

                <div className="form-control mb-4">
                  <label className="label">
                    <span className="label-text">Address Line 2 (Optional)</span>
                  </label>
                  <input
                    type="text"
                    name="address2"
                    value={newLocation.address2}
                    onChange={handleNewLocationChange}
                    className="input input-bordered"
                    placeholder="Apt, Suite, Building, etc."
                  />
                </div>

                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div className="form-control">
                    <label className="label">
                      <span className="label-text">City</span>
                    </label>
                    <input
                      type="text"
                      name="city"
                      value={newLocation.city}
                      onChange={handleNewLocationChange}
                      className="input input-bordered w-full"
                      placeholder="City"
                    />
                  </div>

                  <div className="form-control">
                    <label className="label">
                      <span className="label-text">State/Province</span>
                    </label>
                    <input
                      type="text"
                      name="state"
                      value={newLocation.state}
                      onChange={handleNewLocationChange}
                      className="input input-bordered w-full"
                      placeholder="State/Province"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="form-control">
                    <label className="label">
                      <span className="label-text">ZIP/Postal Code</span>
                    </label>
                    <input
                      type="text"
                      name="zip"
                      value={newLocation.zip}
                      onChange={handleNewLocationChange}
                      className="input input-bordered w-full"
                      placeholder="ZIP/Postal Code"
                    />
                  </div>

                  <div className="form-control">
                    <label className="label">
                      <span className="label-text">Country</span>
                    </label>
                    <input
                      type="text"
                      name="country"
                      value={newLocation.country}
                      onChange={handleNewLocationChange}
                      className="input input-bordered w-full"
                      placeholder="Country"
                    />
                  </div>
                </div>
              </div>
            )}

            <div className="modal-action">
              <button
                type="button"
                className="btn btn-ghost"
                onClick={() => setShowLocationModal(false)}
              >
                Cancel
              </button>
              <button
                type="button"
                className={`btn btn-primary ${creatingLocation ? 'loading' : ''}`}
                onClick={createNewLocation}
                disabled={creatingLocation || !newLocation.name.trim()}
              >
                {creatingLocation ? 'Creating...' : 'Create Location'}
              </button>
            </div>
          </div>
          <div className="modal-backdrop" onClick={() => setShowLocationModal(false)}></div>
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
              <div className="flex gap-2">
                <select
                  name="locationId"
                  value={formData.locationId}
                  onChange={handleLocationChange}
                  className="select select-bordered flex-1"
                >
                  <option value="">Select a location</option>
                  {locations.map(location => (
                    <option key={location.id} value={location.id}>
                      {location.name}
                    </option>
                  ))}
                </select>
                <button
                  type="button"
                  className="btn btn-outline"
                  onClick={() => setShowLocationModal(true)}
                >
                  Add New
                </button>
              </div>
            </div>

            <div className="form-control mb-6">
              <label className="label">
                <span className="label-text">Parent Pod (Optional)</span>
              </label>
              <select
                name="parentId"
                value={formData.parentId}
                onChange={handleChange}
                className="select select-bordered"
              >
                <option value="">None (Root Level)</option>
                {parentPods.map(pod => (
                  <option key={pod.id} value={pod.id}>{pod.title}</option>
                ))}
              </select>
            </div>

            <div className="card-actions justify-end">
              <Link href="/pods" className="btn btn-ghost">
                Cancel
              </Link>
              <button
                type="submit"
                className={`btn btn-primary ${submitting ? 'loading' : ''}`}
                disabled={submitting}
              >
                {submitting ? 'Creating...' : 'Create Pod'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
} 