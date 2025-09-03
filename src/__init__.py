"""
N8N Workflow Documentation System

A high-performance FastAPI application for browsing and searching 
n8n workflow documentation with advanced filtering and categorization.
"""

__version__ = "2.0.0"
__author__ = "N8N Workflow Team"
__email__ = "support@n8n-workflows.com"

from .core.models import WorkflowMetadata, TriggerType, ComplexityLevel
from .core.exceptions import WorkflowAnalysisError, DatabaseConnectionError

__all__ = [
    "WorkflowMetadata",
    "TriggerType", 
    "ComplexityLevel",
    "WorkflowAnalysisError",
    "DatabaseConnectionError",
]