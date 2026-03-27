from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentCategory(str, Enum):
    DESIGN = "design"
    ENGINEERING = "engineering"
    QUALITY = "quality"


class ReviewStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISION_NEEDED = "revision_needed"


class Project(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: Optional[str] = None
    brand_context: Dict[str, Any] = Field(default_factory=dict)
    design_system: Dict[str, Any] = Field(default_factory=dict)
    tech_stack: Dict[str, Any] = Field(default_factory=dict)
    status: str = "active"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Task(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    task_type: str
    input_task: str
    execution_plan: List[Dict[str, Any]] = Field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    priority: int = Field(default=5, ge=1, le=10)
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentExecution(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    task_id: UUID
    agent_name: str
    agent_category: AgentCategory
    phase_number: int
    input_context: Dict[str, Any] = Field(default_factory=dict)
    output_text: str
    output_structured: Dict[str, Any] = Field(default_factory=dict)
    tokens_input: int = 0
    tokens_output: int = 0
    execution_time_ms: int = 0
    status: str = "completed"
    error_message: Optional[str] = None


class TaskResult(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    task_id: UUID
    final_output: str
    summary: Optional[str] = None
    deliverables: List[Dict[str, Any]] = Field(default_factory=list)
    review_status: ReviewStatus = ReviewStatus.PENDING
    review_notes: Optional[str] = None


class ExecutionPhase(BaseModel):
    phase: int
    agents: List[str]
    parallel: bool = False


class ExecutionPlan(BaseModel):
    name: str
    description: Optional[str] = None
    task_types: List[str]
    phases: List[ExecutionPhase]
    is_default: bool = False
