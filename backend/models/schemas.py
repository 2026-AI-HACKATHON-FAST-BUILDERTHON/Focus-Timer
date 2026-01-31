from pydantic import BaseModel, EmailStr
from typing import Optional, List, Literal
from datetime import datetime
from enum import Enum


# Enums
class TaskType(str, Enum):
    READING = "reading"
    PRACTICE = "practice"
    CREATION = "creation"
    ROUTINE = "routine"


class SessionStatus(str, Enum):
    COMPLETED = "completed"
    ABORTED = "aborted"


class AbortReason(str, Enum):
    PHONE = "phone"
    TIRED = "tired"
    BORED = "bored"
    ANXIOUS = "anxious"
    ENVIRONMENT = "environment"
    URGENT = "urgent"
    OTHER = "other"


# Request Schemas
class SessionStartRequest(BaseModel):
    task_type: TaskType
    difficulty: int  # 1-5
    goal: Optional[str] = None
    mode_plan: List[dict]  # [{"focus": 25}, {"break": 5}, ...]


class SessionCompleteRequest(BaseModel):
    session_id: str
    total_focus_sec: int
    total_break_sec: int
    rounds_completed: int


class SessionAbortRequest(BaseModel):
    session_id: str
    abort_reason: AbortReason
    abort_detail: Optional[str] = None
    total_focus_sec: int
    rounds_completed: int


class RecommendationRequest(BaseModel):
    task_type: TaskType
    difficulty: int
    hour: int  # 0-23
    day_of_week: int  # 0-6


class PurchaseRequest(BaseModel):
    item_id: str
    qty: int = 1


class CatEquipRequest(BaseModel):
    hat_item_id: Optional[str] = None
    accessory_item_id: Optional[str] = None
    prop_item_id: Optional[str] = None


# Response Schemas
class UserProfile(BaseModel):
    user_id: str
    email: str
    nickname: Optional[str] = None
    coin_balance: int = 0
    created_at: datetime


class SessionResponse(BaseModel):
    id: str
    user_id: str
    task_type: TaskType
    difficulty: int
    goal: Optional[str] = None
    mode_plan: Optional[List[dict]] = None
    status: SessionStatus
    abort_reason: Optional[AbortReason] = None
    total_focus_sec: int = 0
    total_break_sec: int = 0
    rounds_completed: int = 0
    coin_reward: int = 0
    created_at: datetime


class LoopPhase(BaseModel):
    type: Literal["focus", "break"]
    minutes: int


class RecommendationResponse(BaseModel):
    recommended_loop: List[LoopPhase]
    predicted_completion_prob: float
    reason: str
    risk_level: Literal["low", "medium", "high"]
    micro_routine: Optional[str] = None
    persona_type: Optional[str] = None  # AI가 분류한 유저 페르소나


class WeeklyReportResponse(BaseModel):
    total_focus_minutes: int
    total_sessions: int
    completed_sessions: int
    completion_rate: float
    most_common_abort_reason: Optional[str]
    best_focus_hour: Optional[int]
    experiment_suggestion: str
    daily_stats: List[dict]


class ItemResponse(BaseModel):
    id: str
    name: str
    set_name: Optional[str]
    tag: Optional[str]
    price: int
    color: Optional[str]


class InventoryItem(BaseModel):
    item_id: str
    item_name: str
    qty: int


class CatEquipResponse(BaseModel):
    hat_item_id: Optional[str]
    accessory_item_id: Optional[str]
    prop_item_id: Optional[str]
