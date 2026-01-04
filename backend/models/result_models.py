"""
Result models for workflow execution.
"""
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel


class BlockResult(BaseModel):
    """Result of executing a single block."""
    id: str
    type: str
    status: Literal["queued", "running", "success", "failed"]
    preview_path: Optional[str] = None
    rows: Optional[int] = None
    error: Optional[Dict[str, Any]] = None


class NodeResult(BaseModel):
    """Result of executing a single node."""
    id: str
    type: str
    status: Literal["queued", "running", "success", "failed"]
    preview_path: Optional[str] = None
    rows: Optional[int] = None
    error: Optional[Dict[str, Any]] = None
    progress: Optional[float] = None  # Percentage completed (0-100)


class RunResponse(BaseModel):
    """Response from /run endpoint."""
    run_id: str
    status: Literal["queued", "running", "success", "failed"]
    nodes: Optional[List[NodeResult]] = None
    sources: Optional[List[str]] = None  # Source node IDs
    sinks: Optional[List[str]] = None  # Sink node IDs
    outputs: Optional[Dict[str, Dict[str, str]]] = None  # {node_id: {"output_csv_path": "..."}}
    error: Optional[Dict[str, Any]] = None

