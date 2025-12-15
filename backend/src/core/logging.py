import logging
import sys
from datetime import datetime
from logging import Logger
from typing import Optional


def setup_logging(log_level: Optional[str] = None):
    """
    Set up logging configuration for the application.
    
    Args:
        log_level: Optional log level override (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Use the provided log level or default to INFO
    level = getattr(logging, log_level or "INFO")
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),  # Log to stdout
        ]
    )


def get_logger(name: str) -> Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Name of the logger (typically the module name)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_api_call(logger: Logger, endpoint: str, method: str, user_id: Optional[str] = None):
    """
    Log an API call with relevant information.
    
    Args:
        logger: Logger instance to use
        endpoint: API endpoint that was called
        method: HTTP method used
        user_id: Optional user identifier
    """
    user_info = f"User: {user_id}" if user_id else "User: anonymous"
    logger.info(f"API Call - {user_info} - {method} {endpoint}")


def log_hallucination_check(logger: Logger, query: str, response: str, sources: list):
    """
    Log hallucination check results.
    
    Args:
        logger: Logger instance to use
        query: User's original query
        response: Generated response from the model
        sources: Sources used to generate the response
    """
    logger.info(
        f"Hallucination Check - Query: '{query[:50]}...' "
        f"- Sources Count: {len(sources)} - "
        f"Response: '{response[:100]}...'"
    )


def log_chunk_operation(logger: Logger, operation: str, chunk_id: Optional[str] = None):
    """
    Log chunk-related operations.
    
    Args:
        logger: Logger instance to use
        operation: Description of the operation performed
        chunk_id: Optional chunk identifier
    """
    chunk_info = f"Chunk: {chunk_id}" if chunk_id else "Chunk: unknown"
    logger.debug(f"Chunk Operation - {chunk_info} - {operation}")