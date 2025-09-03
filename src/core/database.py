"""
Enhanced SQLite database module for N8N Workflow Documentation System.

This module provides a high-performance, type-safe database layer with
comprehensive error handling, logging, and advanced search capabilities.
"""

import sqlite3
import json
import os
import glob
import hashlib
import time
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager
import logging

from .models import WorkflowMetadata, TriggerType, ComplexityLevel, WorkflowSummary
from .exceptions import (
    DatabaseConnectionError, 
    WorkflowAnalysisError, 
    WorkflowNotFoundError,
    FileSystemError,
    SearchError
)


class WorkflowDatabase:
    """
    High-performance SQLite database for workflow metadata and search.
    
    Features:
    - FTS5 full-text search with sub-100ms response times
    - WAL mode for concurrent access
    - Comprehensive error handling and logging
    - Type-safe operations with Pydantic models
    - Automatic change detection with MD5 hashing
    """
    
    def __init__(self, db_path: Optional[str] = None, workflows_dir: str = "workflows") -> None:
        """
        Initialize the workflow database.
        
        Args:
            db_path: Path to SQLite database file
            workflows_dir: Directory containing workflow JSON files
        """
        # Configure structured logging
        self.logger = self._setup_logging()
        
        # Database configuration
        self.db_path = db_path or os.environ.get('WORKFLOW_DB_PATH', 'database/workflows.db')
        self.workflows_dir = Path(workflows_dir)
        
        # Performance tracking
        self._query_stats = {
            'total_queries': 0,
            'total_time_ms': 0.0,
            'slow_queries': 0
        }
        
        # Initialize database
        try:
            self._ensure_database_directory()
            self.init_database()
            self.logger.info(f"Database initialized successfully at {self.db_path}")
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise DatabaseConnectionError(
                message=f"Database initialization failed: {e}",
                database_path=self.db_path,
                operation="initialization",
                original_error=e
            )
    
    def _setup_logging(self) -> logging.Logger:
        """Set up structured logging for the database module."""
        logger = logging.getLogger(f"{__name__}.WorkflowDatabase")
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        
        return logger
    
    def _ensure_database_directory(self) -> None:
        """Ensure the database directory exists."""
        db_dir = Path(self.db_path).parent
        try:
            db_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise FileSystemError(
                message=f"Failed to create database directory: {db_dir}",
                file_path=str(db_dir),
                operation="mkdir",
                original_error=e
            )
    
    @contextmanager
    def get_connection(self, readonly: bool = False):
        """
        Context manager for database connections with proper error handling.
        
        Args:
            readonly: Whether to open connection in readonly mode
            
        Yields:
            sqlite3.Connection: Database connection
        """
        conn = None
        try:
            # Connection string for readonly access
            if readonly:
                conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
            else:
                conn = sqlite3.connect(self.db_path, timeout=30.0)
                
            # Configure connection for performance
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=10000")
            conn.execute("PRAGMA temp_store=MEMORY")
            conn.execute("PRAGMA foreign_keys=ON")
            
            # Row factory for dict-like access
            conn.row_factory = sqlite3.Row
            
            yield conn
            
        except sqlite3.Error as e:
            self.logger.error(f"Database connection error: {e}")
            if conn:
                conn.rollback()
            raise DatabaseConnectionError(
                message=f"Database connection failed: {e}",
                database_path=self.db_path,
                operation="connection",
                original_error=e
            )
        finally:
            if conn:
                conn.close()
    
    def init_database(self) -> None:
        """Initialize SQLite database with optimized schema and indexes."""
        with self.get_connection() as conn:
            try:
                # Create main workflows table with enhanced schema
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS workflows (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        filename TEXT UNIQUE NOT NULL,
                        name TEXT NOT NULL,
                        workflow_id TEXT,
                        active BOOLEAN DEFAULT 0,
                        description TEXT DEFAULT '',
                        trigger_type TEXT DEFAULT 'Manual',
                        complexity TEXT DEFAULT 'low',
                        node_count INTEGER DEFAULT 0,
                        integrations TEXT DEFAULT '[]',  -- JSON array
                        tags TEXT DEFAULT '[]',          -- JSON array
                        category TEXT,
                        created_at TEXT,
                        updated_at TEXT,
                        file_hash TEXT NOT NULL,
                        file_size INTEGER DEFAULT 0,
                        analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        CONSTRAINT chk_trigger_type CHECK (trigger_type IN ('Manual', 'Webhook', 'Scheduled', 'Complex')),
                        CONSTRAINT chk_complexity CHECK (complexity IN ('low', 'medium', 'high')),
                        CONSTRAINT chk_node_count CHECK (node_count >= 0),
                        CONSTRAINT chk_file_size CHECK (file_size >= 0)
                    )
                """)
                
                # Create FTS5 table for full-text search
                conn.execute("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS workflows_fts USING fts5(
                        filename,
                        name,
                        description,
                        integrations,
                        tags,
                        category,
                        content=workflows,
                        content_rowid=id,
                        tokenize='porter ascii'
                    )
                """)
                
                # Create performance indexes
                indexes = [
                    "CREATE INDEX IF NOT EXISTS idx_workflows_trigger_type ON workflows(trigger_type)",
                    "CREATE INDEX IF NOT EXISTS idx_workflows_complexity ON workflows(complexity)",
                    "CREATE INDEX IF NOT EXISTS idx_workflows_active ON workflows(active)",
                    "CREATE INDEX IF NOT EXISTS idx_workflows_node_count ON workflows(node_count)",
                    "CREATE INDEX IF NOT EXISTS idx_workflows_filename ON workflows(filename)",
                    "CREATE INDEX IF NOT EXISTS idx_workflows_category ON workflows(category)",
                    "CREATE INDEX IF NOT EXISTS idx_workflows_analyzed_at ON workflows(analyzed_at)",
                    "CREATE INDEX IF NOT EXISTS idx_workflows_file_hash ON workflows(file_hash)",
                    "CREATE INDEX IF NOT EXISTS idx_workflows_composite ON workflows(active, trigger_type, complexity)"
                ]
                
                for index_sql in indexes:
                    conn.execute(index_sql)
                
                # Create triggers to keep FTS table in sync
                self._create_fts_triggers(conn)
                
                # Create system metadata table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS system_metadata (
                        key TEXT PRIMARY KEY,
                        value TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Insert version information
                conn.execute("""
                    INSERT OR REPLACE INTO system_metadata (key, value, updated_at)
                    VALUES ('schema_version', '2.0.0', ?)
                """, (datetime.utcnow().isoformat(),))
                
                conn.commit()
                self.logger.info("Database schema initialized successfully")
                
            except sqlite3.Error as e:
                conn.rollback()
                raise DatabaseConnectionError(
                    message=f"Failed to initialize database schema: {e}",
                    database_path=self.db_path,
                    operation="schema_creation",
                    original_error=e
                )
    
    def _create_fts_triggers(self, conn: sqlite3.Connection) -> None:
        """Create triggers to keep FTS table synchronized with main table."""
        
        # Insert trigger
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS workflows_fts_insert AFTER INSERT ON workflows BEGIN
                INSERT INTO workflows_fts(
                    rowid, filename, name, description, integrations, tags, category
                )
                VALUES (
                    new.id, new.filename, new.name, new.description, 
                    new.integrations, new.tags, new.category
                );
            END
        """)
        
        # Delete trigger
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS workflows_fts_delete AFTER DELETE ON workflows BEGIN
                INSERT INTO workflows_fts(
                    workflows_fts, rowid, filename, name, description, integrations, tags, category
                )
                VALUES (
                    'delete', old.id, old.filename, old.name, old.description,
                    old.integrations, old.tags, old.category
                );
            END
        """)
        
        # Update trigger
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS workflows_fts_update AFTER UPDATE ON workflows BEGIN
                INSERT INTO workflows_fts(
                    workflows_fts, rowid, filename, name, description, integrations, tags, category
                )
                VALUES (
                    'delete', old.id, old.filename, old.name, old.description,
                    old.integrations, old.tags, old.category
                );
                INSERT INTO workflows_fts(
                    rowid, filename, name, description, integrations, tags, category
                )
                VALUES (
                    new.id, new.filename, new.name, new.description,
                    new.integrations, new.tags, new.category
                );
            END
        """)
    
    def get_file_hash(self, file_path: Union[str, Path]) -> str:
        """
        Calculate MD5 hash of file for change detection.
        
        Args:
            file_path: Path to the file
            
        Returns:
            str: MD5 hash of the file
        """
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except (OSError, IOError) as e:
            raise FileSystemError(
                message=f"Failed to read file for hashing: {file_path}",
                file_path=str(file_path),
                operation="read",
                original_error=e
            )
    
    def format_workflow_name(self, filename: str) -> str:
        """
        Convert filename to readable workflow name.
        
        Args:
            filename: Original workflow filename
            
        Returns:
            str: Human-readable workflow name
        """
        # Remove .json extension
        name = filename.replace('.json', '')
        
        # Split by underscores
        parts = name.split('_')
        
        # Skip the first part if it's just a number
        if len(parts) > 1 and parts[0].isdigit():
            parts = parts[1:]
        
        # Convert parts to title case with special handling
        readable_parts = []
        for part in parts:
            # Special handling for common terms
            special_cases = {
                'http': 'HTTP',
                'api': 'API',
                'webhook': 'Webhook',
                'automation': 'Automation',
                'scheduled': 'Scheduled',
                'manual': 'Manual',
                'ai': 'AI',
                'ml': 'ML',
                'csv': 'CSV',
                'json': 'JSON',
                'xml': 'XML',
                'sql': 'SQL',
                'ftp': 'FTP',
                'smtp': 'SMTP',
                'oauth': 'OAuth',
                'jwt': 'JWT',
                'crud': 'CRUD'
            }
            
            if part.lower() in special_cases:
                readable_parts.append(special_cases[part.lower()])
            else:
                readable_parts.append(part.capitalize())
        
        return ' '.join(readable_parts)
    
    def _track_query_performance(self, query_type: str, execution_time_ms: float) -> None:
        """Track query performance for monitoring."""
        self._query_stats['total_queries'] += 1
        self._query_stats['total_time_ms'] += execution_time_ms
        
        # Log slow queries
        if execution_time_ms > 1000:  # 1 second threshold
            self._query_stats['slow_queries'] += 1
            self.logger.warning(
                f"Slow query detected: {query_type} took {execution_time_ms:.2f}ms"
            )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get database performance statistics."""
        if self._query_stats['total_queries'] > 0:
            avg_time = self._query_stats['total_time_ms'] / self._query_stats['total_queries']
        else:
            avg_time = 0.0
            
        return {
            'total_queries': self._query_stats['total_queries'],
            'average_query_time_ms': round(avg_time, 2),
            'slow_queries': self._query_stats['slow_queries'],
            'total_execution_time_ms': round(self._query_stats['total_time_ms'], 2)
        }