"use client";

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { getSession } from '@posey.ai/core';
import { use } from 'react';

interface StoragePod {
  id: string;
  title: string;
  contents?: string;
  description?: string;
  location?: {
    name: string;
  };
}

// Label size options
interface LabelSize {
  name: string;
  width: number;
  height: number;
  description: string;
}

const LABEL_SIZES: LabelSize[] = [
  { 
    name: '4x6', 
    width: 152.4, 
    height: 101.6, 
    description: 'Shipping Label (4 x 6 inches)' 
  },
  { 
    name: '2x4', 
    width: 101.6, 
    height: 50.8, 
    description: 'Small Label (2 x 4 inches)' 
  }
];

export default function PodLabelPage({ params }: { params: Promise<{ id: string }> }) {
  const unwrappedParams = use(params);
  const podId = unwrappedParams.id;

  const router = useRouter();
  const [pod, setPod] = useState<StoragePod | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isGeneratingLabel, setIsGeneratingLabel] = useState(false);
  const [selectedSize, setSelectedSize] = useState<LabelSize>(LABEL_SIZES[0]);
  const [labelSvgContent, setLabelSvgContent] = useState<string | null>(null);

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
          console.error('Unauthorized access, redirecting to login');
          localStorage.removeItem('authToken');
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

  const generateLabel = useCallback(async () => {
    setIsGeneratingLabel(true);
    try {
      const session = await getSession();
      const authToken = localStorage.getItem('authToken');
      
      if (!pod) {
        throw new Error('Pod data not available');
      }
      
      const response = await fetch(`/api/inventory/pods/${podId}/generate-label-svg`, {
        method: 'POST',
        headers: {
          'Authorization': authToken ? `Bearer ${authToken}` : '',
          'Content-Type': 'application/json',
          'X-User-Id': session?.user?.id || '',
        },
        body: JSON.stringify({
          title: pod.title,
          contents: pod.contents,
          id: pod.id,
          location: pod.location?.name,
          width: selectedSize.width,
          height: selectedSize.height
        }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to generate label');
      }
      
      // Get the SVG content as text
      const svgContent = await response.text();
      setLabelSvgContent(svgContent);
    } catch (error) {
      console.error('Error generating label:', error);
      alert('Failed to generate label. Please try again.');
    } finally {
      setIsGeneratingLabel(false);
    }
  }, [pod, podId, selectedSize]);

  const handlePrint = () => {
    if (!labelSvgContent) return;
    
    const printWindow = window.open('', '_blank');
    if (!printWindow) {
      alert('Please allow pop-ups to print the label');
      return;
    }
    
    printWindow.document.write(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>Print Label - ${pod?.title || 'Label'}</title>
          <style>
            body {
              margin: 0;
              padding: 0;
              display: flex;
              justify-content: center;
              align-items: center;
              height: 100vh;
            }
            svg {
              max-width: 100%;
              height: auto;
            }
            @media print {
              body {
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
              }
            }
          </style>
        </head>
        <body onload="window.print(); window.setTimeout(function(){ window.close(); }, 500);window.close();">
          ${labelSvgContent}
        </body>
      </html>
    `);
    printWindow.document.close();
  };

  // Generate label when pod data loads or size changes
  useEffect(() => {
    if (pod && !loading && !error) {
      generateLabel();
    }
  }, [error, generateLabel, loading, pod, selectedSize]);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-[80vh]">
        <span className="loading loading-spinner loading-lg"></span>
      </div>
    );
  }

  if (error || !pod) {
    return (
      <div className="container mx-auto max-w-4xl py-8">
        <div className="alert alert-error">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>{error || 'Pod not found'}</span>
        </div>
        <div className="flex justify-center mt-6">
          <Link href={`/pods/${podId}`} className="btn btn-primary">
            Back to Pod
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto max-w-4xl py-8">
      <div className="flex justify-between items-center mb-6 print:hidden">
        <div className="flex items-center">
          <Link href={`/pods/${podId}`} className="btn btn-ghost btn-sm mr-4">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Back to Pod
          </Link>
          <h1 className="text-3xl font-bold">Pod Label</h1>
        </div>
        <div className="flex items-center gap-2">
          <select 
            className="select select-bordered"
            value={selectedSize.name}
            onChange={(e) => {
              const size = LABEL_SIZES.find(size => size.name === e.target.value);
              if (size) setSelectedSize(size);
            }}
          >
            {LABEL_SIZES.map(size => (
              <option key={size.name} value={size.name}>
                {size.description}
              </option>
            ))}
          </select>
          <button
            onClick={handlePrint}
            className="btn btn-primary print:hidden"
            disabled={isGeneratingLabel || !labelSvgContent}
          >
            {isGeneratingLabel ? (
              <>
                <span className="loading loading-spinner loading-xs mr-2"></span>
                Generating...
              </>
            ) : (
              <>
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
                </svg>
                Print Label
              </>
            )}
          </button>
        </div>
      </div>

      {/* Label Preview */}
      <div className="mb-8 flex justify-center">
        {labelSvgContent ? (
          <div 
            className="border border-gray-300 bg-white"
            dangerouslySetInnerHTML={{ __html: labelSvgContent }}
          />
        ) : (
          <div className="w-full max-w-md h-[400px] flex items-center justify-center border border-gray-300 bg-gray-100">
            <div className="text-center">
              {isGeneratingLabel ? (
                <>
                  <span className="loading loading-spinner loading-lg"></span>
                  <p className="mt-4">Generating label preview...</p>
                </>
              ) : (
                <p>No preview available</p>
              )}
            </div>
          </div>
        )}
      </div>

      <div className="print:hidden mb-8">
        <h2 className="text-xl font-semibold mb-3">Label Options</h2>
        <div className="card bg-base-100 shadow-md">
          <div className="card-body">
            <p className="mb-4">This page shows a label preview for your storage pod. When you click "Print Label", your browser will print the label directly.</p>
            <div className="alert alert-info">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" className="stroke-current shrink-0 w-6 h-6">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
              <span>For best results, use label stickers that match your selected size.</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 