"""
DataFrame loading and merging utilities for workflows.
"""
from typing import Optional
import pandas as pd

from core.context import RunContext


def load_input_dataframe(parent_ids: list[str], run_ctx: RunContext) -> Optional[pd.DataFrame]:
    """
    Load input DataFrame from parent nodes.
    
    Supports single parent (direct load) or multiple parents (merge).
    """
    if not parent_ids:
        return None
    
    if len(parent_ids) == 1:
        parent_id = parent_ids[0]
        df_in = run_ctx.load_parquet(parent_id)
        run_ctx.log(f"Loaded {len(df_in)} rows from parent node {parent_id}")
        return df_in
    
    # Multiple parents - merge DataFrames on index (inner join)
    parent_dfs = []
    for parent_id in parent_ids:
        parent_df = run_ctx.load_parquet(parent_id)
        parent_dfs.append((parent_id, parent_df))
        run_ctx.log(f"Loaded {len(parent_df)} rows from parent node {parent_id}")
    
    df_in = parent_dfs[0][1]  # Start with first DataFrame
    for parent_id, parent_df in parent_dfs[1:]:
        df_in = df_in.merge(parent_df, left_index=True, right_index=True, how='inner')
        run_ctx.log(f"Merged with parent node {parent_id}: {len(df_in)} rows after merge")
    
    run_ctx.log(f"Final merged DataFrame has {len(df_in)} rows from {len(parent_ids)} parents")
    return df_in

