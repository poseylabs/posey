from typing import Dict, List
from app.config import postgres_client

async def get_all_conversations():
    query = """
        SELECT * FROM conversations 
        ORDER BY (messages->-1->>'timestamp')::timestamp DESC
    """
    return await postgres_client.fetch(query)

async def save_conversation(conversation: Dict):
    query = """
        INSERT INTO conversations (id, messages)
        VALUES ($1, $2)
        RETURNING *
    """
    return await postgres_client.fetchrow(
        query, 
        conversation['id'], 
        conversation['messages']
    )

async def save_message(message: Dict):
    query = """
        UPDATE conversations 
        SET messages = messages || $1
        WHERE id = $2
        RETURNING *
    """
    return await postgres_client.fetchrow(
        query,
        [message],
        message['conversation_id']
    )

async def update_conversation(conversation_id: str, updates: Dict):
    query = """
        UPDATE conversations
        SET messages = $1
        WHERE id = $2
        RETURNING *
    """
    return await postgres_client.fetchrow(
        query,
        updates['messages'],
        conversation_id
    )
