import dotenv from 'dotenv';

dotenv.config();

export const config = {
  port: parseInt(process.env.CRON_PORT || '2222', 10),
  agentsServiceUrl: process.env.AGENTS_SERVICE_URL || 'http://localhost:3000',
  memoryPruningSchedule: process.env.MEMORY_PRUNING_SCHEDULE || '0 0 * * *', // Daily at midnight
  memoryConsolidationSchedule: process.env.MEMORY_CONSOLIDATION_SCHEDULE || '0 4 * * *', // Daily at 4 AM
  cacheCleanupSchedule: process.env.CACHE_CLEANUP_SCHEDULE || '0 */6 * * *', // Every 6 hours
  memoryStatsSchedule: process.env.MEMORY_STATS_SCHEDULE || '0 1 * * *', // Daily at 1 AM
  memoryConsolidationThreshold: 5,
  maxMemoryAge: 90,
  memoryCacheTTL: 30000, // 30 seconds, matching Memory class
};
