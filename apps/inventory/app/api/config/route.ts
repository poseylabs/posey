import { NextRequest } from 'next/server';
import { writeFile, readFile } from 'fs/promises';
import { resolve } from 'path';
import { successResponse, errorResponse } from '@/lib/utils';

// Function to update the .env file with new configuration
async function updateEnvFile(databaseUrl: string) {
  try {
    // Path to the .env file
    const envPath = resolve(process.cwd(), '.env');

    // Read the current .env file
    const currentEnv = await readFile(envPath, 'utf8');

    // Replace the DATABASE_URL line
    const updatedEnv = currentEnv.replace(
      /^DATABASE_URL=.*$/m,
      `DATABASE_URL="${databaseUrl}"`
    );

    // Write the updated content back to the .env file
    await writeFile(envPath, updatedEnv, 'utf8');

    return true;
  } catch (error) {
    console.error('Error updating .env file:', error);
    return false;
  }
}

// Function to update the schema provider
async function updateSchemaProvider(provider: string) {
  try {
    const schemaPath = resolve(process.cwd(), 'prisma/schema.prisma');

    // Read the current schema
    const currentSchema = await readFile(schemaPath, 'utf8');

    // Replace the provider
    const updatedSchema = currentSchema.replace(
      /provider = ".*"/,
      `provider = "${provider}"`
    );

    // Write the updated schema back
    await writeFile(schemaPath, updatedSchema, 'utf8');

    return true;
  } catch (error) {
    console.error('Error updating schema provider:', error);
    return false;
  }
}

// Function to read the current configuration from the .env file
async function readEnvFile() {
  try {
    // Path to the .env file
    const envPath = resolve(process.cwd(), '.env');

    // Read the current .env file
    const envContent = await readFile(envPath, 'utf8');

    // Extract the DATABASE_URL value
    const urlMatch = envContent.match(/^DATABASE_URL=["']?([^"'\n]+)["']?/m);
    const databaseUrl = urlMatch ? urlMatch[1] : 'file:./inventory.db';

    // Determine database provider from URL
    const databaseProvider = databaseUrl.startsWith('file:')
      ? 'sqlite'
      : databaseUrl.includes('postgresql')
        ? 'postgresql'
        : 'sqlite';

    return {
      databaseProvider,
      databaseUrl,
    };
  } catch (error) {
    console.error('Error reading .env file:', error);
    return {
      databaseProvider: 'sqlite',
      databaseUrl: 'file:./inventory.db',
    };
  }
}

// GET /api/config - Get current configuration
export async function GET() {
  try {
    const config = await readEnvFile();
    return successResponse(config);
  } catch (error) {
    console.error('Error getting configuration:', error);
    return errorResponse('Failed to get configuration');
  }
}

// POST /api/config - Update configuration
export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { databaseProvider, databaseUrl } = body;

    // Validate inputs
    if (!databaseProvider || !databaseUrl) {
      return errorResponse('Database provider and URL are required');
    }

    // Update the schema provider
    const schemaSuccess = await updateSchemaProvider(databaseProvider);

    // Update the .env file
    const envSuccess = await updateEnvFile(databaseUrl);

    if (schemaSuccess && envSuccess) {
      return successResponse({
        message: 'Configuration updated successfully',
        restartRequired: true
      });
    } else {
      return errorResponse('Failed to update configuration');
    }
  } catch (error) {
    console.error('Error updating configuration:', error);
    return errorResponse('Failed to update configuration');
  }
} 