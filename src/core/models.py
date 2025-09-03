"""
Data models and type definitions for the N8N Workflow Documentation System.

This module contains all Pydantic models, dataclasses, and enums used throughout
the application for type safety and data validation.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class TriggerType(Enum):
    """Workflow trigger types with standardized values."""
    
    MANUAL = "Manual"
    WEBHOOK = "Webhook"
    SCHEDULED = "Scheduled"
    COMPLEX = "Complex"
    
    def __str__(self) -> str:
        return self.value


class ComplexityLevel(Enum):
    """Workflow complexity levels based on node count."""
    
    LOW = "low"      # ≤5 nodes
    MEDIUM = "medium"  # 6-15 nodes
    HIGH = "high"    # 16+ nodes
    
    @classmethod
    def from_node_count(cls, node_count: int) -> 'ComplexityLevel':
        """Determine complexity level from node count."""
        if node_count <= 5:
            return cls.LOW
        elif node_count <= 15:
            return cls.MEDIUM
        else:
            return cls.HIGH
    
    def __str__(self) -> str:
        return self.value


@dataclass
class WorkflowMetadata:
    """
    Complete metadata for a workflow including analysis results.
    
    This dataclass provides a strongly-typed representation of workflow
    data with proper validation and type hints.
    """
    
    filename: str
    name: str
    workflow_id: str
    active: bool
    node_count: int
    trigger_type: TriggerType
    complexity: ComplexityLevel
    integrations: List[str]
    description: str
    file_hash: str
    file_size: int
    analyzed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    tags: List[str] = None
    category: Optional[str] = None
    
    def __post_init__(self) -> None:
        """Post-initialization processing."""
        if self.tags is None:
            self.tags = []
        
        # Ensure complexity matches node count
        expected_complexity = ComplexityLevel.from_node_count(self.node_count)
        if self.complexity != expected_complexity:
            self.complexity = expected_complexity


# Pydantic models for API requests/responses
class WorkflowSummary(BaseModel):
    """Workflow summary for API responses."""
    
    id: Optional[int] = None
    filename: str = Field(..., min_length=1, description="Workflow filename")
    name: str = Field(..., min_length=1, description="Display name") 
    active: bool = Field(default=False, description="Whether workflow is active")
    description: str = Field(default="", description="Workflow description")
    trigger_type: str = Field(default="Manual", description="Trigger type")
    complexity: str = Field(default="low", description="Complexity level")
    node_count: int = Field(ge=0, description="Number of nodes")
    integrations: List[str] = Field(default_factory=list, description="Integration list")
    tags: List[str] = Field(default_factory=list, description="Workflow tags")
    category: Optional[str] = Field(None, description="Workflow category")
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    class Config:
        """Pydantic configuration."""
        validate_assignment = True
        str_strip_whitespace = True
        
    @field_validator('active', mode='before')
    @classmethod
    def convert_active(cls, v: Any) -> bool:
        """Convert various types to boolean for active field."""
        if isinstance(v, int):
            return bool(v)
        if isinstance(v, str):
            return v.lower() in ('true', '1', 'yes', 'on')
        return bool(v)
    
    @field_validator('integrations', 'tags', mode='before')
    @classmethod
    def ensure_list(cls, v: Any) -> List[str]:
        """Ensure fields are always lists."""
        if isinstance(v, str):
            return [v] if v else []
        if v is None:
            return []
        if isinstance(v, (list, tuple)):
            return list(v)
        return [str(v)]


class SearchRequest(BaseModel):
    """Search request parameters with validation."""
    
    query: str = Field(default="", max_length=500, description="Search query")
    trigger: str = Field(default="all", description="Trigger type filter")
    complexity: str = Field(default="all", description="Complexity filter")
    category: str = Field(default="all", description="Category filter")
    active_only: bool = Field(default=False, description="Show only active workflows")
    page: int = Field(default=1, ge=1, description="Page number")
    per_page: int = Field(default=20, ge=1, le=100, description="Items per page")
    
    class Config:
        """Pydantic configuration."""
        str_strip_whitespace = True


class SearchResponse(BaseModel):
    """Search response with pagination metadata."""
    
    workflows: List[WorkflowSummary]
    total: int = Field(ge=0, description="Total number of results")
    page: int = Field(ge=1, description="Current page number")
    per_page: int = Field(ge=1, description="Items per page")
    pages: int = Field(ge=1, description="Total number of pages")
    query: str = Field(description="Search query used")
    filters: Dict[str, Any] = Field(description="Filters applied")
    execution_time_ms: Optional[float] = Field(None, description="Query execution time")
    
    class Config:
        """Pydantic configuration."""
        validate_assignment = True


class StatsResponse(BaseModel):
    """System statistics response."""
    
    total: int = Field(ge=0, description="Total workflows")
    active: int = Field(ge=0, description="Active workflows")
    inactive: int = Field(ge=0, description="Inactive workflows")
    triggers: Dict[str, int] = Field(description="Trigger type distribution")
    complexity: Dict[str, int] = Field(description="Complexity distribution")
    total_nodes: int = Field(ge=0, description="Total node count")
    unique_integrations: int = Field(ge=0, description="Number of unique integrations")
    categories: List[str] = Field(default_factory=list, description="Available categories")
    last_indexed: str = Field(description="Last indexing timestamp")
    database_size_mb: Optional[float] = Field(None, description="Database size in MB")
    
    class Config:
        """Pydantic configuration."""
        validate_assignment = True


class HealthResponse(BaseModel):
    """Health check response."""
    
    status: str = Field(description="Service status")
    message: str = Field(description="Status message")
    timestamp: str = Field(description="Check timestamp")
    database: Dict[str, Any] = Field(description="Database health")
    system: Dict[str, Any] = Field(description="System metrics")
    version: str = Field(description="Application version")
    uptime_seconds: float = Field(ge=0, description="Service uptime")
    
    class Config:
        """Pydantic configuration."""
        validate_assignment = True


class WorkflowDetail(BaseModel):
    """Detailed workflow information for modal display."""
    
    filename: str
    name: str
    description: str
    active: bool
    trigger_type: str
    complexity: str
    node_count: int
    integrations: List[str]
    tags: List[str]
    category: Optional[str] = None
    workflow_id: str
    file_size: int
    file_hash: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    analyzed_at: Optional[str] = None
    json_content: Optional[Dict[str, Any]] = None
    mermaid_diagram: Optional[str] = None
    
    class Config:
        """Pydantic configuration."""
        validate_assignment = True


class ErrorResponse(BaseModel):
    """Standard error response format."""
    
    error: bool = Field(default=True, description="Error flag")
    message: str = Field(description="Error message")
    code: Optional[str] = Field(None, description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")
    timestamp: str = Field(description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")
    
    class Config:
        """Pydantic configuration."""
        validate_assignment = True