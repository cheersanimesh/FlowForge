"""
Client for Sixtyfour API with authentication, timeouts, and retries.
"""
import os
from typing import Dict, Any, Optional
import httpx
from dotenv import load_dotenv

from .http_client_utils import make_request_with_retry


class SixtyfourClient:
    """Client for interacting with Sixtyfour API."""
    
    BASE_URL = "https://api.sixtyfour.ai"
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0  # seconds
    TIMEOUT = 120.0  # seconds
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize client with API key."""
        load_dotenv()
        self.api_key = api_key or os.getenv("SIXTYFOUR_API_KEY")
        if not self.api_key:
            raise ValueError("SIXTYFOUR_API_KEY environment variable not set")
        
        self.client = httpx.Client(
            base_url=self.BASE_URL,
            headers={
                "x-api-key": f"{self.api_key}",
                "Content-Type": "application/json"
            },
            timeout=self.TIMEOUT
        )
    
    def enrich_lead(
        self,
        lead_info: Dict[str, Any],
        struct: Dict[str, str],
        research_plan: Optional[str] = None
    ) -> Dict[str, Any]:
        """Enrich a lead using the /enrich-lead endpoint."""
        payload = {"lead_info": lead_info, "struct": struct}
        if research_plan:
            payload["research_plan"] = research_plan
        #import ipdb; ipdb.set_trace()
        
        return make_request_with_retry(
            self.client, "POST", "/enrich-lead", payload,
            self.MAX_RETRIES, self.RETRY_DELAY
        )
    
    def enrich_lead_async(
        self,
        lead_info: Dict[str, Any],
        struct: Dict[str, str],
        research_plan: Optional[str] = None
    ) -> Dict[str, Any]:
        """Start an async enrich lead job using the /enrich-lead-async endpoint."""
        payload = {"lead_info": lead_info, "struct": struct}
        if research_plan:
            payload["research_plan"] = research_plan
        
        return make_request_with_retry(
            self.client, "POST", "/enrich-lead-async", payload,
            self.MAX_RETRIES, self.RETRY_DELAY
        )
    
    def get_job_status(self, task_id: str) -> Dict[str, Any]:
        """Get the status of an async job using the /job-status/{task_id} endpoint."""
        return make_request_with_retry(
            self.client, "GET", f"/job-status/{task_id}", None,
            self.MAX_RETRIES, self.RETRY_DELAY
        )
    
    def find_email(
        self,
        lead_info: Dict[str, Any],
        mode: str = "PROFESSIONAL"
    ) -> Dict[str, Any]:
        """Find email for a lead using the /find-email endpoint."""
        payload = {"lead": lead_info, "mode": mode}
        return make_request_with_retry(
            self.client, "POST", "/find-email", payload,
            self.MAX_RETRIES, self.RETRY_DELAY
        )
    
    def close(self):
        """Close the HTTP client."""
        self.client.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
