"""
HTTP client utilities for API requests with retries.
"""
import time
import httpx
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


def make_request_with_retry(
    client: httpx.Client,
    method: str,
    endpoint: str,
    json_data: Optional[Dict[str, Any]] = None,
    max_retries: int = 3,
    retry_delay: float = 1.0
) -> Dict[str, Any]:
    """
    Make HTTP request with retry logic.
    
    Args:
        client: HTTP client instance
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint path
        json_data: Request body as dict
        max_retries: Maximum number of retry attempts
        retry_delay: Base delay between retries (seconds)
        
    Returns:
        Response JSON as dict
        
    Raises:
        httpx.HTTPError: If request fails after retries
    """
    last_error = None
    
    for attempt in range(max_retries):
        try:
            response = client.request(
                method=method,
                url=endpoint,
                json=json_data
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            # Don't retry on 4xx errors (client errors)
            if 400 <= e.response.status_code < 500:
                raise
            last_error = e
        except (httpx.RequestError, httpx.TimeoutException) as e:
            last_error = e
        
        if attempt < max_retries - 1:
            wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
            logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s...")
            time.sleep(wait_time)
    
    # All retries exhausted
    raise httpx.HTTPError(f"Request failed after {max_retries} attempts: {last_error}")

