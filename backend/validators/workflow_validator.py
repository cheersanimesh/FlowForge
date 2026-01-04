"""
Workflow validation logic for legacy blocks format.
"""
from typing import List
from pathlib import Path

from models import WorkflowSpec, BlockType


class WorkflowValidator:
    """Validates workflow specifications."""
    
    @staticmethod
    def validate(spec: WorkflowSpec) -> List[str]:
        """
        Validate workflow specification (legacy blocks format only).
        For DAG format, use DAGValidator.validate_dag().
        
        Args:
            spec: Workflow specification
            
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        # Only validate if using legacy blocks format
        if spec.blocks is None or len(spec.blocks) == 0:
            return errors
        
        if not spec.blocks:
            errors.append("Workflow must have at least one block")
            return errors
        
        # Track which blocks require DataFrame
        dataframe_required_blocks = {
            BlockType.FILTER,
            BlockType.ENRICH_LEAD,
            BlockType.FIND_EMAIL,
            BlockType.SAVE_CSV
        }
        
        # Find read_csv block
        read_csv_index = None
        for i, block in enumerate(spec.blocks):
            if block.type == BlockType.READ_CSV:
                read_csv_index = i
                break
        
        # Validate read_csv appears before blocks that need DataFrame
        if read_csv_index is None:
            for i, block in enumerate(spec.blocks):
                if block.type in dataframe_required_blocks:
                    errors.append(
                        f"Block '{block.id}' (type: {block.type}) requires a DataFrame, "
                        "but no read_csv block found before it"
                    )
        else:
            # Check that blocks requiring DataFrame come after read_csv
            for i, block in enumerate(spec.blocks):
                if block.type in dataframe_required_blocks and i < read_csv_index:
                    errors.append(
                        f"Block '{block.id}' (type: {block.type}) requires a DataFrame, "
                        f"but appears before read_csv block at index {read_csv_index}"
                    )
        
        # Validate read_csv file exists (if path provided)
        for block in spec.blocks:
            if block.type == BlockType.READ_CSV:
                try:
                    params = block.params
                    path = params.get("path") if isinstance(params, dict) else (
                        params.path if hasattr(params, "path") else None
                    )
                    
                    if path and not Path(path).exists():
                        errors.append(f"CSV file not found: {path}")
                except Exception as e:
                    errors.append(f"Error validating read_csv block '{block.id}': {str(e)}")
        
        return errors

