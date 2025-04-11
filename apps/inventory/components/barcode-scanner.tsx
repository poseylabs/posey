import React, { useCallback, useEffect, useRef, useState } from 'react';
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

  const [isScanning, setIsScanning] = useState(false);
  const [isCameraReady, setIsCameraReady] = useState(false);
  const [scannerError, setScannerError] = useState<string | null>(null);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [activeBarcode, setActiveBarcode] = useState<string | null>(null);

  const scannerRef = useRef<Html5Qrcode | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const errorCountRef = useRef(0);
  const initAttemptRef = useRef(0);
  const hasInitializedRef = useRef(false);
  const timeoutIdRef = useRef<NodeJS.Timeout | null>(null);

  // Refs to hold the current state values for use in callbacks without causing dependency changes
  const isScanningRef = useRef(isScanning);
  const isTransitioningRef = useRef(isTransitioning);

  // Keep refs updated with the latest state
  useEffect(() => {
    isScanningRef.current = isScanning;
  }, [isScanning]);

  useEffect(() => {
    isTransitioningRef.current = isTransitioning;
  }, [isTransitioning]);

  // Stable scan failure handler
  const handleScanFailure = useCallback((error: any) => {
    // console.log("handleScanFailure called with:", {
    //   error
    // });
    const isCommonError =
      error.includes('No barcode or QR code detected') ||
      error.includes('No MultiFormat Readers were able to detect the code');

    if (!isCommonError) {
      errorCountRef.current += 1;
      if (errorCountRef.current < 3) {
        // console.warn('Scanner error (not a common one):', error);
      }
      if (errorCountRef.current === 10) {
        setScannerError("Having trouble scanning? Make sure the barcode is well-lit and in frame.");
      }
    }

    if (onScanFailure) {
      onScanFailure(error);
    }
  }, [onScanFailure]);

  // Stable cleanup function
  const cleanupScanner = useCallback(async () => {
    if (!scannerRef.current) return;

    // Get the current scanner instance before potentially nullifying it
    const currentScanner = scannerRef.current;
    scannerRef.current = null; // Prevent further operations on this instance

    try {
      setIsTransitioning(true); // Update state

      // Use ref to check if scanning before stopping
      if (isScanningRef.current) {
        await currentScanner.stop();
        // console.log('Scanner stopped during cleanup');
      }

      // Clear the scanner instance (this might throw if already stopped/cleaned)
      try {
        await currentScanner.clear(); // Ensure clear is awaited if it returns a promise
        // console.log('Scanner cleared during cleanup');
      } catch (e) {
        // Ignore errors here as the scanner might already be in a cleared state
        console.warn('Minor error during scanner clear (likely harmless):', e);
      }
      console.log("Scanner cleaned up successfully.");
    } catch (err) {
      // Log errors specifically from the stop() call
      console.error('Error stopping scanner during cleanup:', err);
    } finally {
      setIsTransitioning(false); // Update state
      setIsScanning(false); // Ensure scanning state is reset
      hasInitializedRef.current = false; // Allow re-initialization if component remounts
    }
  }, []); // No dependencies, this function's identity is stable

  // Stable start scanning function - Modified to use constraints instead of cameraId
  const startScanning = useCallback(async () => {
    // Check refs, ensure scanner instance exists
    if (!scannerRef.current || isScanningRef.current || isTransitioningRef.current) {
      console.log('Start scanning condition not met:', {
        hasScanner: !!scannerRef.current,
        isScanning: isScanningRef.current,
        isTransitioning: isTransitioningRef.current,
      });
      return;
    }

    try {
      setIsTransitioning(true); // Update state
      setIsScanning(true); // Update state
      setScannerError(null); // Clear previous errors
      initAttemptRef.current = 0; // Reset attempts

      // Use constraints: prefer back camera (environment)
      const cameraConstraints = { facingMode: "environment" };

      await scannerRef.current.start(
        cameraConstraints, // Use constraints object
        {
          fps,
          qrbox
        },
        (barcode, decodedResult) => {
          // handleScanSuccess(barcode, decodedResult);
          if (barcode && barcode !== activeBarcode) {
            console.log("Scanned new barcode:", {
              barcode,
              decodedResult
            });
            setActiveBarcode(barcode);
            if (typeof onScanSuccess === 'function') {
              onScanSuccess(barcode, decodedResult);
            }
            cleanupScanner();
          }
        },
        handleScanFailure
      );

      console.log("Scanner start() method resolved successfully.");

      // NOTE: Removed immediate state updates here to prevent conflict
      // setTimeout(() => {
      //   setIsCameraReady(true); // Set camera ready state on successful start
      // }, 0);

    } catch (err) {
      console.error('Error starting scanner:', err);
      // Delay state updates slightly here too
      setTimeout(() => {
        setIsScanning(false); // Update state on error
        setIsCameraReady(false); // Ensure camera ready is false on error

        initAttemptRef.current += 1;
        if (initAttemptRef.current >= 2) {
          setScannerError("Failed to start the camera. Please check permissions or try again.");
        } else {
          setScannerError("Could not start camera. Please ensure permissions are granted.");
        }
      }, 0);
    } finally {
      // NOTE: Removed immediate state update here too
      // setTimeout(() => {
      //    setIsTransitioning(false); // Update state
      // }, 0);
    }
    // Dependencies: stable callbacks and config props
  }, [fps, qrbox, handleScanFailure]);


  // Main effect for initialization and cleanup - runs only once on mount/unmount
  useEffect(() => {
    // Prevent double initialization
    if (hasInitializedRef.current) return;
    hasInitializedRef.current = true;

    if (containerRef.current) {
      const scannerContainerId = 'scanner-container';
      if (!document.getElementById(scannerContainerId)) {
        console.error(`Scanner container element with ID '${scannerContainerId}' not found.`);
        setScannerError("Scanner UI element is missing.");
        return;
      }

      // Initialize scanner instance
      try {
        const htmlScanner = new Html5Qrcode(scannerContainerId, {
          // Configure formats here
          formatsToSupport: [
            Html5QrcodeSupportedFormats.AZTEC, Html5QrcodeSupportedFormats.CODABAR,
            Html5QrcodeSupportedFormats.CODE_39, Html5QrcodeSupportedFormats.CODE_93,
            Html5QrcodeSupportedFormats.CODE_128, Html5QrcodeSupportedFormats.DATA_MATRIX,
            Html5QrcodeSupportedFormats.EAN_8, Html5QrcodeSupportedFormats.EAN_13,
            Html5QrcodeSupportedFormats.ITF, Html5QrcodeSupportedFormats.MAXICODE,
            Html5QrcodeSupportedFormats.PDF_417, Html5QrcodeSupportedFormats.QR_CODE,
            Html5QrcodeSupportedFormats.RSS_14, Html5QrcodeSupportedFormats.RSS_EXPANDED,
            Html5QrcodeSupportedFormats.UPC_A, Html5QrcodeSupportedFormats.UPC_E,
            Html5QrcodeSupportedFormats.UPC_EAN_EXTENSION,
          ],
          verbose: false
        });
        scannerRef.current = htmlScanner;
        // console.log("Html5Qrcode instance created.");

        // Attempt to start scanning directly after a brief delay
        // to allow the component and browser to stabilize
        if (timeoutIdRef.current) clearTimeout(timeoutIdRef.current);

        // console.log("Setting timeout to call startScanning...", {
        //   timeoutIdRef: timeoutIdRef.current,
        //   isScanningRef
        // });
        timeoutIdRef.current = setTimeout(() => {
          // console.log("Timeout finished, calling startScanning...", {
          //   isScanningRef
          // });
          // Check refs again right before starting, just in case
          if (!isScanningRef.current && !isTransitioningRef.current && scannerRef.current) {
            startScanning();
          } else {
            console.log("Skipping startScanning call due to state:", { isScanning: isScanningRef.current, isTransitioning: isTransitioningRef.current, hasScanner: !!scannerRef.current });
          }
        }, 100);

      } catch (error) {
        console.error("Error initializing Html5Qrcode instance:", error);
        setScannerError("Failed to set up the scanner.");
        return; // Stop if initialization fails
      }

    } else {
      console.error("Scanner container ref is not available.");
      setScannerError("Scanner UI component failed to load.");
    }

    // Cleanup function for unmount
    return () => {
      console.log("BarcodeScanner unmounting, running cleanup...");
      if (timeoutIdRef.current) {
        clearTimeout(timeoutIdRef.current);
        timeoutIdRef.current = null;
      }
      // Stop the scanner stream directly and synchronously if it exists and is scanning
      // Avoid calling the library's .clear() method here, as React will remove the container node
      /* Removed the explicit stop() call to let React handle DOM removal
      if (scannerRef.current && isScanningRef.current) {
        try {
          // Stop is generally synchronous or fast enough for cleanup
          scannerRef.current.stop();
          console.log("Scanner stopped directly during component unmount.");
        } catch (error) {
          console.error("Error stopping scanner directly during unmount:", error);
          // Ignore errors during cleanup as the component is being removed anyway
        }
      }
      */
      // Nullify the ref to help with garbage collection and prevent stale references
      scannerRef.current = null;
      // Reset the initialization flag on cleanup
      hasInitializedRef.current = false;
    };
    // Empty dependency array ensures this runs only on mount and unmount
  }, []);

  return (
    <div className="barcode-scanner">
      {/* Ensure the ID matches the one used in Html5Qrcode constructor */}
      <div
        id="scanner-container"
        ref={containerRef}
        style={{ width: `${width}px`, height: `${height}px`, overflow: 'hidden' }} // Added overflow hidden
        className="mx-auto border border-gray-300 rounded overflow-hidden mb-4 relative bg-gray-100" // Added relative pos and bg
      >
        {/* Placeholder or visual feedback while camera initializes */}
        {!isCameraReady && !scannerError && (
          <div className="absolute inset-0 flex items-center justify-center text-gray-500">
            {isTransitioning ? 'Starting Camera...' : 'Initializing Scanner...'}
          </div>
        )}
      </div>

      <div className="text-center min-h-[40px]"> {/* Added min-height */}
        {(isScanning || isTransitioning) && !scannerError && (
          <div className="flex items-center justify-center text-sm mt-2">
            <span className="loading loading-spinner loading-sm mr-2"></span>
            <span>Scanning for barcodes...</span>
          </div>
        )}

        {scannerError && (
          <div className="alert alert-error mt-2 text-xs p-2"> {/* Smaller text/padding */}
            <span>{scannerError}</span>
          </div>
        )}

        {!isScanning && !isTransitioning && isCameraReady && !scannerError && (
          <div className="text-sm text-gray-500 mt-2">
            Point camera at a barcode.
          </div>
        )}
      </div>
    </div>
  );
};

export default BarcodeScanner; 