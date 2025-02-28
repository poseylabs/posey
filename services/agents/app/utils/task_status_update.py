"""
Utility functions for sending task status updates via WebSocket
"""
from typing import Optional, Dict, Any
from datetime import datetime
from app.config import logger

async def send_task_status_update(
    task_id: str,
    status: str,
    progress: Optional[int] = None,
    message: Optional[str] = None,
    result: Optional[Dict[str, Any]] = None
) -> None:
    """Send a status update for a task via WebSocket"""
    try:
        update_data = {
            "task_id": task_id,
            "status": status,
            "progress": progress,
            "message": message,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Remove None values
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
    except Exception as e:
        logger.error(f"Error sending status update for task {task_id}: {e}")
        # Don't raise the exception - status updates should not break the main flow 
