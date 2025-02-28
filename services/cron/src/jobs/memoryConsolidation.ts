import axios from 'axios';
import { logger } from '../utils/logger';
import { config } from '../config';

export async function memoryConsolidationJob() {
  try {
    const response = await axios.post(
      `${config.agentsServiceUrl}/memory/consolidate`,
      {
        consolidationConfig: {
          similarityThreshold: 0.85,
          minRecurrence: 3,
          timeWindowDays: 30,
          categories: ['preferences', 'facts', 'experiences'],
          excludeCategories: ['core', 'first_interaction']
        }
      }
    );

    logger.info(`Memory consolidation completed: ${JSON.stringify(response.data)}`);
    return response.data;
  } catch (error) {
    logger.error('Error in memory consolidation job:', error);
    throw error;
  }
}
