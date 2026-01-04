"""
Core workflow execution logic.
"""
import traceback
import asyncio
from pathlib import Path
import logging

from models import WorkflowSpec, RunResponse
from core.context import RunContext
from api.sixtyfour_client import SixtyfourClient
from .workflow_validation import validate_csv_files
from .workflow_dag_setup import setup_and_validate_dag
from .workflow_orchestrator import execute_workflow_parallel
from .workflow_response import build_success_response, initialize_components

logger = logging.getLogger(__name__)


def execute_workflow(spec: WorkflowSpec, run_ctx: RunContext, workspace_dir: Path) -> RunResponse:
    """
    Execute a workflow specification.
    
    Uses DAG format (nodes + edges).
    """
    sixtyfour_client = None
    
    try:
        run_ctx.log("Workflow execution started")
        
        # Setup and validate DAG
        nodes, edges, sources, sinks, error_response = setup_and_validate_dag(spec, run_ctx)
        if error_response:
            error_state = error_response.model_dump()
            run_ctx.save_state(error_state)
            return error_response
        
        # Initialize all components with "queued" status
        initial_response = initialize_components(nodes, sources, sinks)
        initial_response.run_id = run_ctx.run_id
        initial_response.status = "running"  # Workflow is now running
        initial_state = initial_response.model_dump()
        run_ctx.save_state(initial_state)
        run_ctx.log(f"Initialized {len(nodes)} components with queued status")
        
        # Initialize Sixtyfour client
        try:
            sixtyfour_client = SixtyfourClient()
        except ValueError as e:
            logger.warning(f"Sixtyfour client initialization failed: {e}")
        
        # Validate CSV files
        csv_validation = validate_csv_files(nodes, run_ctx)
        
        if csv_validation:
            error_state = csv_validation.model_dump()
            run_ctx.save_state(error_state)
            return csv_validation
        
        # Execute nodes in parallel using async orchestrator
        # Handle both cases: with existing event loop or without
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, create a new event loop in a thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        execute_workflow_parallel(
                            nodes, edges, sources, sinks,
                            run_ctx, sixtyfour_client
                        )
                    )
                    node_results, outputs, error_response = future.result()
            else:
                # Loop exists but not running, we can use it
                node_results, outputs, error_response = loop.run_until_complete(
                    execute_workflow_parallel(
                        nodes, edges, sources, sinks,
                        run_ctx, sixtyfour_client
                    )
                )
        except RuntimeError:
            # No event loop exists, create a new one
            node_results, outputs, error_response = asyncio.run(
                execute_workflow_parallel(
                    nodes, edges, sources, sinks,
                    run_ctx, sixtyfour_client
                )
            )
        if error_response:
            error_state = error_response.model_dump()
            run_ctx.save_state(error_state)
            return error_response
        
        # All nodes completed successfully
        run_ctx.log("Workflow execution completed successfully")
        
        success_response = build_success_response(
            run_ctx.run_id, node_results, outputs, sources, sinks
        )
        success_state = success_response.model_dump()
        run_ctx.save_state(success_state)
        return success_response
        
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        run_ctx.log(f"Workflow execution failed: {error_msg}", level="ERROR")
        run_ctx.log(error_trace, level="ERROR")
        
        error_response = RunResponse(
            run_id=run_ctx.run_id,
            status="failed",
            nodes=[],
            error={"node_id": None, "message": error_msg, "trace": error_trace}
        )
        error_state = error_response.model_dump()
        run_ctx.save_state(error_state)
        return error_response
    
    finally:
        if sixtyfour_client:
            sixtyfour_client.close()
