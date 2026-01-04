"""
Filter executor for filtering DataFrame rows.
"""
from typing import Optional
import pandas as pd

from models import Block, FilterParams
from .base import BlockExecutor, get_params
from core.context import RunContext
from api.sixtyfour_client import SixtyfourClient
from filters import FilterExpressionParser, FilterRuleEvaluator


class FilterExecutor(BlockExecutor):
    """Executor for filter block."""
    
    def execute(
        self,
        df: Optional[pd.DataFrame],
        block: Block,
        run_ctx: RunContext,
        sixtyfour_client: Optional[SixtyfourClient] = None
    ) -> pd.DataFrame:
        """Filter DataFrame rows."""
        if df is None:
            raise ValueError("DataFrame required for filter block. Ensure read_csv appears first.")
        
        params = get_params(block, FilterParams)
        
        if params.mode == "rules":
            rules_dict = [rule.model_dump() for rule in params.rules]
            
            # Validate columns exist
            for rule in rules_dict:
                if rule['col'] not in df.columns:
                    raise ValueError(f"Column '{rule['col']}' not found in DataFrame")
            
            mask = FilterRuleEvaluator.evaluate_rules(
                df, rules_dict, params.combine or "and"
            )
        elif params.mode == "expr":
            mask = FilterExpressionParser.parse_and_evaluate(df, params.expr)
        else:
            raise ValueError(f"Invalid filter mode: {params.mode}")
        
        filtered_df = df[mask].copy()
        run_ctx.log(f"Filtered from {len(df)} to {len(filtered_df)} rows")
        return filtered_df

