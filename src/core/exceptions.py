"""
Custom exceptions for the N8N Workflow Documentation System.

This module defines all custom exceptions used throughout the application
with proper error messages, status codes, and context information.
"""

from typing import Optional, Dict, Any
from datetime import datetime


class BaseWorkflowError(Exception):
    """
    Base exception class for all workflow-related errors.
    
    Provides common functionality for error handling including
    error codes, messages, and contextual information.
    """
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ) -> None:
        """
        Initialize base workflow error.
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            context: Additional context information
            original_error: Original exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.context = context or {}
        self.original_error = original_error
        self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": True,
            "message": self.message,
            "error_code": self.error_code,
            "context": self.context,
            "timestamp": self.timestamp,
            "original_error": str(self.original_error) if self.original_error else None
        }
    
    def __str__(self) -> str:
        """String representation of the error."""
        return f"{self.error_code}: {self.message}"
    
    def __repr__(self) -> str:
        """Detailed representation of the error."""
        return (
            f"{self.__class__.__name__}("
            f"message='{self.message}', "
            f"error_code='{self.error_code}', "
            f"context={self.context}"
            f")"
        )


class WorkflowAnalysisError(BaseWorkflowError):
    """
    Exception raised when workflow analysis fails.
    
    This includes JSON parsing errors, invalid workflow structure,
    or missing required fields in workflow files.
    """
    
    def __init__(
        self,
        message: str,
        filename: Optional[str] = None,
        line_number: Optional[int] = None,
        original_error: Optional[Exception] = None
    ) -> None:
        """
        Initialize workflow analysis error.
        
        Args:
            message: Error description
            filename: Name of the problematic workflow file
            line_number: Line number where error occurred (if applicable)
            original_error: Original parsing or validation error
        """
        context = {}
        if filename:
            context["filename"] = filename
        if line_number:
            context["line_number"] = line_number
            
        super().__init__(
            message=message,
            error_code="WORKFLOW_ANALYSIS_ERROR",
            context=context,
            original_error=original_error
        )
        
        self.filename = filename
        self.line_number = line_number


class DatabaseConnectionError(BaseWorkflowError):
    """
    Exception raised when database operations fail.
    
    This includes connection errors, query failures, transaction rollbacks,
    and database initialization problems.
    """
    
    def __init__(
        self,
        message: str,
        database_path: Optional[str] = None,
        operation: Optional[str] = None,
        original_error: Optional[Exception] = None
    ) -> None:
        """
        Initialize database connection error.
        
        Args:
            message: Error description
            database_path: Path to the database file
            operation: Database operation that failed
            original_error: Original database error
        """
        context = {}
        if database_path:
            context["database_path"] = database_path
        if operation:
            context["operation"] = operation
            
        super().__init__(
            message=message,
            error_code="DATABASE_CONNECTION_ERROR",
            context=context,
            original_error=original_error
        )
        
        self.database_path = database_path
        self.operation = operation


class ConfigurationError(BaseWorkflowError):
    """
    Exception raised when configuration is invalid or missing.
    
    This includes missing configuration files, invalid configuration values,
    or environment setup problems.
    """
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        config_file: Optional[str] = None,
        original_error: Optional[Exception] = None
    ) -> None:
        """
        Initialize configuration error.
        
        Args:
            message: Error description
            config_key: Configuration key that caused the error
            config_file: Configuration file path
            original_error: Original configuration error
        """
        context = {}
        if config_key:
            context["config_key"] = config_key
        if config_file:
            context["config_file"] = config_file
            
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            context=context,
            original_error=original_error
        )
        
        self.config_key = config_key
        self.config_file = config_file


class ValidationError(BaseWorkflowError):
    """
    Exception raised when input validation fails.
    
    This includes invalid API parameters, malformed requests,
    or business rule violations.
    """
    
    def __init__(
        self,
        message: str,
        field_name: Optional[str] = None,
        field_value: Optional[Any] = None,
        validation_rule: Optional[str] = None,
        original_error: Optional[Exception] = None
    ) -> None:
        """
        Initialize validation error.
        
        Args:
            message: Error description
            field_name: Name of the field that failed validation
            field_value: Value that failed validation
            validation_rule: Validation rule that was violated
            original_error: Original validation error
        """
        context = {}
        if field_name:
            context["field_name"] = field_name
        if field_value is not None:
            context["field_value"] = str(field_value)
        if validation_rule:
            context["validation_rule"] = validation_rule
            
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            context=context,
            original_error=original_error
        )
        
        self.field_name = field_name
        self.field_value = field_value
        self.validation_rule = validation_rule


class WorkflowNotFoundError(BaseWorkflowError):
    """
    Exception raised when a requested workflow cannot be found.
    
    This includes missing workflow files or database records.
    """
    
    def __init__(
        self,
        workflow_identifier: str,
        identifier_type: str = "filename",
        original_error: Optional[Exception] = None
    ) -> None:
        """
        Initialize workflow not found error.
        
        Args:
            workflow_identifier: Workflow filename, ID, or other identifier
            identifier_type: Type of identifier (filename, id, etc.)
            original_error: Original error that led to this
        """
        message = f"Workflow not found: {workflow_identifier}"
        context = {
            "workflow_identifier": workflow_identifier,
            "identifier_type": identifier_type
        }
        
        super().__init__(
            message=message,
            error_code="WORKFLOW_NOT_FOUND",
            context=context,
            original_error=original_error
        )
        
        self.workflow_identifier = workflow_identifier
        self.identifier_type = identifier_type


class FileSystemError(BaseWorkflowError):
    """
    Exception raised when file system operations fail.
    
    This includes file reading/writing errors, permission issues,
    or missing directories.
    """
    
    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        operation: Optional[str] = None,
        original_error: Optional[Exception] = None
    ) -> None:
        """
        Initialize file system error.
        
        Args:
            message: Error description
            file_path: Path to the problematic file
            operation: File operation that failed
            original_error: Original file system error
        """
        context = {}
        if file_path:
            context["file_path"] = file_path
        if operation:
            context["operation"] = operation
            
        super().__init__(
            message=message,
            error_code="FILESYSTEM_ERROR",
            context=context,
            original_error=original_error
        )
        
        self.file_path = file_path
        self.operation = operation


class SearchError(BaseWorkflowError):
    """
    Exception raised when search operations fail.
    
    This includes FTS5 query errors, index corruption,
    or search timeout issues.
    """
    
    def __init__(
        self,
        message: str,
        search_query: Optional[str] = None,
        search_filters: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ) -> None:
        """
        Initialize search error.
        
        Args:
            message: Error description
            search_query: Search query that failed
            search_filters: Applied search filters
            original_error: Original search error
        """
        context = {}
        if search_query:
            context["search_query"] = search_query
        if search_filters:
            context["search_filters"] = search_filters
            
        super().__init__(
            message=message,
            error_code="SEARCH_ERROR",
            context=context,
            original_error=original_error
        )
        
        self.search_query = search_query
        self.search_filters = search_filters


class CategoryError(BaseWorkflowError):
    """
    Exception raised when category operations fail.
    
    This includes category mapping errors, invalid categories,
    or category file processing issues.
    """
    
    def __init__(
        self,
        message: str,
        category_name: Optional[str] = None,
        integration_name: Optional[str] = None,
        original_error: Optional[Exception] = None
    ) -> None:
        """
        Initialize category error.
        
        Args:
            message: Error description
            category_name: Name of the problematic category
            integration_name: Integration that couldn't be categorized
            original_error: Original categorization error
        """
        context = {}
        if category_name:
            context["category_name"] = category_name
        if integration_name:
            context["integration_name"] = integration_name
            
        super().__init__(
            message=message,
            error_code="CATEGORY_ERROR",
            context=context,
            original_error=original_error
        )
        
        self.category_name = category_name
        self.integration_name = integration_name