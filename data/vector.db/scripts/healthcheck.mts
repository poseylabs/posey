import dotenv from 'dotenv';
import { QdrantClient } from '@qdrant/js-client-rest';

dotenv.config();

const QDRANT_URL = process.env.QDRANT_URL || 'http://localhost:1111';

async function healthCheck() {
  try {
    const client = new QdrantClient({ url: QDRANT_URL });
    const collections = await client.getCollections();
    return {
      status: 'healthy',
      collections: collections.collections
    };
  } catch (error) {
    console.error('Health check failed:', error);
    return {
      status: 'unhealthy',
      error: error
    };
  }
}

if (process.argv[1] === import.meta.url) {
  healthCheck().then(isHealthy => {
    process.exit(isHealthy ? 0 : 1);
  });
}

export { healthCheck };