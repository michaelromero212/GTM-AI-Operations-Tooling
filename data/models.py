"""
Pydantic data models for GTM AI Operations Hub
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class GTMStage(str, Enum):
    PIPELINE = "Pipeline Generation"
    DEAL = "Deal Execution"
    ONBOARDING = "Onboarding & Adoption"
    RENEWAL = "Renewal & Expansion"


class Complexity(str, Enum):
    QUICK = "Quick Win"
    MEDIUM = "Medium"
    STRATEGIC = "Strategic"


class Approach(str, Enum):
    AGENT = "AI Agent"
    AUTOMATION = "Workflow Automation"
    DATA_FIX = "Data Fix"
    PROCESS = "Process Change"


class BacklogStatus(str, Enum):
    INTAKE = "Intake"
    SCOPING = "Scoping"
    IN_BUILD = "In Build"
    QA = "QA"
    DEPLOYED = "Deployed"
    MEASURING = "Measuring"


class IntakeRequest(BaseModel):
    id: Optional[str] = None
    requester_name: str
    requester_team: str
    pain_point: str
    workflow_stage: str
    manual_time_hours: float
    urgency: str = "Medium"
    created_at: Optional[str] = None
    # Triage results (filled by LLM)
    gtm_stage: Optional[str] = None
    complexity: Optional[str] = None
    approach: Optional[str] = None
    priority_score: Optional[int] = None
    triage_summary: Optional[str] = None
    status: str = "Intake"


class BacklogItem(BaseModel):
    id: str
    request_id: str
    title: str
    requester_name: str
    requester_team: str
    gtm_stage: str
    complexity: str
    approach: str
    priority_score: int
    status: str = "Intake"
    assigned_to: Optional[str] = None
    estimated_time_savings: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class PromptVersion(BaseModel):
    id: str
    request_id: str
    version: int
    prompt_text: str
    response_text: Optional[str] = None
    quality_score: Optional[float] = None
    created_at: Optional[str] = None


class ImpactMetric(BaseModel):
    id: str
    request_id: str
    title: str
    status: str
    manual_time_before: float  # hours per week
    ai_time_after: float  # hours per week
    adoption_rate: float  # percentage
    roi_estimate: float  # dollar value per month
    weeks_deployed: int
    created_at: Optional[str] = None
