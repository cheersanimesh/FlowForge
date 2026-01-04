"""
Node execution loop for workflows.
"""
import traceback
from typing import Tuple

from models import NodeModel, NodeResult, RunResponse
from core.context import RunContext
from api.sixtyfour_client import SixtyfourClient
from .workflow_node_executor import execute_node
from .workflow_response import build_success_response, build_response_with_all_nodes


def execute_node_loop(
    nodes: list[NodeModel],
    edges: list,
    sorted_node_ids: list[str],
    sources: list[str],
    sinks: list[str],
    run_ctx: RunContext,
    sixtyfour_client: SixtyfourClient
) -> Tuple[list, dict, RunResponse | None]:
    """
    Execute all nodes in topological order.
    
    Returns:
        (node_results, outputs, error_response or None)
    """
    # Build node lookup and parent map
    node_map = {node.id: node for node in nodes}
    parents_map = {}
    for edge in edges:
        if edge.to not in parents_map:
            parents_map[edge.to] = []
        parents_map[edge.to].append(edge.from_)
    
    node_results = []
    outputs = {}

    for node_id in sorted_node_ids:
        node = node_map[node_id]
        parent_ids = parents_map.get(node_id, [])
        node_result = None
        
        # Mark node as running before execution
        running_response = build_response_with_all_nodes(
            run_ctx.run_id, nodes, node_results, outputs, sources, sinks,
            current_running_node_id=node_id,
            run_ctx=run_ctx
        )
        running_state = running_response.model_dump()
        run_ctx.save_state(running_state)
        run_ctx.log(f"Starting execution of node {node_id}")
        
        try:
            node_result, df_out, output_info = execute_node(
                node, node_id, parent_ids, run_ctx, sixtyfour_client, sinks
            )
            #import ipdb; ipdb.set_trace()
            node_results.append(node_result)
            
            if output_info:
                outputs[node_id] = output_info
            
            # Save intermediate state after each node completes (includes all nodes)
            intermediate_response = build_response_with_all_nodes(
                run_ctx.run_id, nodes, node_results, outputs, sources, sinks,
                current_running_node_id=None,
                run_ctx=run_ctx
            )
            intermediate_state = intermediate_response.model_dump()
            run_ctx.save_state(intermediate_state)
                
        except Exception as e:
            error_msg = str(e)
            error_trace = traceback.format_exc()
            run_ctx.log(f"Node {node.id} failed: {error_msg}", level="ERROR")
            run_ctx.log(error_trace, level="ERROR")
            
            # Create failed node result if it doesn't exist
            if node_result is None:
                from models import NodeResult
                node_result = NodeResult(
                    id=node.id,
                    type=node.type.value,
                    status="failed",
                    error={"message": error_msg, "trace": error_trace}
                )
            else:
                node_result.status = "failed"
                node_result.error = {"message": error_msg, "trace": error_trace}
            node_results.append(node_result)
            
            # Build error response with all nodes (including failed one)
            error_response = build_response_with_all_nodes(
                run_ctx.run_id, nodes, node_results, outputs, sources, sinks,
                current_running_node_id=None,
                run_ctx=run_ctx
            )
            error_response.status = "failed"
            error_response.error = {"node_id": node.id, "message": error_msg, "trace": error_trace}
            error_state = error_response.model_dump()
            run_ctx.save_state(error_state)
            return (
                node_results, outputs, error_response
            )
    
    return node_results, outputs, None

