import asyncpg
from app.config import settings
from app.config import logger

async def seed_test_data(conn: asyncpg.Connection) -> bool:
    """Seed test data for development environment"""
    try:
        async with conn.transaction():
            # Add test user
            await conn.execute("""
                INSERT INTO users (email, name)
                VALUES ('test@posey.ai', 'Test User')
                ON CONFLICT DO NOTHING
            """)
            
            # Add test project
            await conn.execute("""
                INSERT INTO projects (title, description, user_id)
                VALUES ('Test Project', 'A test project', (SELECT id FROM users WHERE email = 'test@posey.ai'))
                ON CONFLICT DO NOTHING
            """)
            
        return True
    except Exception as e:
        logger.error(f"Test data seeding failed: {str(e)}")
        raise

async def seed_database(conn: asyncpg.Connection) -> bool:
    """Seed database with initial data"""
    try:
         # Add environment-specific seeding
        if settings.ENVIRONMENT == "development":
            await seed_test_data(conn)
        
        # Add version tracking for seeds
        await conn.execute("""
            INSERT INTO seed_versions (version, name)
            VALUES ($1, $2)
        """, "1.0", "initial_seed")

        # Start transaction
        async with conn.transaction():
            # Add system tags
            await conn.execute("""
                INSERT INTO system_tags (name, description, category)
                VALUES 
                    ('research', 'Research-related content', 'purpose'),
                    ('task', 'Action items and todos', 'purpose')
                ON CONFLICT DO NOTHING
            """)
            
            # Add default LLM providers
            await conn.execute("""
                INSERT INTO llm_providers (name, base_url)
                VALUES 
                    ('anthropic', 'https://api.anthropic.com'),
                    ('openai', 'https://api.openai.com'),
                    ('ollama', 'http://localhost:11434')
                ON CONFLICT DO NOTHING
            """)
            
        return True
    except Exception as e:
        logger.error(f"Database seeding failed: {str(e)}")
        raise 
