"""
Async workflow orchestrator for parallel node execution.

Executes nodes as soon as their parents complete, using async queues
to maximize throughput by running ready nodes in parallel.
"""
import asyncio
import traceback
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict

from models import NodeModel, NodeResult, RunResponse
from core.context import RunContext
from api.sixtyfour_client import SixtyfourClient
from .workflow_node_executor import execute_node
from .workflow_response import build_success_response, build_response_with_all_nodes


class WorkflowOrchestrator:
    """Orchestrates parallel execution of workflow nodes."""
    
    def __init__(
        self,
        nodes: List[NodeModel],
        edges: List,
        sources: List[str],
        sinks: List[str],
        run_ctx: RunContext,
        sixtyfour_client: Optional[SixtyfourClient]
    ):
        """Initialize the orchestrator."""
        self.nodes = nodes
        self.edges = edges
        self.sources = sources
        self.sinks = sinks
        self.run_ctx = run_ctx
        self.sixtyfour_client = sixtyfour_client
        
        # Build node lookup
        self.node_map = {node.id: node for node in nodes}
        
        # Build parent and child relationships
        self.parents_map: Dict[str, List[str]] = defaultdict(list)
        self.children_map: Dict[str, List[str]] = defaultdict(list)
        
        for edge in edges:
            self.parents_map[edge.to].append(edge.from_)
            self.children_map[edge.from_].append(edge.to)
        
        # Track execution state
        self.completed_nodes: Set[str] = set()
        self.node_results: List[NodeResult] = []
        self.outputs: Dict[str, dict] = {}
        self.failed_node_id: Optional[str] = None
        self.error_response: Optional[RunResponse] = None
        
        # Lock for thread-safe state updates
        self.state_lock = asyncio.Lock()
    
    def _get_ready_nodes(self) -> List[str]:
        """Get all nodes that are ready to execute (all parents completed)."""
        ready = []
        for node_id in self.node_map.keys():
            if node_id in self.completed_nodes:
                continue  # Already completed
            
            # Check if all parents are completed
            parent_ids = self.parents_map.get(node_id, [])
            if all(parent_id in self.completed_nodes for parent_id in parent_ids):
                ready.append(node_id)
        
        return ready
    
    async def _execute_node_async(
        self,
        node_id: str
    ) -> Tuple[NodeResult, Optional[dict]]:
        """
        Execute a single node asynchronously.
        
        Returns:
            (node_result, output_info)
        """
        node = self.node_map[node_id]
        parent_ids = self.parents_map.get(node_id, [])
        
        # Run the synchronous execute_node in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        try:
            node_result, df_out, output_info = await loop.run_in_executor(
                None,
                execute_node,
                node,
                node_id,
                parent_ids,
                self.run_ctx,
                self.sixtyfour_client,
                self.sinks
            )
            return node_result, output_info
        except Exception as e:
            # Handle execution error
            error_msg = str(e)
            error_trace = traceback.format_exc()
            self.run_ctx.log(f"Node {node_id} failed: {error_msg}", level="ERROR")
            self.run_ctx.log(error_trace, level="ERROR")
            
            node_result = NodeResult(
                id=node.id,
                type=node.type.value,
                status="failed",
                error={"message": error_msg, "trace": error_trace}
            )
            return node_result, None
    
    def _update_state_internal(self, running_node_ids: Set[str]):
        """Internal state update without locking (caller must hold lock)."""
        self.run_ctx.log(f"Building response with {len(self.node_results)} completed nodes, {len(running_node_ids)} running")
        intermediate_response = build_response_with_all_nodes(
            self.run_ctx.run_id,
            self.nodes,
            self.node_results,
            self.outputs,
            self.sources,
            self.sinks,
            running_node_ids=running_node_ids,
            run_ctx=self.run_ctx
        )
        
        self.run_ctx.log(f"Response built, dumping to dict...")
        intermediate_state = intermediate_response.model_dump()
        self.run_ctx.log(f"State dict created, saving to file...")
        # Save state synchronously to ensure immediate persistence
        self.run_ctx.save_state(intermediate_state)
        self.run_ctx.log(
            f"State updated: {len(self.completed_nodes)}/{len(self.nodes)} completed, "
            f"{len(running_node_ids)} running: {sorted(running_node_ids) if running_node_ids else 'none'}"
        )
    
    async def _update_state(self, running_node_ids: Set[str]):
        """Update workflow state with current execution status."""
        async with self.state_lock:
            self._update_state_internal(running_node_ids)
    
    async def _mark_node_completed(
        self,
        node_id: str,
        node_result: NodeResult,
        output_info: Optional[dict],
        running_node_ids: Set[str]
    ):
        """Mark a node as completed and update state."""
        self.run_ctx.log(f"Marking node {node_id} as completed with status {node_result.status}")
        async with self.state_lock:
            self.completed_nodes.add(node_id)
            self.node_results.append(node_result)
            
            if output_info:
                self.outputs[node_id] = output_info
            
            # Update state after node completion (excluding the just-completed node)
            # Remove the completed node from running set if present
            running_set = running_node_ids - {node_id}
            self.run_ctx.log(f"Updating state: node {node_id} completed, remaining running: {sorted(running_set)}")
            # Use internal method since we already hold the lock
            self._update_state_internal(running_set)
    
    async def execute(self) -> Tuple[List[NodeResult], Dict[str, dict], Optional[RunResponse]]:
        """
        Execute all nodes in parallel, starting nodes as soon as their parents complete.
        
        Returns:
            (node_results, outputs, error_response or None)
        """
        total_nodes = len(self.nodes)
        
        # Initialize with source nodes (nodes with no parents)
        ready_queue = asyncio.Queue()
        initial_ready = self._get_ready_nodes()
        
        for node_id in initial_ready:
            await ready_queue.put(node_id)
            self.run_ctx.log(f"Node {node_id} is ready to execute (source node)")
        
        # Track running tasks
        running_tasks: Dict[str, asyncio.Task] = {}
        max_concurrent = 10  # Maximum number of nodes to run in parallel
        
        try:
            iteration = 0
            while len(self.completed_nodes) < total_nodes:
                iteration += 1
                self.run_ctx.log(f"Orchestrator loop iteration {iteration}: {len(self.completed_nodes)}/{total_nodes} completed, {len(running_tasks)} running")
                
                # Check if we have failed
                if self.failed_node_id:
                    self.run_ctx.log(f"Workflow failed at node {self.failed_node_id}, breaking")
                    break
                
                # Start new tasks if we have capacity and ready nodes
                while (
                    len(running_tasks) < max_concurrent and
                    not ready_queue.empty() and
                    not self.failed_node_id
                ):
                    try:
                        node_id = ready_queue.get_nowait()
                        
                        # Skip if already completed (shouldn't happen, but safety check)
                        if node_id in self.completed_nodes:
                            continue
                        
                        # Create task for node execution
                        task = asyncio.create_task(self._execute_node_async(node_id))
                        running_tasks[node_id] = task
                        self.run_ctx.log(f"Starting execution of node {node_id}")
                        
                        # Update state to show node as running
                        await self._update_state(set(running_tasks.keys()))
                        
                    except asyncio.QueueEmpty:
                        break
                
                # Wait for at least one task to complete
                if not running_tasks:
                    # No tasks running and queue is empty, but not all nodes completed
                    # This shouldn't happen in a valid DAG, but handle gracefully
                    if ready_queue.empty():
                        self.run_ctx.log(
                            "Warning: No tasks running and queue is empty, "
                            f"but only {len(self.completed_nodes)}/{total_nodes} nodes completed",
                            level="ERROR"
                        )
                        break
                    continue
                
                # Wait for at least one task to complete
                self.run_ctx.log(f"Waiting for {len(running_tasks)} running task(s) to complete...")
                # Check if any tasks are already done (in case they completed very quickly)
                already_done = {task for task in running_tasks.values() if task.done()}
                if already_done:
                    self.run_ctx.log(f"Found {len(already_done)} task(s) already completed")
                    done = already_done
                    pending = set(running_tasks.values()) - already_done
                else:
                    # Wait for at least one to complete
                    done, pending = await asyncio.wait(
                        running_tasks.values(),
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    self.run_ctx.log(f"Got {len(done)} completed task(s) from wait, {len(pending)} still pending")
                
                # Process completed tasks
                self.run_ctx.log(f"Processing {len(done)} completed task(s)")
                for task in done:
                    # Find which node this task belongs to
                    completed_node_id = None
                    for node_id, t in running_tasks.items():
                        if t == task:
                            completed_node_id = node_id
                            break
                    
                    if not completed_node_id:
                        self.run_ctx.log("Warning: Could not find node_id for completed task", level="WARNING")
                        continue
                    
                    self.run_ctx.log(f"Task for node {completed_node_id} completed, getting result...")
                    # Get result
                    try:
                        node_result, output_info = await task
                        self.run_ctx.log(f"Got result for node {completed_node_id}: status={node_result.status}")
                        
                        # Get current running tasks (before removing this one)
                        current_running = set(running_tasks.keys())
                        
                        # Remove from running tasks
                        del running_tasks[completed_node_id]
                        
                        # Check if node failed
                        if node_result.status == "failed":
                            self.failed_node_id = completed_node_id
                            await self._mark_node_completed(
                                completed_node_id,
                                node_result,
                                output_info,
                                current_running
                            )
                            
                            # Build error response
                            self.error_response = build_response_with_all_nodes(
                                self.run_ctx.run_id,
                                self.nodes,
                                self.node_results,
                                self.outputs,
                                self.sources,
                                self.sinks,
                                running_node_ids=set(),
                                run_ctx=self.run_ctx
                            )
                            self.error_response.status = "failed"
                            self.error_response.error = {
                                "node_id": completed_node_id,
                                "message": node_result.error.get("message", "Unknown error") if node_result.error else "Unknown error",
                                "trace": node_result.error.get("trace") if node_result.error else None
                            }
                            error_state = self.error_response.model_dump()
                            self.run_ctx.save_state(error_state)
                            break
                        
                        # Mark node as completed (current_running already excludes this node)
                        await self._mark_node_completed(
                            completed_node_id,
                            node_result,
                            output_info,
                            current_running
                        )
                        
                        self.run_ctx.log(f"Node {completed_node_id} completed successfully")
                        
                        # Check children to see if any are now ready
                        children = self.children_map.get(completed_node_id, [])
                        new_ready_nodes = []
                        for child_id in children:
                            # Check if all parents of this child are completed
                            parent_ids = self.parents_map.get(child_id, [])
                            if all(parent_id in self.completed_nodes for parent_id in parent_ids):
                                if child_id not in self.completed_nodes and child_id not in running_tasks:
                                    await ready_queue.put(child_id)
                                    new_ready_nodes.append(child_id)
                                    self.run_ctx.log(f"Node {child_id} is now ready to execute")
                        
                        # Update state after marking children as ready (if any)
                        if new_ready_nodes:
                            await self._update_state(set(running_tasks.keys()))
                    
                    except Exception as e:
                        # Task execution error
                        error_msg = str(e)
                        error_trace = traceback.format_exc()
                        self.run_ctx.log(
                            f"Error processing completed task for node {completed_node_id}: {error_msg}",
                            level="ERROR"
                        )
                        self.run_ctx.log(error_trace, level="ERROR")
                        
                        # Mark node as failed
                        node_result = NodeResult(
                            id=completed_node_id,
                            type=self.node_map[completed_node_id].type.value,
                            status="failed",
                            error={"message": error_msg, "trace": error_trace}
                        )
                        self.failed_node_id = completed_node_id
                        await self._mark_node_completed(
                            completed_node_id,
                            node_result,
                            None,
                            set(running_tasks.keys())
                        )
                        
                        # Build error response
                        self.error_response = build_response_with_all_nodes(
                            self.run_ctx.run_id,
                            self.nodes,
                            self.node_results,
                            self.outputs,
                            self.sources,
                            self.sinks,
                            running_node_ids=set(),
                            run_ctx=self.run_ctx
                        )
                        self.error_response.status = "failed"
                        self.error_response.error = {
                            "node_id": completed_node_id,
                            "message": error_msg,
                            "trace": error_trace
                        }
                        error_state = self.error_response.model_dump()
                        self.run_ctx.save_state(error_state)
                        break
                
                # If we failed, cancel remaining tasks
                if self.failed_node_id:
                    for task in running_tasks.values():
                        task.cancel()
                    break
            
            # Wait for any remaining tasks to complete (in case of early exit)
            if running_tasks:
                # Cancel remaining tasks if we failed
                if self.failed_node_id:
                    for task in running_tasks.values():
                        task.cancel()
                else:
                    # Wait for all remaining tasks
                    await asyncio.gather(*running_tasks.values(), return_exceptions=True)
        
        except Exception as e:
            error_msg = str(e)
            error_trace = traceback.format_exc()
            self.run_ctx.log(f"Orchestrator error: {error_msg}", level="ERROR")
            self.run_ctx.log(error_trace, level="ERROR")
            
            # Build error response
            self.error_response = build_response_with_all_nodes(
                self.run_ctx.run_id,
                self.nodes,
                self.node_results,
                self.outputs,
                self.sources,
                self.sinks,
                running_node_ids=set(),
                run_ctx=self.run_ctx
            )
            self.error_response.status = "failed"
            self.error_response.error = {
                "node_id": None,
                "message": error_msg,
                "trace": error_trace
            }
            error_state = self.error_response.model_dump()
            self.run_ctx.save_state(error_state)
        
        return self.node_results, self.outputs, self.error_response


async def execute_workflow_parallel(
    nodes: List[NodeModel],
    edges: List,
    sources: List[str],
    sinks: List[str],
    run_ctx: RunContext,
    sixtyfour_client: Optional[SixtyfourClient]
) -> Tuple[List[NodeResult], Dict[str, dict], Optional[RunResponse]]:
    """
    Execute workflow nodes in parallel using async orchestration.
    
    Nodes are executed as soon as their parents complete, maximizing throughput.
    
    Returns:
        (node_results, outputs, error_response or None)
    """
    orchestrator = WorkflowOrchestrator(
        nodes, edges, sources, sinks, run_ctx, sixtyfour_client
    )
    return await orchestrator.execute()

