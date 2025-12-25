import time
import random
from functools import wraps
from typing import Callable, Type, Any
import requests
import logging


def retry_on_exception(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,),
    logger: logging.Logger = None
):
    """
    Decorator to retry a function when specific exceptions are raised.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        backoff_factor: Multiplier for exponential backoff
        exceptions: Tuple of exception types to catch
        logger: Logger for logging retry attempts
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == max_retries:
                        # Final attempt, raise the exception
                        if logger:
                            logger.error(f"Failed after {max_retries} retries: {str(e)}")
                        raise e

                    # Calculate delay with exponential backoff and jitter
                    delay = min(base_delay * (backoff_factor ** attempt), max_delay)
                    jitter = random.uniform(0, 0.1 * delay)
                    total_delay = delay + jitter

                    if logger:
                        logger.warning(
                            f"Attempt {attempt + 1} failed: {str(e)}. "
                            f"Retrying in {total_delay:.2f} seconds..."
                        )

                    time.sleep(total_delay)

            # This should never be reached, but included for type safety
            raise last_exception

        return wrapper

    return decorator


def is_retryable_http_status(status_code: int) -> bool:
    """
    Check if an HTTP status code indicates a retryable error.

    Args:
        status_code: HTTP status code

    Returns:
        True if the status code is retryable, False otherwise
    """
    retryable_codes = {
        429,  # Too Many Requests
        502,  # Bad Gateway
        503,  # Service Unavailable
        504   # Gateway Timeout
    }
    return status_code in retryable_codes


def retryable_request(
    method: str,
    url: str,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    logger: logging.Logger = None,
    **kwargs
) -> requests.Response:
    """
    Make an HTTP request with retry logic for retryable status codes.

    Args:
        method: HTTP method (GET, POST, etc.)
        url: Request URL
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries
        max_delay: Maximum delay between retries
        backoff_factor: Multiplier for exponential backoff
        logger: Logger for logging retry attempts
        **kwargs: Additional arguments to pass to requests

    Returns:
        requests.Response object
    """
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            response = requests.request(method, url, **kwargs)

            # If successful or not retryable, return immediately
            if response.status_code < 400 or not is_retryable_http_status(response.status_code):
                return response

            # If retryable error, continue to next attempt
            if attempt == max_retries:
                if logger:
                    logger.error(f"Request failed after {max_retries} retries: {response.status_code} {response.reason}")
                response.raise_for_status()

        except requests.RequestException as e:
            last_exception = e

            if attempt == max_retries:
                if logger:
                    logger.error(f"Request failed after {max_retries} retries: {str(e)}")
                raise e

        # Calculate delay with exponential backoff and jitter
        delay = min(base_delay * (backoff_factor ** attempt), max_delay)
        jitter = random.uniform(0, 0.1 * delay)
        total_delay = delay + jitter

        if logger:
            logger.warning(
                f"Request attempt {attempt + 1} failed. "
                f"Retrying in {total_delay:.2f} seconds..."
            )

        time.sleep(total_delay)

    # This should never be reached, but included for type safety
    raise last_exception