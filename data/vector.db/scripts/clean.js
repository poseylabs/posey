import dotenv from 'dotenv';
import { QdrantClient } from '@qdrant/js-client-rest';

dotenv.config();

const QDRANT_URL = process.env.QDRANT_URL || 'http://localhost:1111';

async function cleanDatabase() {

  console.info('Cleaning vector database...');

  try {
    const client = new QdrantClient({ url: QDRANT_URL });

    // Get all collections
    const collections = await client.getCollections();

    // Delete each collection
    for (const collection of collections.collections) {
      await client.deleteCollection(collection.name);
    }

    console.info('Vector database cleaned.');

  } catch (error) {
    console.error('Error cleaning vector database:', error);
    process.exit(1);
  }
}

cleanDatabase();
