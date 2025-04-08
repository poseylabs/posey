import React, { useState, useEffect, useRef } from 'react';
import BarcodeScanner from './BarcodeScanner';

interface BarcodeLookupProps {
  onProductFound: (productData: any) => void;
}

const BarcodeLookup: React.FC<BarcodeLookupProps> = ({ onProductFound }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [scanResult, setScanResult] = useState<string | null>(null);
  const [showScanner, setShowScanner] = useState(true);
  const [manualCode, setManualCode] = useState('');
  const [lastProcessedCode, setLastProcessedCode] = useState<string | null>(null);
  const [scannerFailed, setScannerFailed] = useState(false);
  const [mountScanner, setMountScanner] = useState(true);
  const scannerTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  
  // Cleanup function to clear any timeouts
  const clearTimeouts = () => {
    if (scannerTimeoutRef.current) {
      clearTimeout(scannerTimeoutRef.current);
      scannerTimeoutRef.current = null;
    }
  };

  // Handle scanner toggling properly with timeout cleanup
  const toggleScanner = (show: boolean) => {
    // Clear any pending timeouts
    clearTimeouts();
    
    if (!show) {
      // When hiding scanner, unmount it completely to avoid state transitions
      setShowScanner(false);
      // Use a small delay to ensure clean unmounting
      scannerTimeoutRef.current = setTimeout(() => {
        setMountScanner(false);
      }, 300);
    } else {
      // When showing scanner, mount it first, then show it
      setMountScanner(true);
      // Small delay to ensure mount happens before show
      scannerTimeoutRef.current = setTimeout(() => {
        setShowScanner(true);
      }, 300);
    }
  };
  
  // Cleanup on unmount
  useEffect(() => {
    return () => {
      clearTimeouts();
    };
  }, []);

  const handleScanSuccess = async (decodedText: string) => {
    // Avoid processing the same code twice
    if (lastProcessedCode === decodedText) {
      return;
    }
    
    // Update state
    setLastProcessedCode(decodedText);
    setScanResult(decodedText);
    setScannerFailed(false);
    
    // Hide scanner properly
    toggleScanner(false);
    
    // Process the barcode
    await lookupBarcode(decodedText);
  };

  const handleScanError = (err: any) => {
    // Only log serious errors, not the common "no barcode found" errors
    if (!err.includes('No barcode') && !err.includes('No MultiFormat Readers')) {
      console.warn('Scan error:', err);
      
      // Check for camera access or initialization errors
      if (err.includes('Permission') || err.includes('access') || err.includes('Failed to start')) {
        setScannerFailed(true);
        setError('Camera access failed. Please check your camera permissions.');
      }
    }
  };

  const lookupBarcode = async (barcode: string) => {
    console.log('lookupBarcode for barcode:', barcode);
    setLoading(true);
    setError(null);
    
    try {
      // Simulate API call with a timeout
      const timeoutPromise = new Promise<void>((resolve) => {
        scannerTimeoutRef.current = setTimeout(() => {
          setLoading(false);
          
          const testProductData = {
            title: `Product for UPC: ${barcode}`,
            description: `This is a test product for barcode: ${barcode}`,
            brand: 'Test Brand',
            category: 'Test Category',
            upc: barcode,
            source: 'Local Test'
          };
          
          onProductFound(testProductData);
          resolve();
        }, 1000);
      });
      
      await timeoutPromise;
    } catch (err) {
      console.error('Error looking up product:', err);
      setError('Failed to lookup product. Please try again.');
      setLoading(false);
    }
  };

  const handleManualSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!manualCode.trim()) return;
    
    setScanResult(manualCode);
    await lookupBarcode(manualCode);
  };

  // Render the component with key to force a clean remount if needed
  return (
    <div className="barcode-lookup mb-8">
      <div className="flex flex-col gap-4">
        {showScanner && !scannerFailed && (
          <h2 className="text-lg font-semibold">Scanning for product barcode...</h2>
        )}
        
        {scannerFailed && (
          <div className="alert alert-warning">
            <span>Camera access failed. You can still enter a barcode manually below.</span>
          </div>
        )}
        
        <div className="scanner-container">
          {mountScanner && showScanner && !scannerFailed && (
            <div key="scanner-wrapper">
              <BarcodeScanner 
                onScanSuccess={handleScanSuccess} 
                onScanFailure={handleScanError}
              />
              <button 
                className="btn btn-outline mt-2" 
                onClick={() => toggleScanner(false)}
              >
                Cancel Scanning
              </button>
            </div>
          )}
          
          {!showScanner && scanResult && !loading && !error && (
            <>
              <div className="alert alert-success mb-3">
                <span>Barcode scanned successfully: {scanResult}</span>
              </div>
              <button 
                className="btn btn-primary"
                onClick={() => {
                  setScanResult(null);
                  toggleScanner(true);
                }}
              >
                Scan Again
              </button>
            </>
          )}
        </div>

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
      </div>
    </div>
  );
};

export default BarcodeLookup; 