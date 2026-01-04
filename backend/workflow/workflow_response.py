"""
Response building utilities for workflow execution.
"""
from typing import Optional
from models import NodeResult, RunResponse, NodeModel
from core.context import RunContext


def build_success_response(
    run_id: str,
    node_results: list[NodeResult],
    outputs: dict,
    sources: list[str],
    sinks: list[str]
) -> RunResponse:
    """Build success response from execution results."""
    return RunResponse(
        run_id=run_id,
        status="success",
        nodes=node_results,
        sources=sources,
        sinks=sinks,
        outputs=outputs if outputs else None
    )


def initialize_components(
    nodes: list[NodeModel],
    sources: list[str],
    sinks: list[str]
) -> RunResponse:
    """Initialize all nodes with queued status."""
    node_results = [
        NodeResult(
            id=node.id,
            type=node.type.value,
            status="queued",
            preview_path=None,
            rows=None,
            error=None
        )
        for node in nodes
    ]
    
    return RunResponse(
        run_id="",  # Will be set by caller
        status="queued",
        nodes=node_results,
        sources=sources,
        sinks=sinks,
        outputs=None,
        error=None
    )


def build_response_with_all_nodes(
    run_id: str,
    all_nodes: list[NodeModel],
    completed_node_results: list[NodeResult],
    outputs: dict,
    sources: list[str],
    sinks: list[str],
    current_running_node_id: str = None,
    running_node_ids: set = None,
    run_ctx: Optional[RunContext] = None
) -> RunResponse:
    """Build response including all nodes with their current statuses."""
    # Create a map of completed nodes
    completed_map = {nr.id: nr for nr in completed_node_results}
    
    # Build set of running node IDs (support both single and multiple)
    running_set = set()
    if running_node_ids:
        running_set = running_node_ids
    elif current_running_node_id:
        running_set = {current_running_node_id}
    
    # Load current state to preserve progress fields
    current_state = None
    state_node_map = {}
    if run_ctx:
        try:
            current_state = run_ctx.load_state()
            if current_state and current_state.get("nodes"):
                for state_node in current_state["nodes"]:
                    state_node_map[state_node.get("id")] = state_node
        except Exception:
            # If we can't load state, continue without it
            pass
    
    # Build list of all nodes with their current statuses
    all_node_results = []
    for node in all_nodes:
        if node.id in completed_map:
            # Use completed result
            all_node_results.append(completed_map[node.id])
        elif node.id in running_set:
            # Mark as running, preserve progress from state if available
            progress = None
            if node.id in state_node_map:
                progress = state_node_map[node.id].get("progress")
            
            all_node_results.append(NodeResult(
                id=node.id,
                type=node.type.value,
                status="running",
                preview_path=None,
                rows=None,
                error=None,
                progress=progress
            ))
        else:
            # Still queued
            all_node_results.append(NodeResult(
                id=node.id,
                type=node.type.value,
                status="queued",
                preview_path=None,
                rows=None,
                error=None
            ))
    
    return RunResponse(
        run_id=run_id,
        status="running",
        nodes=all_node_results,
        sources=sources,
        sinks=sinks,
        outputs=outputs if outputs else None,
        error=None
    )

