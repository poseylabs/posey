import express from 'express';
// import cron from 'node-cron';
import { logger } from './utils/logger';
import { config } from './config';

const app = express();

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'healthy' });
});

app.listen(config.port, () => {
  logger.info(`Cron service running on port ${config.port}`);
});