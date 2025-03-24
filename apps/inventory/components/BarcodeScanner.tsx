import React, { useEffect, useRef, useState } from 'react';
import { Html5Qrcode, Html5QrcodeSupportedFormats } from 'html5-qrcode';

interface BarcodeScannerProps {
  onScanSuccess: (decodedText: string, decodedResult: any) => void;
  onScanFailure?: (error: any) => void;
  width?: number;
  height?: number;
  fps?: number;
  qrbox?: { width: number; height: number };
}

const BarcodeScanner: React.FC<BarcodeScannerProps> = ({
  onScanSuccess,
  onScanFailure,
  width = 300,
  height = 300,
  fps = 10,
  qrbox = { width: 250, height: 250 },
}) => {
  const scannerRef = useRef<Html5Qrcode | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [isCameraReady, setIsCameraReady] = useState(false);
  const [scannerError, setScannerError] = useState<string | null>(null);
  const errorCountRef = useRef(0);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const initAttemptRef = useRef(0);
  const hasInitializedRef = useRef(false);
  const timeoutIdRef = useRef<NodeJS.Timeout | null>(null);

  // Wrap onScanSuccess to handle stopping the scanner after a successful scan
  const handleScanSuccess = (decodedText: string, decodedResult: any) => {
    // Only process if we're not already transitioning
    if (isTransitioning) return;
    
    // Stop scanning automatically after a successful scan
    if (scannerRef.current && isScanning) {
      setIsTransitioning(true);
      scannerRef.current.stop()
        .then(() => {
          console.log('Scanner stopped after successful scan');
          setIsScanning(false);
          setIsTransitioning(false);
          // Call the parent's onScanSuccess callback with the decoded text and result
          onScanSuccess(decodedText, decodedResult);
        })
        .catch((err) => {
          console.error('Error stopping scanner after successful scan:', err);
          setIsTransitioning(false);
        });
    }
  };

  // Custom scan failure handler to prevent console spam
  const handleScanFailure = (error: any) => {
    // These are normal "no barcode found" errors that we can ignore
    const isCommonError = 
      error.includes('No barcode or QR code detected') || 
      error.includes('No MultiFormat Readers were able to detect the code');
    
    if (!isCommonError) {
      errorCountRef.current += 1;
      
      // Only log real errors and only the first few occurrences
      if (errorCountRef.current < 3) {
        console.warn('Scanner error (not a common one):', error);
      }
      
      // If we get too many errors, show a message to the user
      if (errorCountRef.current === 10) {
        setScannerError("Having trouble scanning? Make sure the barcode is well-lit and in frame.");
      }
    }
    
    // Call the original onScanFailure if provided
    if (onScanFailure) {
      onScanFailure(error);
    }
  };

  useEffect(() => {
    // Prevent double initialization in React strict mode
    if (hasInitializedRef.current) return;
    
    // Mark as initialized to prevent duplicate setup
    hasInitializedRef.current = true;
    
    // Initialize scanner
    if (containerRef.current) {
      try {
        // Check if we already have a scanner instance and clean it up first
        if (scannerRef.current) {
          try {
            scannerRef.current.clear();
          } catch (error) {
            console.warn('Error clearing existing scanner:', error);
          }
        }
        
        const htmlScanner = new Html5Qrcode('scanner-container');
        scannerRef.current = htmlScanner;
  
        // Get available cameras and start scanning with the first camera
        Html5Qrcode.getCameras()
          .then((devices) => {
            if (devices && devices.length) {
              // Use the first camera (typically the back camera on mobile)
              setIsCameraReady(true);
              
              // Wait a moment before starting the scanner to ensure the DOM is ready
              // Clear any existing timeout to prevent duplication
              if (timeoutIdRef.current) {
                clearTimeout(timeoutIdRef.current);
              }
              
              timeoutIdRef.current = setTimeout(() => {
                if (!isScanning && !isTransitioning) {
                  startScanning(devices[0].id);
                }
              }, 800);
            } else {
              setScannerError("No cameras found. Please ensure camera access is allowed.");
            }
          })
          .catch((err) => {
            console.error('Error getting cameras', err);
            setScannerError("Failed to access the camera. Please check your camera permissions.");
          });
      } catch (error) {
        console.error('Error initializing scanner:', error);
        setScannerError("Failed to initialize scanner. Please try again.");
      }
    }

    return () => {
      // Clean up scanner and any pending timeouts on unmount
      if (timeoutIdRef.current) {
        clearTimeout(timeoutIdRef.current);
        timeoutIdRef.current = null;
      }
      
      cleanupScanner();
    };
  }, []);

  const cleanupScanner = async () => {
    if (!scannerRef.current) return;
    
    try {
      setIsTransitioning(true);
      
      // Only call stop() if we are actually scanning
      if (isScanning) {
        await scannerRef.current.stop();
        console.log('Scanner stopped during cleanup');
      }
      
      // Try to clear the scanner instance
      try {
        scannerRef.current.clear();
      } catch (e) {
        console.warn('Error clearing scanner:', e);
      }
      
      // Reset the scanner reference
      scannerRef.current = null;
    } catch (err) {
      console.error('Error cleaning up scanner:', err);
    } finally {
      setIsTransitioning(false);
      setIsScanning(false);
      hasInitializedRef.current = false;
    }
  };

  const startScanning = async (cameraId: string) => {
    // Don't start if scanner not initialized, already scanning, or transitioning
    if (!scannerRef.current || isScanning || isTransitioning) return;

    try {
      setIsTransitioning(true);
      setIsScanning(true);
      
      await scannerRef.current.start(
        cameraId,
        {
          fps,
          qrbox,
          aspectRatio: 1,
          // Support all formats for barcode scanning
          formatsToSupport: [
            Html5QrcodeSupportedFormats.AZTEC,
            Html5QrcodeSupportedFormats.CODABAR,
            Html5QrcodeSupportedFormats.CODE_39,
            Html5QrcodeSupportedFormats.CODE_93,
            Html5QrcodeSupportedFormats.CODE_128,
            Html5QrcodeSupportedFormats.DATA_MATRIX,
            Html5QrcodeSupportedFormats.EAN_8,
            Html5QrcodeSupportedFormats.EAN_13,
            Html5QrcodeSupportedFormats.ITF,
            Html5QrcodeSupportedFormats.MAXICODE,
            Html5QrcodeSupportedFormats.PDF_417,
            Html5QrcodeSupportedFormats.QR_CODE,
            Html5QrcodeSupportedFormats.RSS_14,
            Html5QrcodeSupportedFormats.RSS_EXPANDED,
            Html5QrcodeSupportedFormats.UPC_A,
            Html5QrcodeSupportedFormats.UPC_E,
            Html5QrcodeSupportedFormats.UPC_EAN_EXTENSION,
          ],
        } as any, // Type casting as any to bypass the type error temporarily
        handleScanSuccess,
        handleScanFailure
      );
      
      console.log('Scanner started successfully');
    } catch (err) {
      console.error('Error starting scanner:', err);
      setIsScanning(false);
      
      // Track initialization attempts
      initAttemptRef.current += 1;
      
      // If we've failed multiple times, show a user-friendly error
      if (initAttemptRef.current >= 2) {
        setScannerError("Failed to start the camera. Please try again or use manual entry.");
      }
    } finally {
      setIsTransitioning(false);
    }
  };

  return (
    <div className="barcode-scanner">
      <div
        id="scanner-container"
        ref={containerRef}
        style={{ width: `${width}px`, height: `${height}px` }}
        className="mx-auto border border-gray-300 rounded overflow-hidden mb-4"
      ></div>

      <div className="text-center">
        {(isScanning || isTransitioning) && !scannerError && (
          <div className="flex items-center justify-center text-sm mt-2">
            <span className="loading loading-spinner loading-sm mr-2"></span>
            <span>Scanning for barcodes...</span>
          </div>
        )}
        
        {scannerError && (
          <div className="alert alert-error mt-2">
            <span>{scannerError}</span>
          </div>
        )}
        
        {!isScanning && !isTransitioning && isCameraReady && !scannerError && (
          <div className="text-sm text-gray-500 mt-2">
            Camera ready. Waiting for a barcode...
          </div>
        )}
      </div>
    </div>
  );
};

export default BarcodeScanner; 