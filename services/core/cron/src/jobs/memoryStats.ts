import axios from 'axios';
import { logger } from '../utils/logger';
import { config } from '../config';

export async function memoryStatsJob() {
  try {
    const response = await axios.post(
      `${config.agentsServiceUrl}/memory/stats/generate`,
      {
        statsConfig: {
          calculateRecurrencePatterns: true,
          generateCategoryDistribution: true,
          identifyTopMemories: true,
          timeRange: 'last_30_days'
        }
      }
    );

    logger.info(`Memory stats generated: ${JSON.stringify(response.data)}`);
    return response.data;
  } catch (error) {
    logger.error('Error in memory stats job:', error);
    throw error;
  }
}
