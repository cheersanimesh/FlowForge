"""
Base executor class and utilities.
"""
from typing import Optional
import pandas as pd

from models import Block
from core.context import RunContext
from api.sixtyfour_client import SixtyfourClient


def get_params(block: Block, param_class):
    """
    Safely extract and parse params from a block.
    
    Args:
        block: Block instance
        param_class: Pydantic model class for params
        
    Returns:
        Parsed params instance
        
    Raises:
        ValueError: If params cannot be parsed or are invalid
    """
    try:
        if isinstance(block.params, param_class):
            return block.params
        elif isinstance(block.params, dict):
            return param_class(**block.params)
        else:
            if hasattr(block.params, "model_dump"):
                return param_class(**block.params.model_dump())
            else:
                return param_class(**dict(block.params))
    except Exception as e:
        error_msg = (
            f"Failed to parse params for block '{block.id}' (type: {block.type}). "
            f"Expected {param_class.__name__}, but got params: {block.params}. "
            f"Error: {str(e)}"
        )
        raise ValueError(error_msg) from e


class BlockExecutor:
    """Base class for block executors."""
    
    def execute(
        self,
        df: Optional[pd.DataFrame],
        block: Block,
        run_ctx: RunContext,
        sixtyfour_client: Optional[SixtyfourClient] = None
    ) -> pd.DataFrame:
        """
        Execute the block.
        
        Args:
            df: Input DataFrame (None for read_csv)
            block: Block definition
            run_ctx: Run context
            sixtyfour_client: Sixtyfour API client (for enrich/find blocks)
            
        Returns:
            Output DataFrame
            
        Raises:
            Exception: If execution fails
        """
        raise NotImplementedError

