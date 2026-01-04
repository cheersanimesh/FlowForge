"""
Executor for enrich_lead block.
"""
from typing import Optional, Dict, List
import pandas as pd
import time

from models import Block, EnrichLeadParams
from .base import BlockExecutor, get_params
from core.context import RunContext
from api.sixtyfour_client import SixtyfourClient


class EnrichLeadExecutor(BlockExecutor):
    """Executor for enrich_lead block."""
    
    def _update_node_status(self, run_ctx: RunContext, block: Block, status: str, message: str = "", progress: Optional[float] = None):
        """Update the node status in the state file."""
        try:
            state = run_ctx.load_state()
            if state and state.get("nodes"):
                for node in state["nodes"]:
                    if node.get("id") == block.id:
                        node["status"] = status
                        if progress is not None:
                            node["progress"] = progress
                        if message:
                            run_ctx.log(message)
                        run_ctx.save_state(state)
                        break
        except Exception as e:
            run_ctx.log(f"Error updating node status: {str(e)}", level="ERROR")
    
    def execute(
        self,
        df: Optional[pd.DataFrame],
        block: Block,
        run_ctx: RunContext,
        sixtyfour_client: Optional[SixtyfourClient] = None
    ) -> pd.DataFrame:
        """Enrich leads by calling Sixtyfour API async endpoint."""
        
        if df is None:
            raise ValueError("DataFrame required for enrich_lead block. Ensure read_csv appears first.")
        
        if sixtyfour_client is None:
            raise ValueError("Sixtyfour client required for enrich_lead block")
        
        params = get_params(block, EnrichLeadParams)
        
        # Validate columns exist
        for csv_col in params.lead_mapping.values():
            if csv_col not in df.columns:
                raise ValueError(f"Column '{csv_col}' not found in DataFrame")
        
        run_ctx.log(f"Starting async enrichment for {len(df)} leads...")
        self._update_node_status(run_ctx, block, "running", "Starting async enrichment jobs...", progress=0.0)
        
        # Step 1: Submit async jobs for all rows
        task_ids: Dict[int, str] = {}  # Map row index to task_id
        
        for idx, row in df.iterrows():
            try:
                lead_info = {}
                
                for lead_field, csv_col in params.lead_mapping.items():
                    value = row.get(csv_col)
                    if pd.notna(value) and value != "":
                        lead_info[lead_field] = str(value)
                
                # Submit async job
                response = sixtyfour_client.enrich_lead_async(
                    lead_info=lead_info,
                    struct=params.struct,
                    research_plan=params.research_plan
                )
                
                task_id = response.get("task_id")
                if task_id:
                    task_ids[idx] = task_id
                    run_ctx.log(f"Submitted async job for row {idx}, task_id: {task_id}")
                else:
                    run_ctx.log(f"Failed to get task_id for row {idx}", level="ERROR")
                    
            except Exception as e:
                run_ctx.log(f"Error submitting async job for row {idx}: {str(e)}", level="ERROR")
        
        if not task_ids:
            raise ValueError("Failed to submit any async jobs")
        
        run_ctx.log(f"Submitted {len(task_ids)} async jobs. Polling for completion...")
        self._update_node_status(run_ctx, block, "running", f"Polling {len(task_ids)} async jobs...", progress=0.0)
        
        # Step 2: Poll for job status
        poll_interval = 10  # seconds
        max_poll_time = 15 * 60  # 15 minutes max
        start_time = time.time()
        
        completed_jobs: Dict[int, Dict] = {}  # Map row index to result
        failed_jobs: List[int] = []
        
        while len(completed_jobs) + len(failed_jobs) < len(task_ids):
            if time.time() - start_time > max_poll_time:
                run_ctx.log(f"Polling timeout after {max_poll_time} seconds", level="ERROR")
                break
            
            for idx, task_id in task_ids.items():
                if idx in completed_jobs or idx in failed_jobs:
                    continue
                
                try:
                    status_response = sixtyfour_client.get_job_status(task_id)
                    status = status_response.get("status")
                    
                    if status == "completed":
                        result = status_response.get("result", {})
                        completed_jobs[idx] = result
                        run_ctx.log(f"Job completed for row {idx}, task_id: {task_id}")
                    elif status == "failed":
                        error_msg = status_response.get("error", "Unknown error")
                        run_ctx.log(f"Job failed for row {idx}, task_id: {task_id}: {error_msg}", level="ERROR")
                        failed_jobs.append(idx)
                    # If status is "pending" or "processing", continue polling
                    
                except Exception as e:
                    run_ctx.log(f"Error checking status for row {idx}, task_id: {task_id}: {str(e)}", level="ERROR")
            
            # Update status with progress
            completed_count = len(completed_jobs) + len(failed_jobs)
            total_count = len(task_ids)
            progress_percentage = (completed_count / total_count * 100) if total_count > 0 else 0.0
            progress_msg = f"Progress: {completed_count}/{total_count} jobs completed ({progress_percentage:.1f}%)"
            run_ctx.log(progress_msg)
            self._update_node_status(run_ctx, block, "running", progress_msg, progress=progress_percentage)
            
            # If not all jobs are done, wait before next poll
            if completed_count < total_count:
                time.sleep(poll_interval)
        
        run_ctx.log(f"Polling complete. {len(completed_jobs)} completed, {len(failed_jobs)} failed")
        
        # Step 3: Process completed results
        enriched_data = []
        
        for idx in df.index:
            if idx in completed_jobs:
                try:
                    result = completed_jobs[idx]
                    structured_data = result.get("structured_data", {})
                    enriched_row = {}
                    for field_name, field_value in structured_data.items():
                        col_name = f"{params.output_prefix}{field_name}"
                        enriched_row[col_name] = field_value
                    enriched_data.append(enriched_row)
                except Exception as e:
                    run_ctx.log(f"Error processing result for row {idx}: {str(e)}", level="ERROR")
                    enriched_data.append({})
            elif idx in failed_jobs:
                run_ctx.log(f"Skipping row {idx} due to failed job")
                enriched_data.append({})
            else:
                run_ctx.log(f"Row {idx} did not complete within timeout", level="ERROR")
                enriched_data.append({})
        
        # Merge enriched data into DataFrame
        enriched_df = df.copy()
        for idx, enriched_row in enumerate(enriched_data):
            df_idx = df.index[idx]
            for col_name, value in enriched_row.items():
                enriched_df.loc[df_idx, col_name] = value
        
        new_columns = [k for k in enriched_df.columns if k.startswith(params.output_prefix)]
        run_ctx.log(f"Enrichment complete. Added {len(new_columns)} new columns")
        self._update_node_status(run_ctx, block, "success", f"Enrichment complete. Added {len(new_columns)} new columns", progress=100.0)
        
        return enriched_df

