from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class TicketCategory(str, Enum):
    INCIDENT = "Incident"
    PROBLEM = "Problem"
    CHANGE_REQUEST = "Change Request"
    SERVICE_REQUEST = "Service Request"


class TicketPriority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class Ticket(BaseModel):
    """Raw ticket data from upload"""
    id: str
    title: str
    description: str
    created_at: Optional[datetime] = None
    # Actual values (for supervised learning)
    actual_category: Optional[str] = None
    actual_routing: Optional[str] = None
    actual_resolution: Optional[str] = None


class TicketPrediction(BaseModel):
    """Agent's predictions for a ticket"""
    ticket_id: str
    predicted_category: str
    predicted_routing: str
    predicted_resolution: str
    confidence_scores: dict = Field(default_factory=dict)
    skill_used: Optional[str] = None


class ProcessingResult(BaseModel):
    """Result of processing a single ticket"""
    ticket: Ticket
    prediction: TicketPrediction
    category_correct: Optional[bool] = None
    routing_correct: Optional[bool] = None
    resolution_correct: Optional[bool] = None


class SkillMetadata(BaseModel):
    """Metadata from SKILL.md frontmatter"""
    name: str
    description: str
    file_path: str
    is_approved: bool = True


class ProposedSkill(BaseModel):
    """A skill proposed by the learning engine"""
    id: str
    name: str
    description: str
    trigger_pattern: str
    content: str  # Full SKILL.md content
    created_at: datetime = Field(default_factory=datetime.utcnow)
    source_tickets: List[str] = Field(default_factory=list)
    status: str = "pending"  # pending, approved, rejected


class ProcessingRun(BaseModel):
    """A batch processing run"""
    id: str
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    total_tickets: int = 0
    processed_tickets: int = 0
    correct_predictions: int = 0
    results: List[ProcessingResult] = Field(default_factory=list)
    proposed_skills: List[str] = Field(default_factory=list)
