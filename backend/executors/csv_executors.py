"""
CSV-related executors (read_csv, save_csv).
"""
from typing import Optional
from pathlib import Path
import pandas as pd

from models import Block, ReadCsvParams, SaveCsvParams
from .base import BlockExecutor, get_params
from core.context import RunContext
from api.sixtyfour_client import SixtyfourClient


class ReadCsvExecutor(BlockExecutor):
    """Executor for read_csv block."""
    
    def execute(
        self,
        df: Optional[pd.DataFrame],
        block: Block,
        run_ctx: RunContext,
        sixtyfour_client: Optional[SixtyfourClient] = None
    ) -> pd.DataFrame:
        """
        Load CSV file into DataFrame.
        
        The path can be:
        - A relative path (e.g., "uploads/uuid.csv" or "input.csv") - resolved relative to backend working directory
        - An absolute path - used as-is
        
        This works correctly even when frontend and backend are on different servers,
        since the workflow executes on the backend.
        """
        params = get_params(block, ReadCsvParams)
        path = Path(params.path)
        
        # If path is relative, resolve it relative to current working directory (backend's working dir)
        if not path.is_absolute():
            path = Path.cwd() / path
        
        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {params.path} (resolved to: {path})")
        
        run_ctx.log(f"Reading CSV from {params.path}")
        df = pd.read_csv(path)
        run_ctx.log(f"Loaded {len(df)} rows, {len(df.columns)} columns")
        return df


class SaveCsvExecutor(BlockExecutor):
    """Executor for save_csv block."""
    
    def execute(
        self,
        df: Optional[pd.DataFrame],
        block: Block,
        run_ctx: RunContext,
        sixtyfour_client: Optional[SixtyfourClient] = None
    ) -> pd.DataFrame:
        """Save DataFrame to CSV."""
        if df is None:
            raise ValueError("DataFrame required for save_csv block. Ensure read_csv appears first.")
        
        params = get_params(block, SaveCsvParams)
        
        if params.path:
            output_path = Path(params.path)
            output_path = Path(str(output_path).replace("{run_id}", run_ctx.run_id))
        else:
            output_path = run_ctx.workspace_dir / "output.csv"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        run_ctx.log(f"Saving CSV to {output_path}")
        df.to_csv(output_path, index=False)
        run_ctx.log(f"Saved {len(df)} rows to {output_path}")
        
        return df  # Return unchanged DataFrame