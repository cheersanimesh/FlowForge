"""
Run context for workflow execution, managing state and file I/O.
"""
import json
from typing import Optional
from pathlib import Path
import pandas as pd

from .context_utils import sanitize_id


class RunContext:
    """Context for a workflow run, managing state and file I/O."""
    
    def __init__(self, run_id: str, workspace_dir: str):
        """Initialize run context."""
        self.run_id = run_id
        self.workspace_dir = Path(workspace_dir) / run_id
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.workspace_dir / "logs.jsonl"
        self.state_file = self.workspace_dir / "state.json"
        self.block_results = []
    
    def log(self, message: str, level: str = "INFO"):
        """Write a log entry to logs.jsonl."""
        log_entry = {
            "timestamp": pd.Timestamp.now().isoformat(),
            "level": level,
            "message": message
        }
        with open(self.log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    
    def save_preview(self, df: pd.DataFrame, block_id: str, step_index: Optional[int] = None) -> str:
        """Save a preview (head 20 rows) as JSON. Returns absolute path."""
        sanitized_id_val = sanitize_id(block_id)
        if step_index is not None:
            preview_path = self.workspace_dir / f"preview_{step_index}_{sanitized_id_val}.json"
        else:
            preview_path = self.workspace_dir / f"preview_{sanitized_id_val}.json"
        
        preview_df = df.head(20)
        preview_data = {
            "rows": len(df),
            "columns": list(df.columns),
            "preview": preview_df.to_dict(orient="records")
        }
        with open(preview_path, "w") as f:
            json.dump(preview_data, f, indent=2, default=str)
        # Return absolute path
        return str(preview_path.resolve())
    
    def save_parquet(
        self, 
        df: pd.DataFrame, 
        step_index: Optional[int] = None, 
        block_type: Optional[str] = None, 
        node_id: Optional[str] = None
    ) -> str:
        """Save DataFrame as parquet."""
        if node_id is not None:
            sanitized_id_val = sanitize_id(node_id)
            parquet_path = self.workspace_dir / f"node_{sanitized_id_val}.parquet"
        else:
            parquet_path = self.workspace_dir / f"step_{step_index}_{block_type}.parquet"
        df.to_parquet(parquet_path, index=False)
        return str(parquet_path)
    
    def load_parquet(self, node_id: str) -> pd.DataFrame:
        """Load a parquet file for a node."""
        sanitized_id_val = sanitize_id(node_id)
        parquet_path = self.workspace_dir / f"node_{sanitized_id_val}.parquet"
        if not parquet_path.exists():
            raise FileNotFoundError(f"Parquet file not found for node {node_id}: {parquet_path}")
        return pd.read_parquet(parquet_path)
    
    def save_state(self, state: dict):
        """Save workflow execution state to state.json."""
        with open(self.state_file, "w") as f:
            json.dump(state, f, indent=2, default=str)
    
    def load_state(self) -> Optional[dict]:
        """Load workflow execution state from state.json and normalize paths to absolute."""
        if not self.state_file.exists():
            return None
        with open(self.state_file, "r") as f:
            state = json.load(f)
        
        # Normalize preview_path and output_csv_path to absolute paths
        if state.get("nodes"):
            for node in state["nodes"]:
                if node.get("preview_path"):
                    preview_path = Path(node["preview_path"])
                    if not preview_path.is_absolute():
                        # If relative, resolve relative to workspace_dir
                        node["preview_path"] = str((self.workspace_dir / preview_path).resolve())
                    else:
                        node["preview_path"] = str(preview_path.resolve())
        
        # Normalize output_csv_path in outputs
        if state.get("outputs"):
            for node_id, output_info in state["outputs"].items():
                if "output_csv_path" in output_info:
                    output_path = Path(output_info["output_csv_path"])
                    if not output_path.is_absolute():
                        output_info["output_csv_path"] = str(output_path.resolve())
                    else:
                        output_info["output_csv_path"] = str(output_path.resolve())
        
        return state

