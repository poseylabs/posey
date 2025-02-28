import { MongoDBAdapter } from '../database/mongodb';

async function setupDatabase() {
  
  const adapter = new MongoDBAdapter();
  try {
    await adapter.connect();
    const db = adapter.getDatabase();

    await db.createCollection('personas');
    await db.createCollection('memories');

  } catch (error) {
    console.error('Failed to set up database:', error);
  } finally {
    await adapter.disconnect();
  }
}

setupDatabase();