from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.models.api import ProjectCreate, ProjectResponse, ProjectUpdate
from app.models.schemas import Project, Agent
from app.models.responses import StandardResponse
from typing import List
import uuid

router = APIRouter(prefix="/projects", tags=["projects"])

@router.get("/", response_model=StandardResponse[List[ProjectResponse]])
async def list_projects(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """List all projects for current user"""
    projects = await db.query(Project).filter(Project.user_id == request.state.user['id']).all()
    return StandardResponse.success_response([
        ProjectResponse.from_orm(project) for project in projects
    ])

@router.get("/{project_id}", response_model=StandardResponse[ProjectResponse])
async def get_project(
    request: Request,
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get project details"""
    project = await db.get(Project, project_id)
    if not project or project.user_id != request.state.user['id']:
        raise HTTPException(status_code=404, detail="Project not found")
    return StandardResponse.success_response(ProjectResponse.from_orm(project))

@router.put("/{project_id}", response_model=StandardResponse[ProjectResponse])
async def update_project(
    request: Request,
    project_id: uuid.UUID,
    project_update: ProjectUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update project"""
    project = await db.get(Project, project_id)
    if not project or project.user_id != request.state.user['id']:
        raise HTTPException(status_code=404, detail="Project not found")
    
    for field, value in project_update.dict(exclude_unset=True).items():
        setattr(project, field, value)
    
    await db.commit()
    await db.refresh(project)
    return StandardResponse.success_response(ProjectResponse.from_orm(project))

@router.delete("/{project_id}")
async def delete_project(
    request: Request,
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete/archive project"""
    project = await db.get(Project, project_id)
    if not project or project.user_id != request.state.user['id']:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project.status = "archived"
    await db.commit()
    return StandardResponse.success_response(message="Project archived successfully")

@router.post("/{project_id}/agent", response_model=StandardResponse[ProjectResponse])
async def assign_agent(
    request: Request,
    project_id: uuid.UUID,
    agent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Assign agent to project"""
    project = await db.get(Project, project_id)
    if not project or project.user_id != request.state.user['id']:
        raise HTTPException(status_code=404, detail="Project not found")
    
    agent = await db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    project.agent_id = agent_id
    await db.commit()
    await db.refresh(project)
    return StandardResponse.success_response(ProjectResponse.from_orm(project))
