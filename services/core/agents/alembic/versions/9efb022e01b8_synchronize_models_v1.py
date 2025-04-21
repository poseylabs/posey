"""synchronize models v1

Revision ID: 9efb022e01b8
Revises: 
Create Date: 2025-04-15 17:49:16.645372

"""
import os
from typing import Sequence, Union
import warnings

from alembic import op
import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision: str = '9efb022e01b8'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Path to the SQL migration files relative to this script
MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), '../../app/db/migrations')

# Sequence of SQL files to execute for this migration
# These should represent the complete schema setup required by the models
# referenced by Alembic revision 9efb022e01b8.
SQL_FILES = [
    '000_init_schema.sql',
    '001_users.sql',
    '002_auth_fields.sql',
    '003_llm.sql',
    '004_agents.sql',
    '005_conversations.sql',
    '006_projects.sql',
    '007_background_tasks.sql',
    '008_research.sql',
    '009_invite_codes.sql',
    '010_memory.sql',
    '011_favorites.sql',
    '012_feedback_tables.sql',
    '013_research_relations.sql',
    '014_integration_tables.sql',
    '015_calendar.sql',
    '016_files.sql',
    '017_integrations.sql',
    '018_agent_capabilities.sql',
    '019_agent_updates.sql',
    '020_conversation_updates.sql',
    '021_creative_agent.sql',
    '022_media_history.sql',
    '023_project_conversations.sql',
    '024_user_preferences.sql',
    '025_minion_configs.sql',
    '026_managed_minions.sql'
]

def execute_sql_file(filename: str):
    """Reads and executes a SQL file."""
    filepath = os.path.join(MIGRATIONS_DIR, filename)
    print(f"Attempting to read SQL file: {os.path.abspath(filepath)}")
    
    if not os.path.exists(filepath):
        print(f"WARNING: SQL file not found: {filepath}")
        return
        
    with open(filepath, 'r') as f:
        sql_content = f.read()
        # Execute the entire file content as a single block
        # Do not split by semicolon, as it breaks DO blocks
        if sql_content.strip(): # Ensure content exists
            print(f"Executing SQL content from {filename} ({len(sql_content)} bytes)")
            try:
                op.execute(sql_content)
                print(f"SQL execution complete for {filename}")
            except Exception as e:
                # Just continue with the next file
                print(f"WARNING: Error executing {filename}: {str(e)}")
                print(f"Continuing with next SQL file...")
        else:
            print(f"WARNING: Empty SQL content in {filename}")

def upgrade():
    """
    Upgrade the database using predefined SQL files.
    This function executes SQL migration files in order.
    Each SQL file is executed in its own transaction to isolate errors.
    """
    # Get migration files directory
    migrations_dir = os.path.join(os.path.dirname(__file__), '../../app/db/migrations')
    print(f"Migration files directory: {migrations_dir}")
    print(f"Directory exists: {os.path.exists(migrations_dir)}")
    
    # List all files found in migrations directory
    files_in_dir = os.listdir(migrations_dir) if os.path.exists(migrations_dir) else []
    print(f"Files found in migrations directory: {files_in_dir}")
    
    # Get the database URL from the current connection
    conn = op.get_bind()
    engine_url = str(conn.engine.url)
    
    # Execute each SQL file in its own connection/transaction
    for sql_file in SQL_FILES:
        file_path = os.path.join(migrations_dir, sql_file)
        print(f"  - Processing {sql_file}...")
        
        try:
            # Read SQL file
            if not os.path.exists(file_path):
                warnings.warn(f"SQL file not found: {file_path}")
                print(f"WARNING: SQL file not found: {file_path}")
                continue
                
            with open(file_path, 'r') as f:
                sql_content = f.read()
                
            if not sql_content.strip():
                warnings.warn(f"SQL file is empty: {file_path}")
                print(f"WARNING: SQL file is empty: {file_path}")
                continue
                
            print(f"Executing SQL content from {sql_file} ({len(sql_content)} bytes)")
            
            # Create a new engine and connection for this SQL file
            with create_engine(engine_url).connect() as separate_conn:
                # Set AUTOCOMMIT for this connection
                separate_conn = separate_conn.execution_options(isolation_level="AUTOCOMMIT")
                
                # Execute SQL commands
                separate_conn.execute(text(sql_content))
                print(f"  - Successfully executed {sql_file}")
            
        except Exception as e:
            print(f"WARNING: Error executing {sql_file}: {e}")
            print(f"  - Continuing to next file...")
    
    print("Finished executing upgrade SQL files.")

def downgrade() -> None:
    """Downgrade schema.
    NOTE: A simple downgrade path is provided, but executing DROP statements 
    based on the upgrade SQL files might be complex and require specific
    downgrade SQL scripts or more sophisticated logic.
    """
    # ### commands auto generated by Alembic - please adjust! ###
    # This is a placeholder downgrade. A real downgrade would need 
    # corresponding DROP statements or separate downgrade SQL files.
    print("Starting downgrade (placeholder - drops may need manual adjustment or specific downgrade scripts)")
    
    # Attempt to drop types created in the first SQL file (reverse order)
    # This is brittle and assumes the types exist.
    enum_types = [
        'content_type', 'file_relationship_type', 'file_source', 'task_status', 
        'task_priority', 'user_task_status', 'research_status', 'project_focus', 
        'user_role', 'project_status', 'sender_type', 'message_role', 'run_status', 
        'tool_status', 'tool_category', 'event_recurrence', 'agent_status', 'agent_type'
    ]
    for enum_name in enum_types:
        try:
            print(f"  - Dropping ENUM TYPE {enum_name}...")
            op.execute(f"DROP TYPE IF EXISTS {enum_name} CASCADE") # Use CASCADE carefully
            print(f"  - Finished dropping {enum_name}.")
        except Exception as e:
            print(f"  - Warning: Failed to drop type {enum_name}. It might not exist or have dependencies. Error: {e}")

    # A full downgrade would need to drop tables, columns, constraints, etc.
    # added in the upgrade sequence, potentially by executing downgrade SQL files.
    print("Finished downgrade (placeholder).")
    # op.drop_constraint('users_username_key', 'users', type_='unique')
    # ... (many more drop statements would be needed here)
    # ### end Alembic commands ###
