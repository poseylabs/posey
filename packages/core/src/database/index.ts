// Create a browser-safe version that doesn't try to import Node.js modules
// In the browser, we'll use API calls instead of direct database access

// Browser-compatible mock implementation
const mockGetDatabase = () => {
  console.warn('Direct database access is not available in browser environment');
  return null;
};

// Export an appropriate implementation based on environment
// This approach avoids runtime errors when importing in the browser
export const getDatabase = mockGetDatabase;