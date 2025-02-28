import express from 'express';
import cron from 'node-cron';
import { logger } from './utils/logger';
import { memoryPruningJob } from './jobs/memoryPruning';
import { config } from './config';
import { memoryConsolidationJob } from './jobs/memoryConsolidation';
import { cacheCleanupJob } from './jobs/cacheCleanup';
import { memoryStatsJob } from './jobs/memoryStats';

const app = express();

// Register cron jobs
cron.schedule(config.memoryPruningSchedule, async () => {
  try {
    logger.info('Starting memory pruning job');
    await memoryPruningJob();
    logger.info('Memory pruning job completed');
  } catch (error) {
    logger.error('Error in memory pruning job:', error);
  }
});

cron.schedule(config.memoryConsolidationSchedule, async () => {
  try {
    logger.info('Starting memory consolidation job');
    await memoryConsolidationJob();
    logger.info('Memory consolidation completed');
  } catch (error) {
    logger.error('Error in memory consolidation job:', error);
  }
});

cron.schedule(config.cacheCleanupSchedule, async () => {
  try {
    logger.info('Starting cache cleanup job');
    await cacheCleanupJob();
    logger.info('Cache cleanup completed');
  } catch (error) {
    logger.error('Error in cache cleanup job:', error);
  }
});

cron.schedule(config.memoryStatsSchedule, async () => {
  try {
    logger.info('Starting memory stats job');
    await memoryStatsJob();
    logger.info('Memory stats completed');
  } catch (error) {
    logger.error('Error in memory stats job:', error);
  }
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'healthy' });
});

app.listen(config.port, () => {
  logger.info(`Cron service running on port ${config.port}`);
});