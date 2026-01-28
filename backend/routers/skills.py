"""
Skills Router

API endpoints for skill management and approval.
"""

from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..models import SkillMetadata, ProposedSkill
from ..services.skill_loader import skill_loader
from ..services.learning_engine import learning_engine

router = APIRouter(prefix="/api/skills", tags=["skills"])


class SkillListResponse(BaseModel):
    skills: List[SkillMetadata]
    count: int


class ProposedSkillResponse(BaseModel):
    id: str
    name: str
    description: str
    trigger_pattern: str
    content: str
    source_tickets: List[str]
    status: str


@router.get("/", response_model=SkillListResponse)
async def list_skills():
    """List all available skills"""
    skills = skill_loader.discover_skills()
    return SkillListResponse(skills=skills, count=len(skills))


@router.get("/proposed")
async def list_proposed_skills():
    """List all pending skill proposals"""
    pending = learning_engine.get_pending_skills()
    return {
        "count": len(pending),
        "skills": [
            ProposedSkillResponse(
                id=s.id,
                name=s.name,
                description=s.description,
                trigger_pattern=s.trigger_pattern,
                content=s.content,
                source_tickets=s.source_tickets,
                status=s.status
            ).model_dump()
            for s in pending
        ]
    }


@router.get("/proposed/{skill_id}")
async def get_proposed_skill(skill_id: str):
    """Get details of a specific proposed skill"""
    if skill_id not in learning_engine.proposed_skills:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    skill = learning_engine.proposed_skills[skill_id]
    return ProposedSkillResponse(
        id=skill.id,
        name=skill.name,
        description=skill.description,
        trigger_pattern=skill.trigger_pattern,
        content=skill.content,
        source_tickets=skill.source_tickets,
        status=skill.status
    )


@router.post("/approve/{skill_id}")
async def approve_skill(skill_id: str):
    """Approve a proposed skill"""
    if not learning_engine.approve_skill(skill_id):
        raise HTTPException(status_code=404, detail="Skill not found")
    
    return {"message": f"Skill {skill_id} approved and activated"}


@router.delete("/reject/{skill_id}")
async def reject_skill(skill_id: str):
    """Reject a proposed skill"""
    if not learning_engine.reject_skill(skill_id):
        raise HTTPException(status_code=404, detail="Skill not found")
    
    return {"message": f"Skill {skill_id} rejected and removed"}


@router.get("/{skill_name}/content")
async def get_skill_content(skill_name: str):
    """Get the full content of a skill"""
    content = skill_loader.get_skill_content(skill_name)
    if content is None:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    return {"name": skill_name, "content": content}
