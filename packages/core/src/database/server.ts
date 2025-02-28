import { MongoDBAdapter } from './mongodb';

// Singleton instance
let dbInstance: MongoDBAdapter | null = null;

export function getDatabase() {
  if (!dbInstance) {
    dbInstance = new MongoDBAdapter();
  }
  return dbInstance;
}

// Helper function to ensure we're on server side
declare const window: any;

export function isServer() {
  return typeof window === 'undefined';
}