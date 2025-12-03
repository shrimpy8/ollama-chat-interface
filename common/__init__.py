"""
Common Utilities Module for Ollama Chat Interface

This module provides shared utilities for the Ollama chat interface:
- Configuration management (config_loader)
- Structured logging setup (logging_config)
- Retry logic for network requests (retry_utils)
- Conversation export utilities (export_utils)

Author: Harsh
"""

from .config_loader import ConfigLoader, load_config
from .logging_config import setup_logging
from .retry_utils import api_request_with_retry
from .export_utils import export_to_json, export_to_markdown, save_export_file

__all__ = [
    'ConfigLoader',
    'load_config',
    'setup_logging',
    'api_request_with_retry',
    'export_to_json',
    'export_to_markdown',
    'save_export_file'
]

__version__ = "1.0.0"
