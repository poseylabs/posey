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
  const [cameraId, setCameraId] = useState('');
  const [cameras, setCameras] = useState<{ id: string; label: string }[]>([]);

  useEffect(() => {
    // Initialize scanner
    if (containerRef.current) {
      const htmlScanner = new Html5Qrcode('scanner-container');
      scannerRef.current = htmlScanner;

      // Get available cameras
      Html5Qrcode.getCameras()
        .then((devices) => {
          if (devices && devices.length) {
            setCameras(
              devices.map((device) => ({
                id: device.id,
                label: device.label || `Camera ${device.id}`,
              }))
            );
            // Set first camera as default
            setCameraId(devices[0].id);
          }
        })
        .catch((err) => {
          console.error('Error getting cameras', err);
        });
    }

    return () => {
      // Clean up scanner on unmount
      if (scannerRef.current && isScanning) {
        scannerRef.current
          .stop()
          .then(() => {
            console.log('Scanner stopped');
          })
          .catch((err) => {
            console.error('Error stopping scanner:', err);
          });
      }
    };
  }, []);

  const startScanning = async () => {
    if (!scannerRef.current || !cameraId) return;

    try {
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
        onScanSuccess,
        onScanFailure
      );
    } catch (err) {
      console.error('Error starting scanner:', err);
      setIsScanning(false);
    }
  };

  const stopScanning = async () => {
    if (!scannerRef.current || !isScanning) return;

    try {
      await scannerRef.current.stop();
      setIsScanning(false);
    } catch (err) {
      console.error('Error stopping scanner:', err);
    }
  };

  const handleCameraChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    if (isScanning) {
      stopScanning().then(() => {
        setCameraId(e.target.value);
      });
    } else {
      setCameraId(e.target.value);
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

      <div className="flex flex-col gap-3 mt-3">
        {cameras.length > 0 && (
          <div className="form-control">
            <label className="label">
              <span className="label-text">Camera</span>
            </label>
            <select
              className="select select-bordered w-full"
              value={cameraId}
              onChange={handleCameraChange}
              disabled={isScanning}
            >
              {cameras.map((camera) => (
                <option key={camera.id} value={camera.id}>
                  {camera.label}
                </option>
              ))}
            </select>
          </div>
        )}

        <div className="flex justify-center gap-2">
          {!isScanning ? (
            <button 
              className="btn btn-primary" 
              onClick={startScanning}
              disabled={!cameraId}
            >
              Start Scanning
            </button>
          ) : (
            <button 
              className="btn btn-error" 
              onClick={stopScanning}
            >
              Stop Scanning
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default BarcodeScanner; 