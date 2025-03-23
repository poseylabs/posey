import React, { useState } from 'react';
import BarcodeScanner from './BarcodeScanner';

interface BarcodeLookupProps {
  onProductFound: (productData: any) => void;
}

interface LookupResult {
  title: string;
  description: string;
  brand?: string;
  category?: string;
  upc: string;
  source: string;
  originalData: any;
}

const BarcodeLookup: React.FC<BarcodeLookupProps> = ({ onProductFound }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [scanResult, setScanResult] = useState<string | null>(null);
  const [showScanner, setShowScanner] = useState(false);
  const [manualCode, setManualCode] = useState('');

  const handleScanSuccess = async (decodedText: string) => {
    if (scanResult === decodedText) {
      return;
    }
    setScanResult(decodedText);
    setShowScanner(false);
    await lookupBarcode(decodedText);
  };

  const handleScanError = (err: any) => {
    console.warn(err);
  };

  const lookupBarcode = async (barcode: string) => {
    console.log('lookupBarcode (temp disabled)....');
    // setLoading(true);
    // setError(null);
    
    // try {
    //   const response = await fetch(`/api/inventory/lookup?upc=${encodeURIComponent(barcode)}`);
    //   const data = await response.json();
      
    //   if (data.success && data.data) {
    //     onProductFound(data.data);
    //   } else {
    //     setError(data.message || 'Product not found');
    //   }
    // } catch (err) {
    //   console.error('Error looking up product:', err);
    //   setError('Failed to lookup product. Please try again.');
    // } finally {
    //   setLoading(false);
    // }
  };

  const handleManualSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!manualCode.trim()) return;
    
    setScanResult(manualCode);
    await lookupBarcode(manualCode);
  };

  return (
    <div className="barcode-lookup mb-8">
      <div className="flex flex-col gap-4">
        <h2 className="text-lg font-semibold">Find Product by Barcode</h2>
        
        {!showScanner ? (
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => setShowScanner(true)}
          >
            Scan Barcode
          </button>
        ) : (
          <div className="scanner-container">
            <BarcodeScanner 
              onScanSuccess={handleScanSuccess} 
              onScanFailure={handleScanError}
            />
            <button 
              className="btn btn-outline mt-2" 
              onClick={() => setShowScanner(false)}
            >
              Cancel Scanning
            </button>
          </div>
        )}

        <div className="divider">OR</div>

        <form onSubmit={handleManualSubmit} className="flex flex-col gap-3">
          <div className="form-control">
            <label className="label">
              <span className="label-text">Enter barcode manually</span>
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                className="input input-bordered flex-1"
                value={manualCode}
                onChange={(e) => setManualCode(e.target.value)}
                placeholder="Enter UPC/EAN code"
              />
              <button 
                type="submit" 
                className="btn btn-primary"
                disabled={loading || !manualCode.trim()}
              >
                Lookup
              </button>
            </div>
          </div>
        </form>

        {loading && (
          <div className="loading-indicator">
            <span className="loading loading-spinner loading-md"></span>
            <span className="ml-2">Looking up product...</span>
          </div>
        )}

        {error && (
          <div className="alert alert-error">
            <span>{error}</span>
          </div>
        )}

        {scanResult && !loading && !error && (
          <div className="alert alert-info">
            <span>Last scanned code: {scanResult}</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default BarcodeLookup; 