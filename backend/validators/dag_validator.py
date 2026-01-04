"""
DAG validation logic for nodes and edges format.
"""
from typing import List, Tuple

from models import NodeModel, EdgeModel, BlockType
from .dag_structure import build_adjacency_list, topological_sort


class DAGValidator:
    """Validates DAG structure and properties."""
    
    @staticmethod
    def build_adjacency_list(
        nodes: List[NodeModel], 
        edges: List[EdgeModel]
    ) -> Tuple[dict, dict]:
        """Build adjacency list and indegree map from nodes and edges."""
        return build_adjacency_list(nodes, edges)
    
    @staticmethod
    def topological_sort(
        nodes: List[NodeModel], 
        edges: List[EdgeModel]
    ) -> Tuple[List[str], List[str]]:
        """Perform topological sort using Kahn's algorithm."""
        return topological_sort(nodes, edges)
    
    @staticmethod
    def validate_dag(nodes: List[NodeModel], edges: List[EdgeModel]) -> List[str]:
        """
        Validate DAG structure and constraints.
        
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        # Check unique node IDs
        node_ids = [node.id for node in nodes]
        if len(node_ids) != len(set(node_ids)):
            duplicates = [nid for nid in node_ids if node_ids.count(nid) > 1]
            errors.append(f"Duplicate node IDs found: {set(duplicates)}")
            return errors
        
        # Validate edge references
        node_id_set = set(node_ids)
        for edge in edges:
            if edge.from_ not in node_id_set:
                errors.append(f"Edge references unknown source node: {edge.from_}")
            if edge.to not in node_id_set:
                errors.append(f"Edge references unknown target node: {edge.to}")
        
        if errors:
            return errors
        
        # Check for cycles
        try:
            sorted_nodes, cycle_nodes = topological_sort(nodes, edges)
            if cycle_nodes:
                errors.append(f"Cycle detected in DAG. Nodes in cycle: {cycle_nodes}")
        except ValueError as e:
            errors.append(str(e))
        
        if errors:
            return errors
        
        # Validate source nodes (indegree 0) - only read_csv allowed
        _, indegree_map = build_adjacency_list(nodes, edges)
        source_nodes = [node_id for node_id, indegree in indegree_map.items() if indegree == 0]
        for node_id in source_nodes:
            node = next(n for n in nodes if n.id == node_id)
            if node.type != BlockType.READ_CSV:
                errors.append(
                    f"Source node '{node_id}' has type '{node.type}', "
                    "but only 'read_csv' is allowed as a source"
                )
        
        return errors
    
    @staticmethod
    def get_sources_and_sinks(
        nodes: List[NodeModel], 
        edges: List[EdgeModel]
    ) -> Tuple[List[str], List[str]]:
        """Get source nodes (indegree 0) and sink nodes (outdegree 0)."""
        adjacency_list, indegree_map = build_adjacency_list(nodes, edges)
        sources = [node_id for node_id, indegree in indegree_map.items() if indegree == 0]
        all_node_ids = {node.id for node in nodes}
        sinks = [
            node_id for node_id in all_node_ids
            if node_id not in adjacency_list or len(adjacency_list[node_id]) == 0
        ]
        return sources, sinks
