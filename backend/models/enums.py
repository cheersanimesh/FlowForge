"""
Enumerations for workflow types and operators.
"""
from enum import Enum


class BlockType(str, Enum):
    """Supported block types."""
    READ_CSV = "read_csv"
    FILTER = "filter"
    ENRICH_LEAD = "enrich_lead"
    FIND_EMAIL = "find_email"
    SAVE_CSV = "save_csv"


class FilterOperator(str, Enum):
    """Filter operators for rule-based filtering."""
    CONTAINS = "contains"
    EQUALS = "equals"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    IN = "in"
    NOT_NULL = "not_null"
    IS_TRUE = "is_true"
    IS_FALSE = "is_false"

