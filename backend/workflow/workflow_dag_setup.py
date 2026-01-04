"""
DAG setup and validation for workflow execution.
"""
from typing import Tuple

from models import WorkflowSpec, NodeModel, EdgeModel, RunResponse
from core.context import RunContext
from validators.dag_validator import DAGValidator


def setup_and_validate_dag(
    spec: WorkflowSpec, 
    run_ctx: RunContext
) -> Tuple[list, list, list, list, RunResponse | None]:
    """
    Setup and validate DAG from workflow spec.
    
    Returns:
        (nodes, edges, sources, sinks, error_response or None)
    """
    nodes = spec.nodes
    edges = spec.edges or []
    run_ctx.log(f"Using DAG format with {len(nodes)} nodes and {len(edges)} edges")
    
    # Validate DAG
    dag_validator = DAGValidator()
    validation_errors = dag_validator.validate_dag(nodes, edges)
    if validation_errors:
        error_msg = "; ".join(validation_errors)
        run_ctx.log(f"DAG validation failed: {error_msg}", level="ERROR")
        return (
            nodes, edges, [], [],
            RunResponse(
                run_id=run_ctx.run_id,
                status="failed",
                nodes=[],
                error={"node_id": None, "message": f"Validation failed: {error_msg}", "trace": None}
            )
        )
    
    # Get sources and sinks
    sources, sinks = dag_validator.get_sources_and_sinks(nodes, edges)
    run_ctx.log(f"Sources: {sources}, Sinks: {sinks}")
    
    # Topological sort
    sorted_node_ids, cycle_nodes = dag_validator.topological_sort(nodes, edges)
    if cycle_nodes:
        error_msg = f"Cycle detected: {cycle_nodes}"
        run_ctx.log(f"DAG validation failed: {error_msg}", level="ERROR")
        return (
            nodes, edges, sources, sinks,
            RunResponse(
                run_id=run_ctx.run_id,
                status="failed",
                nodes=[],
                sources=sources,
                sinks=sinks,
                error={"node_id": None, "message": error_msg, "trace": None}
            )
        )
    
    return nodes, edges, sources, sinks, None

