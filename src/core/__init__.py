"""
Core module for N8N Workflow Documentation System.

Contains data models, exceptions, and core business logic.
"""

from .models import WorkflowMetadata, TriggerType, ComplexityLevel
from .exceptions import WorkflowAnalysisError, DatabaseConnectionError
from .database import WorkflowDatabase

__all__ = [
    "WorkflowMetadata",
    "TriggerType",
    "ComplexityLevel", 
    "WorkflowAnalysisError",
    "DatabaseConnectionError",
    "WorkflowDatabase",
]