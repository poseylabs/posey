// This file helps Node.js load TypeScript files in ES modules mode
import pkg from 'pg';
const { Pool } = pkg;

// Initialize database connection pools
let _poseyPool: pkg.Pool | null = null;

// Export a function that gets or initializes the pool
export function getPool(): pkg.Pool {
    if (!_poseyPool) {
        console.log('Initializing Posey database connection pool', { dsn: process.env.POSTGRES_DSN_POSEY });

        // Check if DSN is available
        if (!process.env.POSTGRES_DSN_POSEY) {
            throw new Error('POSTGRES_DSN_POSEY environment variable is not set');
        }

        _poseyPool = new Pool({
            connectionString: process.env.POSTGRES_DSN_POSEY,
        });
    }

    return _poseyPool;
}

// Validate database connection
export async function validateDatabaseConnection(): Promise<void> {
    try {
        const pool = getPool();
        await pool.query('SELECT 1');
        console.log('Database connection validated successfully');
    } catch (error) {
        console.error('Error validating database connection:', error);
        throw error;
    }
}

// Export a poseyPool object with the same interface as Pool
export const poseyPool = {
    get pool() {
        return getPool();
    },
    // Properly type the query method to match pg Pool's query method
    query: async (text: string, params?: any[]) => {
        return getPool().query(text, params);
    }
}; 