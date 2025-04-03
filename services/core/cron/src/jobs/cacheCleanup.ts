import axios from 'axios';
import { logger } from '../utils/logger';
import { config } from '../config';

export async function cacheCleanupJob() {
  try {
    const response = await axios.post(
      `${config.agentsServiceUrl}/memory/cache/cleanup`,
      {
        cleanupConfig: {
          maxAge: config.memoryCacheTTL,
          clearAll: false
        }
      }
    );

    logger.info(`Cache cleanup completed: ${JSON.stringify(response.data)}`);
    return response.data;
  } catch (error) {
    logger.error('Error in cache cleanup job:', error);
    throw error;
  }
}
