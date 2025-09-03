#!/usr/bin/env python3
"""
🚀 N8N Workflows Search Engine Launcher
Start the advanced search system with optimized performance.
"""

import sys
import os
import argparse
import logging
import signal
import socket
import yaml
from pathlib import Path
from typing import Dict, Optional, Callable
from contextlib import contextmanager
from dataclasses import dataclass
import sqlite3

# Configure logging
def setup_logging(debug: bool = False) -> None:
    """Configure logging with proper format and level."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

@dataclass
class Config:
    """Application configuration."""
    host: str
    port: int
    db_path: str
    debug: bool
    
    @classmethod
    def load(cls, config_path: str = "config.yaml") -> "Config":
        """Load configuration from YAML file."""
        default_config = {
            "host": "127.0.0.1",
            "port": 8000,
            "db_path": "database/workflows.db",
            "debug": False
        }
        
        try:
            with open(config_path) as f:
                config = yaml.safe_load(f)
            return cls(**{**default_config, **(config or {})})
        except FileNotFoundError:
            logging.warning(f"Config file {config_path} not found, using defaults")
            return cls(**default_config)

@contextmanager
def get_db_connection() -> sqlite3.Connection:
    """Context manager for database connections."""
    conn = None
    try:
        conn = sqlite3.connect("database/workflows.db")
        conn.row_factory = sqlite3.Row
        yield conn
    finally:
        if conn:
            conn.close()

def validate_port(port: int) -> bool:
    """Validate port number."""
    return 1024 <= port <= 65535

def validate_host(host: str) -> bool:
    """Validate host address."""
    try:
        socket.gethostbyname(host)
        return True
    except socket.error:
        return False

def print_banner():
    """Print application banner."""
    logging.info("🚀 n8n-workflows Advanced Search Engine")
    logging.info("=" * 50)

def check_requirements() -> bool:
    """Check if required dependencies are installed."""
    required_deps = ["sqlite3", "uvicorn", "fastapi", "yaml", "slowapi"]
    missing_deps = []
    
    for dep in required_deps:
        try:
            __import__(dep)
        except ImportError:
            missing_deps.append(dep)
    
    if missing_deps:
        logging.error(f"❌ Missing dependencies: {', '.join(missing_deps)}")
        logging.info("💡 Install with: pip install -r requirements.txt")
        return False
    
    logging.info("✅ Dependencies verified")
    return True

def setup_directories():
    """Create necessary directories."""
    directories = ["database", "static", "workflows", "logs"]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    logging.info("✅ Directories verified")

def setup_database(force_reindex: bool = False) -> str:
    """Setup and initialize the database."""
    from workflow_db import WorkflowDatabase
    
    db_path = "database/workflows.db"
    
    logging.info(f"🔄 Setting up database: {db_path}")
    
    try:
        # Create database instance with path
        db = WorkflowDatabase(db_path)
        
        # Check if database has data or force reindex
        stats = db.get_stats()
        if stats['total'] == 0 or force_reindex:
            logging.info("📚 Indexing workflows...")
            index_stats = db.index_all_workflows(force_reindex=True)
            logging.info(f"✅ Indexed {index_stats['processed']} workflows")
            
            # Show final stats
            final_stats = db.get_stats()
            logging.info(f"📊 Database contains {final_stats['total']} workflows")
        else:
            logging.info(f"✅ Database ready: {stats['total']} workflows")
        
        return db_path
    except Exception as e:
        logging.error(f"Database setup failed: {e}")
        raise

def setup_shutdown_handler(cleanup_func: Callable[[], None]) -> None:
    """Setup graceful shutdown handler."""
    def handler(signum, frame):
        logging.info("Received shutdown signal, cleaning up...")
        cleanup_func()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)

def cleanup() -> None:
    """Cleanup function for graceful shutdown."""
    logging.info("Cleaning up resources...")
    # Add cleanup tasks here

def start_server(host: str = "127.0.0.1", port: int = 8000, reload: bool = False):
    """Start the FastAPI server."""
    if not validate_host(host):
        raise ValueError(f"Invalid host address: {host}")
    if not validate_port(port):
        raise ValueError(f"Invalid port number: {port}")

    logging.info(f"🌐 Starting server at http://{host}:{port}")
    logging.info(f"📊 API Documentation: http://{host}:{port}/docs")
    logging.info(f"🔍 Workflow Search: http://{host}:{port}/api/workflows")
    logging.info("Press Ctrl+C to stop the server")
    logging.info("-" * 50)
    
    # Configure database path
    os.environ['WORKFLOW_DB_PATH'] = "database/workflows.db"
    
    # Setup shutdown handler
    setup_shutdown_handler(cleanup)
    
    # Start uvicorn with better configuration
    import uvicorn
    uvicorn.run(
        "api_server:app", 
        host=host, 
        port=port, 
        reload=reload,
        log_level="debug" if reload else "info",
        access_log=True if reload else False,
        workers=1 if reload else 4
    )

def main():
    """Main entry point with command line arguments."""
    parser = argparse.ArgumentParser(
        description="N8N Workflows Search Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py                    # Start with default settings
  python run.py --port 3000        # Start on port 3000
  python run.py --host 0.0.0.0     # Accept external connections
  python run.py --reindex          # Force database reindexing
  python run.py --dev              # Development mode with auto-reload
        """
    )
    
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to (default: 8000)")
    parser.add_argument("--reindex", action="store_true", help="Force database reindexing")
    parser.add_argument("--dev", action="store_true", help="Development mode with auto-reload")
    parser.add_argument("--config", type=str, help="Path to config file")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    # Setup logging first
    setup_logging(args.debug)
    
    # Load configuration
    config = Config.load(args.config if args.config else "config.yaml")
    
    # Override config with command line arguments
    if args.host != "127.0.0.1":
        config.host = args.host
    if args.port != 8000:
        config.port = args.port
    if args.debug:
        config.debug = True
    
    print_banner()
    
    # Check dependencies
    if not check_requirements():
        sys.exit(1)
    
    # Setup directories
    setup_directories()
    
    # Setup database
    try:
        setup_database(force_reindex=args.reindex)
    except Exception as e:
        logging.error(f"❌ Database setup error: {e}")
        sys.exit(1)
    
    # Start server
    try:
        start_server(
            host=config.host,
            port=config.port,
            reload=args.dev
        )
    except KeyboardInterrupt:
        logging.info("\n👋 Server stopped!")
    except Exception as e:
        logging.error(f"❌ Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()