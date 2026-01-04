"""
Validation helpers for workflow execution.
"""
from pathlib import Path

from models import NodeModel, RunResponse, BlockType
from core.context import RunContext


def validate_csv_files(nodes: list[NodeModel], run_ctx: RunContext):
    """
    Validate that all read_csv nodes have existing files.
    
    Returns RunResponse with error if validation fails, None otherwise.
    """
    for node in nodes:
        if node.type == BlockType.READ_CSV:
            
            params = node.params
            path = params.get("path") if isinstance(params, dict) else (
                params.path if hasattr(params, "path") else None
            )
            
            if path and not Path(path).exists():
                error_msg = f"CSV file not found: {path}"
                run_ctx.log(f"Validation failed: {error_msg}", level="ERROR")
                return RunResponse(
                    run_id=run_ctx.run_id,
                    status="failed",
                    nodes=[],
                    error={
                        "node_id": node.id,
                        "message": error_msg,
                        "trace": None
                    }
                )
    return None

