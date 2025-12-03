"""
Retry Utilities for Ollama Chat Interface

Provides retry decorators and functions for API calls with exponential backoff.
Handles network errors, timeouts, and HTTP errors gracefully.

Author: Harsh
"""

import logging
from typing import Any, Callable
import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

logger = logging.getLogger(__name__)


def create_retry_decorator(
    max_attempts: int = 3,
    min_wait: int = 2,
    max_wait: int = 10,
    multiplier: int = 2
):
    """
    Create a retry decorator with exponential backoff for network operations.

    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time in seconds
        max_wait: Maximum wait time in seconds
        multiplier: Multiplier for exponential backoff

    Returns:
        Retry decorator configured with specified parameters

    Example:
        >>> @create_retry_decorator(max_attempts=3)
        >>> def my_api_call():
        >>>     return requests.post(url, json=data)
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=multiplier, min=min_wait, max=max_wait),
        retry=retry_if_exception_type((
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.HTTPError,
            requests.exceptions.RequestException
        )),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True
    )


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=10),
    retry=retry_if_exception_type((
        requests.exceptions.ConnectionError,
        requests.exceptions.Timeout,
        requests.exceptions.HTTPError,
        requests.exceptions.RequestException
    )),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True
)
def api_request_with_retry(
    url: str,
    method: str = "POST",
    **kwargs
) -> requests.Response:
    """
    Make an API request with automatic retry logic.

    Uses exponential backoff strategy to handle temporary network issues:
    - Attempt 1: Immediate
    - Attempt 2: Wait 2 seconds
    - Attempt 3: Wait 4 seconds
    - Maximum wait: 10 seconds

    Args:
        url: API endpoint URL
        method: HTTP method (GET, POST, PUT, DELETE, etc.)
        **kwargs: Additional arguments passed to requests.request()
                 (e.g., json, headers, timeout, params)

    Returns:
        Response object from the API

    Raises:
        requests.exceptions.ConnectionError: If connection fails after all retries
        requests.exceptions.Timeout: If request times out after all retries
        requests.exceptions.HTTPError: If HTTP error occurs after all retries
        requests.exceptions.RequestException: For other request errors

    Example:
        >>> response = api_request_with_retry(
        >>>     url="http://localhost:11434/api/generate",
        >>>     method="POST",
        >>>     json={"model": "deepseek-r1:latest", "prompt": "Hello"},
        >>>     timeout=120
        >>> )
        >>> data = response.json()
    """
    logger.info(f"Making {method} request to {url} with retry protection...")

    try:
        response = requests.request(method, url, **kwargs)

        # Raise HTTPError for bad status codes (4xx, 5xx)
        response.raise_for_status()

        logger.info(f"Request successful: {method} {url} - Status {response.status_code}")
        return response

    except requests.exceptions.ConnectionError as e:
        logger.warning(f"Connection error occurred, retrying: {str(e)}")
        raise
    except requests.exceptions.Timeout as e:
        logger.warning(f"Request timeout, retrying: {str(e)}")
        raise
    except requests.exceptions.HTTPError as e:
        logger.warning(f"HTTP error occurred, retrying: {str(e)}")
        raise
    except requests.exceptions.RequestException as e:
        logger.warning(f"Request error occurred, retrying: {str(e)}")
        raise


def safe_api_call(
    api_function: Callable,
    *args,
    fallback_value: Any = None,
    **kwargs
) -> Any:
    """
    Safely call an API function with error handling and optional fallback.

    Wraps API calls to catch and log exceptions, returning a fallback value
    instead of crashing the application.

    Args:
        api_function: The function to call
        *args: Positional arguments for the function
        fallback_value: Value to return if the function fails
        **kwargs: Keyword arguments for the function

    Returns:
        Result of the function call, or fallback_value on error

    Example:
        >>> def get_response(prompt):
        >>>     return api_request_with_retry(url, json={"prompt": prompt})
        >>>
        >>> response = safe_api_call(
        >>>     get_response,
        >>>     "Hello",
        >>>     fallback_value={"error": "Service unavailable"}
        >>> )
    """
    try:
        return api_function(*args, **kwargs)
    except Exception as e:
        logger.error(f"API call failed: {str(e)}", exc_info=True)
        return fallback_value
