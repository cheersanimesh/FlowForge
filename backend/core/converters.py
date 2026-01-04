"""
Conversion utilities for workflow formats.
"""
from models import (
    Block, NodeModel, EdgeModel, BlockType,
    ReadCsvParams, FilterParams, EnrichLeadParams,
    FindEmailParams, SaveCsvParams
)


def convert_blocks_to_dag(blocks: list[Block]) -> tuple[list[NodeModel], list[EdgeModel]]:
    """
    Convert legacy blocks format to DAG format (nodes + edges).
    
    Args:
        blocks: List of blocks in sequential order
        
    Returns:
        Tuple of (nodes, edges) representing a linear chain
    """
    nodes = []
    edges = []
    
    for block in blocks:
        # Convert Block to NodeModel
        node = NodeModel(
            id=block.id,
            type=block.type,
            params=block.params if isinstance(block.params, dict) 
                else block.params.model_dump() if hasattr(block.params, "model_dump") 
                else dict(block.params)
        )
        nodes.append(node)
        
        # Create edge from previous block to current (if not first)
        if len(nodes) > 1:
            prev_node_id = blocks[len(nodes) - 2].id
            edges.append(EdgeModel(from_=prev_node_id, to=block.id))
    
    return nodes, edges


def convert_node_to_block(node: NodeModel) -> Block:
    """
    Convert NodeModel to Block for executor compatibility.
    
    Args:
        node: NodeModel instance
        
    Returns:
        Block instance with properly typed params
    """
    # Map block types to their corresponding param classes
    param_class_map = {
        BlockType.READ_CSV: ReadCsvParams,
        BlockType.FILTER: FilterParams,
        BlockType.ENRICH_LEAD: EnrichLeadParams,
        BlockType.FIND_EMAIL: FindEmailParams,
        BlockType.SAVE_CSV: SaveCsvParams,
    }
    
    # Get the appropriate param class for this block type
    param_class = param_class_map.get(node.type)
    
    if param_class is None:
        raise ValueError(f"Unknown block type: {node.type}")
    
    # Convert dict params to typed param model
    if isinstance(node.params, dict):
        params = param_class(**node.params)
    elif isinstance(node.params, param_class):
        # Already the correct type
        params = node.params
    else:
        # Try to convert from other param types
        if hasattr(node.params, "model_dump"):
            params = param_class(**node.params.model_dump())
        else:
            params = param_class(**dict(node.params))
    
    return Block(
        id=node.id,
        type=node.type,
        params=params
    )

