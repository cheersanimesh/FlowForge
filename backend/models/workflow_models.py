"""
Workflow specification models.
"""
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, model_validator

from .enums import BlockType
from .params import (
    ReadCsvParams, FilterParams, EnrichLeadParams, 
    FindEmailParams, SaveCsvParams
)


class Block(BaseModel):
    """A single workflow block."""
    id: str = Field(..., description="Unique block identifier")
    type: BlockType = Field(..., description="Block type")
    params: Union[
        ReadCsvParams, FilterParams, EnrichLeadParams, 
        FindEmailParams, SaveCsvParams, Dict[str, Any]
    ] = Field(..., description="Block-specific parameters")


class NodeModel(BaseModel):
    """A single workflow node (DAG format)."""
    id: str = Field(..., description="Unique node identifier")
    type: BlockType = Field(..., description="Node type")
    params: Dict[str, Any] = Field(..., description="Node-specific parameters")


class EdgeModel(BaseModel):
    """An edge in the workflow DAG."""
    from_: str = Field(..., alias="from", description="Source node ID")
    to: str = Field(..., description="Target node ID")


class WorkflowSpec(BaseModel):
    """Complete workflow specification."""
    nodes: List[NodeModel] = Field(..., min_length=1, description="List of nodes (DAG format)")
    edges: Optional[List[EdgeModel]] = Field(None, description="List of edges (DAG format)")

