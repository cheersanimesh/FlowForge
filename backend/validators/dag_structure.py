"""
DAG structure utilities (topological sort, adjacency lists).
"""
from typing import List, Dict, Tuple
from collections import defaultdict, deque

from models import NodeModel, EdgeModel


def build_adjacency_list(
    nodes: List[NodeModel], 
    edges: List[EdgeModel]
) -> Tuple[Dict[str, List[str]], Dict[str, int]]:
    """
    Build adjacency list and indegree map from nodes and edges.
    
    Returns:
        Tuple of (adjacency_list, indegree_map)
    """
    adjacency_list = defaultdict(list)
    indegree_map = defaultdict(int)
    
    # Initialize indegree for all nodes
    for node in nodes:
        indegree_map[node.id] = 0
    
    # Build adjacency list and count indegrees
    for edge in edges:
        adjacency_list[edge.from_].append(edge.to)
        indegree_map[edge.to] += 1
    
    return dict(adjacency_list), dict(indegree_map)


def topological_sort(
    nodes: List[NodeModel], 
    edges: List[EdgeModel]
) -> Tuple[List[str], List[str]]:
    """
    Perform topological sort using Kahn's algorithm.
    
    Returns:
        Tuple of (sorted_node_ids, cycle_nodes) - if cycle_nodes is non-empty, there's a cycle
    """
    # Validate all edge references
    node_ids = {node.id for node in nodes}
    for edge in edges:
        if edge.from_ not in node_ids:
            raise ValueError(f"Edge references unknown source node: {edge.from_}")
        if edge.to not in node_ids:
            raise ValueError(f"Edge referednces unknown target node: {edge.to}")
    
    adjacency_list, indegree_map = build_adjacency_list(nodes, edges)
    
    # Find all sources (indegree 0)
    queue = deque([node_id for node_id, indegree in indegree_map.items() if indegree == 0])
    sorted_nodes = []
    processed_count = 0
    
    while queue:
        node_id = queue.popleft()
        sorted_nodes.append(node_id)
        processed_count += 1
        
        # Reduce indegree of neighbors
        for neighbor in adjacency_list.get(node_id, []):
            indegree_map[neighbor] -= 1
            if indegree_map[neighbor] == 0:
                queue.append(neighbor)
    
    # If not all nodes processed, there's a cycle
    if processed_count != len(nodes):
        remaining = [node_id for node_id in node_ids if node_id not in sorted_nodes]
        return sorted_nodes, remaining
    else:
        return sorted_nodes, []

