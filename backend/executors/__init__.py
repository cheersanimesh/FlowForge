"""
Executor registry for workflow blocks.
"""
from models import BlockType
from core.context import RunContext
from .base import BlockExecutor
from .csv_executors import ReadCsvExecutor, SaveCsvExecutor
from .filter_executor import FilterExecutor
from .enrich_lead_executor import EnrichLeadExecutor
from .find_email_executor import FindEmailExecutor

# Registry of executors
EXECUTOR_REGISTRY = {
    BlockType.READ_CSV: ReadCsvExecutor(),
    BlockType.FILTER: FilterExecutor(),
    BlockType.ENRICH_LEAD: EnrichLeadExecutor(),
    BlockType.FIND_EMAIL: FindEmailExecutor(),
    BlockType.SAVE_CSV: SaveCsvExecutor(),
}

__all__ = [
    "RunContext",
    "BlockExecutor",
    "EXECUTOR_REGISTRY",
    "ReadCsvExecutor",
    "SaveCsvExecutor",
    "FilterExecutor",
    "EnrichLeadExecutor",
    "FindEmailExecutor",
]

