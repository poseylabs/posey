from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, UUID4
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.config import logger, db
from app.middleware.response import standardize_response
from app.config.defaults import LLM_CONFIG
import json;

router = APIRouter(
    prefix="/user",
    tags=["user"]
)

class UserPreferences(BaseModel):
    """User preferences model"""
    llm: Optional[Dict[str, Any]] = None
    image: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class UserPreferencesResponse(BaseModel):
    """Response model for user preferences operations"""
    user_id: UUID4
    preferences: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

# Default preferences that will be merged with user preferences
DEFAULT_USER_PREFERENCES = {
    "llm": {
        "provider": LLM_CONFIG["default"]["provider"],
        "model": LLM_CONFIG["default"]["model"],
        "temperature": 0.7,
        "max_tokens": 1000,
        "top_p": 0.95,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0
    },
    "image": {
        "provider": "openai",
        "model": "dalle-3"
    }
}

@router.get("/{user_id}/preferences", response_model=Dict[str, Any])
@standardize_response
async def get_user_preferences(user_id: UUID4):
    """Retrieve user preferences"""
    try:
        async with db.get_session() as session:
            query = text("""
                SELECT preferences FROM users WHERE id = :user_id
            """)
            result = await session.execute(query, {"user_id": str(user_id)})
            row = result.fetchone()

            if not row:
                logger.info(f"No user preferences found for {user_id}, returning default preferences")
                return DEFAULT_USER_PREFERENCES

            # Merge defaults with stored preferences
            stored_prefs = row[0] if row[0] else {}
            return {
                **DEFAULT_USER_PREFERENCES,
                **stored_prefs
            }

    except Exception as e:
        logger.error(f"Error retrieving user preferences: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve user preferences")

