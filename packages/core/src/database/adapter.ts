import { MongoDBAdapter } from './mongodb';

export interface DatabaseAdapter {
  connect(): Promise<void>;
  disconnect(): Promise<void>;
  getDatabase(): any;
}

export {
  MongoDBAdapter
}
