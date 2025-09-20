"""
Logging configuration for Google ADK Teams Bot
Provides structured logging with console and file outputs
"""

import os
import sys
import json
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage(),
            'thread_name': record.threadName,
            'process_id': record.process
        }
        
        if hasattr(record, 'user_id'):
            log_obj['user_id'] = record.user_id
            
        if hasattr(record, 'conversation_id'):
            log_obj['conversation_id'] = record.conversation_id
            
        if hasattr(record, 'request_id'):
            log_obj['request_id'] = record.request_id
            
        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_obj)


def setup_logging(log_level: str = None) -> logging.Logger:
    """
    Configure logging for the application
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Configured logger instance
    """
    log_level = log_level or os.getenv('LOG_LEVEL', 'INFO')
    
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    logger = logging.getLogger('adk_teams_bot')
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    logger.handlers = []
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / 'app.log',
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    json_formatter = JSONFormatter()
    file_handler.setFormatter(json_formatter)
    logger.addHandler(file_handler)
    
    error_file_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / 'error.log',
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(json_formatter)
    logger.addHandler(error_file_handler)
    
    return logger


def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger instance
    
    Args:
        name: Logger name (defaults to 'adk_teams_bot')
        
    Returns:
        Logger instance
    """
    if name:
        return logging.getLogger(f'adk_teams_bot.{name}')
    return logging.getLogger('adk_teams_bot')


def log_request(logger: logging.Logger, request_data: Dict[str, Any]) -> None:
    """
    Log incoming request details
    
    Args:
        logger: Logger instance
        request_data: Request data to log
    """
    logger.info(
        "Incoming request",
        extra={
            'request_id': request_data.get('id'),
            'user_id': request_data.get('from', {}).get('id'),
            'conversation_id': request_data.get('conversation', {}).get('id')
        }
    )


def log_response(logger: logging.Logger, response_data: Dict[str, Any], duration_ms: float) -> None:
    """
    Log outgoing response details
    
    Args:
        logger: Logger instance
        response_data: Response data to log
        duration_ms: Request processing duration in milliseconds
    """
    logger.info(
        f"Response sent (duration: {duration_ms:.2f}ms)",
        extra={
            'response_type': response_data.get('type'),
            'duration_ms': duration_ms
        }
    )


def log_error(logger: logging.Logger, error: Exception, context: Dict[str, Any] = None) -> None:
    """
    Log error with context
    
    Args:
        logger: Logger instance
        error: Exception to log
        context: Additional context data
    """
    logger.error(
        f"Error occurred: {str(error)}",
        exc_info=True,
        extra=context or {}
    )


logger = setup_logging()