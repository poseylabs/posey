import axios from 'axios';
import { logger } from '../utils/logger';
import { config } from '../config';

export async function memoryPruningJob() {
  try {
    // Call agents service to prune expired memories
    const response = await axios.post(
      `${config.agentsServiceUrl}/memory/prune`,
      {
        pruneConfig: {
          checkExpired: true,
          consolidateThreshold: config.memoryConsolidationThreshold,
          maxAge: config.maxMemoryAge,
          excludeCategories: ['core', 'first_interaction']
        }
      }
    );

    logger.info(`Memory pruning completed: ${JSON.stringify(response.data)}`);
    return response.data;
  } catch (error) {
    logger.error('Error in memory pruning job:', error);
    throw error;
  }
}
