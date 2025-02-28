from typing import List
from app.models.schemas import Task
from datetime import datetime

def calculate_success_rate(tasks: List[Task]) -> float:
    """Calculate success rate of completed tasks"""
    if not tasks:
        return 0.0
    completed = len([t for t in tasks if t.status == "completed"])
    return (completed / len(tasks)) * 100

def calculate_avg_completion_time(tasks: List[Task]) -> float:
    """Calculate average completion time in hours"""
    completed_tasks = [t for t in tasks if t.status == "completed" and t.completed_at]
    if not completed_tasks:
        return 0.0
    
    total_hours = sum(
        (t.completed_at - t.created_at).total_seconds() / 3600 
        for t in completed_tasks
    )
    return total_hours / len(completed_tasks)

def generate_markdown(conversation, messages) -> str:
    """Generate markdown format for conversation export"""
    md = f"# {conversation.title}\n\n"
    md += f"Created: {conversation.created_at}\n\n"
    
    for msg in messages:
        md += f"## {msg.sender_user.name} ({msg.created_at})\n"
        md += f"{msg.content}\n\n"
    
    return md 
