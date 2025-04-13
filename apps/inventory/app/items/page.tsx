"use client";

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { getSession } from '@posey.ai/core';

interface Item {
  id: string;
  title: string;
  description?: string;
  quantity: number;
  podId?: string;
  pod?: {
    id: string;
    title: string;
  };
}

export default function ItemsPage() {
  const router = useRouter();
  const [items, setItems] = useState<Item[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      const session = await getSession();
      if (!session?.user) {
        router.push('/login');
        return;
      }

      fetchItems();
    };

    checkAuth();
  }, [router]);

  const fetchItems = async () => {
    try {
      const response = await fetch('/api/inventory/items');
      if (!response.ok) {
        throw new Error('Failed to fetch items');
      }
      const data = await response.json();
      setItems(data.data || []);
    } catch (error) {
      console.error('Error fetching items:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="container mx-auto py-12 text-center">Loading items...</div>;
  }

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">All Items</h1>
        <Link href="/items/new" className="btn btn-primary">
          Add New Item
        </Link>
      </div>

      {items.length === 0 ? (
        <div className="text-center py-12">
          <h3 className="text-xl mb-2">No items found</h3>
          <p className="text-gray-500 mb-6">Start by adding your first item</p>
          <Link href="/items/new" className="btn btn-primary">
            Add Your First Item
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {items.map((item) => (
            <div key={item.id} className="card bg-base-100 shadow-md">
              <div className="card-body">
                <h2 className="card-title">{item.title}</h2>
                {item.description && <p className="text-sm">{item.description}</p>}
                <div className="flex justify-between mt-2">
                  <span className="badge">Qty: {item.quantity}</span>
                  {item.pod && (
                    <Link href={`/pods/${item.pod.id}`} className="text-sm text-blue-500 hover:underline">
                      In: {item.pod.title}
                    </Link>
                  )}
                </div>
                <div className="card-actions justify-end mt-3">
                  <Link href={`/items/${item.id}`} className="btn btn-sm btn-outline">
                    View Details
                  </Link>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
} 