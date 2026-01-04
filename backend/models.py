"""
Pydantic models for workflow specification and execution (backward compatibility module).
Re-exports from models package.
"""
from .models import (
    BlockType, FilterOperator, FilterRule, FilterParams, ReadCsvParams,
    EnrichLeadParams, FindEmailParams, SaveCsvParams, Block, NodeModel,
    EdgeModel, WorkflowSpec, BlockResult, NodeResult, RunResponse
)

__all__ = [
    "BlockType",
    "FilterOperator",
    "FilterRule",
    "FilterParams",
    "ReadCsvParams",
    "EnrichLeadParams",
    "FindEmailParams",
    "SaveCsvParams",
    "Block",
    "NodeModel",
    "EdgeModel",
    "WorkflowSpec",
    "BlockResult",
    "NodeResult",
    "RunResponse",
]
