"""
Node execution logic for workflows.
"""
from typing import Optional
from pathlib import Path
from models import NodeModel, NodeResult, BlockType
from core.context import RunContext
from executors import EXECUTOR_REGISTRY
from api.sixtyfour_client import SixtyfourClient
from core.converters import convert_node_to_block
from .workflow_dataframe import load_input_dataframe


def execute_node(
    node: NodeModel,
    node_id: str,
    parent_ids: list[str],
    run_ctx: RunContext,
    sixtyfour_client: Optional[SixtyfourClient],
    sinks: list[str]
) -> tuple[NodeResult, Optional[object], Optional[dict]]:
    """
    Execute a single node and return its result.
    
    Returns (node_result, df_out, output_info)
    """
    node_result = NodeResult(
        id=node.id,
        type=node.type.value,
        status="running",
        preview_path=None,
        rows=None
    )
    
    run_ctx.log(f"Executing node {node.id} (type: {node.type})")
    
    # Load input DataFrame
    df_in = load_input_dataframe(parent_ids, run_ctx) if parent_ids else None
    if not parent_ids:
        run_ctx.log(f"Node {node.id} is a source node")
    
    # Convert node to block for executor compatibility
    block = convert_node_to_block(node)
    
    # Get executor
    executor = EXECUTOR_REGISTRY.get(node.type)
    if not executor:
        raise ValueError(f"No executor found for node type: {node.type}")
    
    #import ipdb; ipdb.set_trace()
    # Execute node
    df_out = executor.execute(df_in, block, run_ctx, sixtyfour_client)
    #import ipdb; ipdb.set_trace()
    # Save parquet artifact
    if df_out is not None:
        run_ctx.save_parquet(df_out, node_id=node.id)
        preview_path = run_ctx.save_preview(df_out, node.id)
        node_result.preview_path = preview_path
        node_result.rows = len(df_out)
    
    # Track output path for save_csv sink nodes
    output_info = None
    if node.type == BlockType.SAVE_CSV and node_id in sinks:
        params = node.params
        path = params.get("path") if isinstance(params, dict) else (
            params.path if hasattr(params, "path") else None
        )
        
        if path:
            output_csv_path = str(path).replace("{run_id}", run_ctx.run_id)
            # Convert to absolute path if it's a relative path
            path_obj = Path(output_csv_path)
            if not path_obj.is_absolute():
                output_csv_path = str(path_obj.resolve())
        else:
            output_csv_path = str((run_ctx.workspace_dir / "output.csv").resolve())
        
        output_info = {"output_csv_path": output_csv_path}
    
    node_result.status = "success"
    run_ctx.log(f"Node {node.id} completed successfully")
    
    return node_result, df_out, output_info

