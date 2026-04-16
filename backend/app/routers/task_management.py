from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.services.task_manager import TaskManager
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Mock functions for now
def get_db():
    return None

def verify_admin_token():
    return {"user_id": "admin", "isAdmin": True}

@router.get("/tasks", response_model=List[Dict[str, Any]])
async def list_tasks(
    status: Optional[str] = None,
    current_user: dict = Depends(verify_admin_token)
):
    """List all tasks, optionally filtered by status"""
    try:
        task_manager = TaskManager()
        tasks = task_manager.list_tasks(status)
        return tasks
    except Exception as e:
        logger.error(f"Error listing tasks: {e}")
        raise HTTPException(status_code=500, detail="Failed to list tasks")

@router.get("/tasks/{task_id}", response_model=Dict[str, Any])
async def get_task(
    task_id: str,
    current_user: dict = Depends(verify_admin_token)
):
    """Get specific task by ID"""
    try:
        task_manager = TaskManager()
        task = task_manager.get_task(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return task
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get task")

@router.post("/tasks", response_model=Dict[str, str])
async def create_task(
    task_data: Dict[str, Any],
    current_user: dict = Depends(verify_admin_token)
):
    """Create a new task"""
    try:
        task_manager = TaskManager()
        task_id = task_manager.create_task(task_data)
        
        return {"task_id": task_id, "message": "Task created successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise HTTPException(status_code=500, detail="Failed to create task")

@router.put("/tasks/{task_id}/status")
async def update_task_status(
    task_id: str,
    status: str,
    notes: str = "",
    current_user: dict = Depends(verify_admin_token)
):
    """Update task status"""
    try:
        task_manager = TaskManager()
        success = task_manager.update_task_status(task_id, status, notes)
        
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return {"message": "Task status updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating task status: {e}")
        raise HTTPException(status_code=500, detail="Failed to update task status")

@router.get("/tasks/next", response_model=Dict[str, Any])
async def get_next_task(
    current_user: dict = Depends(verify_admin_token)
):
    """Get the next task to work on"""
    try:
        task_manager = TaskManager()
        next_task = task_manager.get_next_task()
        
        if not next_task:
            return {"message": "No pending tasks available"}
        
        return next_task
    except Exception as e:
        logger.error(f"Error getting next task: {e}")
        raise HTTPException(status_code=500, detail="Failed to get next task")

@router.post("/tasks/execute/{task_id}")
async def execute_task(
    task_id: str,
    current_user: dict = Depends(verify_admin_token)
):
    """Execute a specific task (placeholder for future AI agent integration)"""
    try:
        task_manager = TaskManager()
        task = task_manager.get_task(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # TODO: Implement actual task execution logic
        # This would integrate with AI agents to execute tasks
        
        return {
            "task_id": task_id,
            "message": "Task execution initiated",
            "status": "executing"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to execute task")