import dotenv from 'dotenv';
import { QdrantClient } from '@qdrant/js-client-rest';

dotenv.config();

const VECTOR_SIZE = 1024;

async function validateCollection(client, collectionName) {
  try {
    const info = await client.getCollection(collectionName);
    console.info(`Validating collection ${collectionName}:`, info);
    
    // Verify the collection configuration
    if (info.config.params.vectors.size !== VECTOR_SIZE) {
      throw new Error(`Collection ${collectionName} has wrong vector size`);
    }
    
    // Test basic operations
    await client.scroll(collectionName, {
      limit: 1,
      with_payload: true,
      with_vectors: false,
    });
    
    return true;
  } catch (error) {
    console.error(`Validation failed for ${collectionName}:`, error);
    return false;
  }
}

// async function healthCheck() {
//   try {
//     console.info('Checking Qdrant health...');
//     const client = new QdrantClient({ url: QDRANT_URL });
    
//     // Get collections to verify connectivity
//     const collections = await client.getCollections();
//     console.info('Collections:', collections);
    
//     return true;
//   } catch (error) {
//     console.error('Health check failed:', error);
//     return false;
//   }
// }

async function initializeCollections() {
  const client = new QdrantClient({ 
    url: 'http://localhost:1111',
    timeout: 10000 // 10 second timeout
  });

  const collections = [
    'agent_memories',
    'conversation_threads',
    'users',
    'user_actions',
    'knowledge_base',          // For storing general knowledge and documentation
    'agent_abilities',         // Store vector representations of agent capabilities
    'user_preferences',        // User-specific settings and preferences
    'interaction_patterns',    // Common interaction patterns for learning
    'feedback_data',          // User feedback and corrections
    'context_windows',        // Active context for ongoing conversations
    'semantic_search_cache',  // Cache frequently searched concepts
    'agent_workflows',        // Common sequences of agent interactions
    'error_patterns'          // Store error cases for improvement
  ];

  console.info('Initializing collections...');

  for (const collection of collections) {
    try {
      console.info(`\nProcessing collection: ${collection}`);
      
      // Check if collection exists
      const exists = await client.getCollection(collection)
        .then(() => true)
        .catch(() => false);

      if (!exists) {
        console.info(`Creating collection: ${collection}`);
        await client.createCollection(collection, {
          vectors: {
            size: VECTOR_SIZE,
            distance: 'Cosine'
          },
          optimizers_config: {
            default_segment_number: 2
          },
          replication_factor: 1
        });
        
        // Wait a bit for collection to be ready
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Validate the new collection
        const isValid = await validateCollection(client, collection);
        if (!isValid) {
          throw new Error(`Failed to validate newly created collection ${collection}`);
        }
        console.info(`Collection ${collection} created and validated successfully`);
      } else {
        console.info(`Collection ${collection} exists, validating...`);
        const isValid = await validateCollection(client, collection);
        if (!isValid) {
          console.info(`Recreating invalid collection ${collection}`);
          await client.deleteCollection(collection);
          await client.createCollection(collection, {
            vectors: {
              size: VECTOR_SIZE,
              distance: 'Cosine'
            }
          });
          const revalidate = await validateCollection(client, collection);
          if (!revalidate) {
            throw new Error(`Failed to recreate collection ${collection}`);
          }
        }
      }
    } catch (error) {
      console.error(`Error handling collection ${collection}:`, error);
      process.exit(1);
    }
  }

  // Final validation of all collections
  console.info('\nFinal validation of all collections:');
  const collectionList = await client.getCollections();
  console.info('Available collections:', collectionList);
}

initializeCollections().catch(error => {
  console.error('Initialization failed:', error);
  process.exit(1);
});
