"""
Utility functions for context operations.
"""
import re


def sanitize_id(node_id: str) -> str:
    """
    Sanitize node ID for filesystem use.
    Allow [a-zA-Z0-9_-], replace others with underscore.
    """
    return re.sub(r'[^a-zA-Z0-9_-]', '_', node_id)

