#!/usr/bin/env ts-node
import { exec } from 'child_process';
import { promises as fs } from 'fs';
import { resolve } from 'path';
import { promisify } from 'util';
import readline from 'readline';

const execAsync = promisify(exec);

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

const question = (query: string): Promise<string> => {
  return new Promise(resolve => rl.question(query, resolve));
};

async function updateEnvFile(databaseUrl: string) {
  try {
    // Path to the .env file
    const envPath = resolve(process.cwd(), '.env');

    // Read the current .env file
    const currentEnv = await fs.readFile(envPath, 'utf8');

    // Replace the DATABASE_URL line
    const updatedEnv = currentEnv.replace(
      /^DATABASE_URL=.*$/m,
      `DATABASE_URL="${databaseUrl}"`
    );

    // Write the updated content back to the .env file
    await fs.writeFile(envPath, updatedEnv, 'utf8');

    return true;
  } catch (error) {
    console.error('Error updating .env file:', error);
    return false;
  }
}

async function updateSchemaProvider(provider: string) {
  try {
    const schemaPath = resolve(process.cwd(), 'prisma/schema.prisma');
    const currentSchema = await fs.readFile(schemaPath, 'utf8');

    // Split into lines and process
    const lines = currentSchema.split('\n');
    let inDatasourceBlock = false;
    
    for (let i = 0; i < lines.length; i++) {
      // Check if we're entering the datasource block
      if (lines[i].trim().match(/^datasource\s+db\s+{/)) {
        inDatasourceBlock = true;
        continue;
      }
      
      // Check if we're leaving the datasource block
      if (inDatasourceBlock && lines[i].trim() === '}') {
        inDatasourceBlock = false;
        continue;
      }
      
      // Replace provider in the datasource block
      if (inDatasourceBlock && lines[i].trim().match(/^\s*provider\s*=/)) {
        lines[i] = lines[i].replace(/provider\s*=\s*"[^"]*"/, `provider = "${provider}"`);
      }
    }
    
    // Join lines back and write to file
    await fs.writeFile(schemaPath, lines.join('\n'), 'utf8');
    return true;
  } catch (error) {
    console.error('Error updating schema provider:', error);
    return false;
  }
}

async function ensureCorrectGenerator() {
  try {
    const schemaPath = resolve(process.cwd(), 'prisma/schema.prisma');
    const currentSchema = await fs.readFile(schemaPath, 'utf8');

    // Split into lines and process
    const lines = currentSchema.split('\n');
    let inGeneratorBlock = false;
    
    for (let i = 0; i < lines.length; i++) {
      // Check if we're entering the generator block
      if (lines[i].trim().match(/^generator\s+client\s+{/)) {
        inGeneratorBlock = true;
        continue;
      }
      
      // Check if we're leaving the generator block
      if (inGeneratorBlock && lines[i].trim() === '}') {
        inGeneratorBlock = false;
        continue;
      }
      
      // Make sure generator provider is prisma-client-js
      if (inGeneratorBlock && lines[i].trim().match(/^\s*provider\s*=/)) {
        lines[i] = lines[i].replace(/provider\s*=\s*"[^"]*"/, 'provider = "prisma-client-js"');
      }
    }
    
    // Join lines back and write to file
    await fs.writeFile(schemaPath, lines.join('\n'), 'utf8');
    
    return true;
  } catch (error) {
    console.error('Error updating generator provider:', error);
    return false;
  }
}

async function setupDatabase() {
  console.log('\n🔧 Inventory Database Setup\n');

  // Ask which database to use
  const dbTypeOptions = `
Choose your database:
1. SQLite (default, no server required)
2. PostgreSQL (requires PostgreSQL server)
3. Use existing Posey database (port 3333)
`;

  let databaseProvider = 'sqlite';
  let databaseUrl = 'file:./inventory.db';

  const dbChoice = await question(dbTypeOptions + 'Enter your choice (1-3): ');

  switch (dbChoice.trim()) {
    case '1': // SQLite
      console.log('\n📝 Using SQLite (file-based database)');
      databaseProvider = 'sqlite';
      databaseUrl = 'file:./inventory.db';
      break;

    case '2': // PostgreSQL
      console.log('\n📝 Setting up PostgreSQL connection');
      databaseProvider = 'postgresql';

      const pgHost = await question('Database host (default: localhost): ') || 'localhost';
      const pgPort = await question('Database port (default: 5432): ') || '5432';
      const pgUser = await question('Database user (default: postgres): ') || 'postgres';
      const pgPassword = await question('Database password (default: postgres): ') || 'postgres';
      const pgDb = await question('Database name (default: inventory): ') || 'inventory';

      databaseUrl = `postgresql://${pgUser}:${pgPassword}@${pgHost}:${pgPort}/${pgDb}?schema=public`;
      break;

    case '3': // Posey Database
      console.log('\n📝 Using existing Posey database on port 3333');
      databaseProvider = 'postgresql';
      databaseUrl = 'postgresql://postgres:postgres@localhost:3333/inventory?schema=public';
      break;

    default:
      console.log('\n⚠️ Invalid choice. Using SQLite as default.');
      break;
  }

  // Update schema provider
  console.log('\n🔄 Setting database provider to ' + databaseProvider + '...');
  await updateSchemaProvider(databaseProvider);

  // Ensure generator is correct
  console.log('\n🔄 Ensuring correct Prisma generator...');
  await ensureCorrectGenerator();

  // Update the .env file
  console.log('\n🔄 Updating database connection string...');
  await updateEnvFile(databaseUrl);

  // Generate Prisma client
  console.log('\n🔄 Generating Prisma client...');
  try {
    await execAsync('npx prisma generate');
    console.log('✅ Prisma client generated');
  } catch (error) {
    console.error('❌ Error generating Prisma client:', error);
    console.log('Try generating the client manually with: npx prisma generate');
  }

  // Run database migrations
  console.log('\n🔄 Running database migrations...');
  try {
    await execAsync('npx prisma migrate dev --name init');
    console.log('✅ Database migrations completed');
  } catch (error) {
    console.error('❌ Error running migrations:', error);
    console.log('Try running the migrations manually with: npx prisma migrate dev');
  }

  console.log('\n✅ Database setup complete!');
  console.log(`\nDatabase provider: ${databaseProvider}`);
  console.log(`Connection string: ${databaseUrl}`);
  console.log('\nYou can now start the application with: yarn dev');

  rl.close();
}

// Run the setup
setupDatabase().catch(error => {
  console.error('Error during setup:', error);
  rl.close();
}); 