@router.post("/{user_id}/preferences", response_model=Dict[str, Any])
@standardize_response
async def update_user_preferences(
    user_id: UUID4,
    preferences: Dict[str, Any]
):
    """Update user preferences"""
    try:
        async with db.get_session() as session:
            # Get current preferences
            query = text("""
                SELECT preferences FROM users WHERE id = :user_id
            """)
            result = await session.execute(query, {"user_id": str(user_id)})
            row = result.fetchone()

            if not row:
                raise HTTPException(status_code=404, detail="User not found")

            # Merge preferences in correct order: defaults -> existing -> new
            current_prefs = row[0] if row[0] else {}
            merged_preferences = {
                **DEFAULT_USER_PREFERENCES,
                **current_prefs,
                **preferences
            }

            # Update preferences
            update_query = text("""
                UPDATE users 
                SET preferences = :preferences::jsonb,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :user_id
                RETURNING id, preferences, created_at, updated_at
            """)

            result = await session.execute(
                update_query,
                {
                    "user_id": str(user_id),
                    "preferences": json.dumps(merged_preferences)
                }
            )
            await session.commit()

            updated = result.fetchone()
            return {
                "user_id": updated[0],
                "preferences": updated[1],
                "created_at": updated[2],
                "updated_at": updated[3]
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user preferences: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update user preferences: {str(e)}")

@router.get("/", response_model=List[Dict[str, Any]])
@standardize_response
async def list_users(
    status: Optional[str] = Query(None, pattern="^(active|inactive|suspended)$"),
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    """List users with optional filtering"""
    try:
        async with db.get_session() as session:
            query = """
                SELECT * FROM users 
                WHERE 1=1
            """
            params = {}

            if status:
                query += " AND status = :status"
                params["status"] = status

            query += " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
            params.update({"limit": limit, "offset": offset})

            result = await session.execute(text(query), params)
            return result.fetchall()

    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(status_code=500, detail="Failed to list users")

def parse_datetime(date_str: str) -> datetime:
    """Convert ISO datetime string to datetime object"""
    try:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        return None

@router.put("/{user_id}", response_model=Dict[str, Any])
@standardize_response
async def update_user(
    user_id: UUID4,
    user_data: Dict[str, Any]
):
    """Update user data"""
    try:
        logger.info(f"Attempting to update user {user_id} with data: {user_data}")

        async with db.get_session() as session:
            # First check if user exists
            check_query = text("""
                SELECT id FROM users WHERE id = :user_id
            """)
            result = await session.execute(check_query, {"user_id": str(user_id)})
            if not result.fetchone():
                logger.error(f"User {user_id} not found")
                raise HTTPException(status_code=404, detail="User not found")

            # Convert camelCase to snake_case for database columns
            db_fields = {}
            field_mappings = {
                'email': 'email',
                'username': 'username',
                'role': 'role',
                'metadata': 'metadata',
                'lastLogin': 'last_login'  # Add back lastLogin mapping
            }

            # Special handling for datetime fields
            datetime_fields = {'last_login'}

            for key, value in user_data.items():
                if key in field_mappings:
                    db_key = field_mappings[key]
                    # Convert datetime strings for specific fields
                    if db_key in datetime_fields and isinstance(value, str):
                        value = parse_datetime(value)
                    db_fields[db_key] = value
                elif key == 'metadata':
                    db_fields[db_key] = json.dumps(value)
                else:
                    # Convert any other camelCase to snake_case
                    snake_key = ''.join(['_'+c.lower() if c.isupper() else c for c in key]).lstrip('_')
                    db_fields[snake_key] = value

            if not db_fields:
                logger.warning("No valid fields to update")
                raise HTTPException(status_code=400, detail="No valid fields to update")

            # Build the update query
            update_fields = []
            update_values = {"user_id": str(user_id)}

            for key, value in db_fields.items():
                if key not in ['id', 'created_at']:  # Only protect truly immutable fields
                    if value is not None:  # Only include non-None values
                        update_fields.append(f"{key} = :{key}")
                        update_values[key] = value

            update_query = text(f"""
                UPDATE users 
                SET {", ".join(update_fields)},
                    updated_at = NOW()
                WHERE id = :user_id
                RETURNING *
            """)

            logger.info(f"Executing update query: {update_query}")
            logger.info(f"Update values: {update_values}")

            result = await session.execute(update_query, update_values)
            await session.commit()

            updated = result.fetchone()
            if updated:
                logger.info(f"Successfully updated user {user_id}")
                response_data = dict(updated)

                if 'updated_at' in response_data:
                    response_data['updatedAt'] = response_data.pop('updated_at')
                if 'created_at' in response_data:
                    response_data['createdAt'] = response_data.pop('created_at')
                if 'last_login' in response_data:
                    response_data['lastLogin'] = response_data.pop('last_login')
   
                # Convert other snake_case fields to camelCase
                for camel, snake in field_mappings.items():
                    if snake in response_data:
                        response_data[camel] = response_data[snake]
                        response_data.pop(snake)

                if 'email' in user_data or 'username' in user_data:
                    # Only sync if email or username is being changed
                    await sync_to_supertokens(
                        str(user_id), 
                        user_data.get('email'), 
                        user_data.get('username')
                    )

                return response_data
            else:
                logger.error(f"Update succeeded but no row returned for user {user_id}")
                raise HTTPException(status_code=500, detail="Update failed")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update user: {str(e)}")

async def sync_to_supertokens(user_id: str, email: Optional[str] = None, username: Optional[str] = None):
    """Sync user data from application DB to Supertokens"""
    try:
        import httpx
        from app.config import get_settings

        settings = get_settings()
        supertokens_api_url = settings.SUPERTOKENS_API_URL
        api_key = settings.SUPERTOKENS_API_KEY
        
        logger.info(f"Syncing user {user_id} to Supertokens with email={email}, username={username}")
        
        headers = {
            "api-key": api_key,
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            # If email is being updated, call the updateEmail endpoint
            if email:
                email_update_url = f"{supertokens_api_url}/recipe/user/email"
                email_payload = {
                    "userId": user_id,
                    "email": email
                }
                
                logger.info(f"Updating email in Supertokens for user {user_id}: {email}")
                email_response = await client.put(
                    email_update_url, 
                    json=email_payload, 
                    headers=headers
                )
                
                if email_response.status_code != 200:
                    logger.error(f"Failed to update email in Supertokens: {email_response.text}")
                    return False
                
                logger.info(f"Successfully updated email in Supertokens for user {user_id}")
            
            # If username is being updated, update it in UserMetadata
            if username:
                # First get current metadata
                metadata_url = f"{supertokens_api_url}/recipe/user/metadata"
                get_metadata_payload = {
                    "userId": user_id
                }
                
                get_response = await client.get(
                    metadata_url, 
                    params=get_metadata_payload, 
                    headers=headers
                )
                
                if get_response.status_code != 200:
                    logger.error(f"Failed to get metadata from Supertokens: {get_response.text}")
                    return False
                
                # Parse current metadata
                current_metadata = get_response.json().get("metadata", {})
                
                # Update username in metadata
                current_metadata["username"] = username
                
                # Put updated metadata back
                update_metadata_payload = {
                    "userId": user_id,
                    "metadata": current_metadata
                }
                
                logger.info(f"Updating username in Supertokens metadata for user {user_id}: {username}")
                update_response = await client.put(
                    metadata_url, 
                    json=update_metadata_payload, 
                    headers=headers
                )
                
                if update_response.status_code != 200:
                    logger.error(f"Failed to update metadata in Supertokens: {update_response.text}")
                    return False
                
                logger.info(f"Successfully updated username in Supertokens metadata for user {user_id}")
        
        return True
    except Exception as e:
        logger.error(f"Error syncing to Supertokens: {str(e)}")
        return False
