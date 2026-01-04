"""
Parameter models for workflow blocks.
"""
from typing import Optional, Literal, Dict, List, Union
from pydantic import BaseModel, Field, field_validator


class FilterRule(BaseModel):
    """A single filter rule."""
    col: str = Field(..., description="Column name to filter on")
    op: str = Field(..., description="Operator to use")
    value: Optional[Union[str, List[str]]] = Field(None, description="Value to compare against")


class FilterParams(BaseModel):
    """Parameters for filter block."""
    mode: Literal["rules", "expr"] = Field("rules", description="Filter mode: 'rules' or 'expr'")
    rules: Optional[List[FilterRule]] = Field(None, description="Rules for rule-based filtering")
    combine: Optional[Literal["and", "or"]] = Field("and", description="How to combine rules")
    expr: Optional[str] = Field(None, description="Simple expression for expr mode")

    @field_validator('rules', mode='before')
    @classmethod
    def validate_rules(cls, v, info):
        """Ensure rules are provided when mode is 'rules'."""
        if info.data.get('mode') == 'rules' and not v:
            raise ValueError("rules must be provided when mode is 'rules'")
        return v

    @field_validator('expr', mode='before')
    @classmethod
    def validate_expr(cls, v, info):
        """Ensure expr is provided when mode is 'expr'."""
        if info.data.get('mode') == 'expr' and not v:
            raise ValueError("expr must be provided when mode is 'expr'")
        return v


class ReadCsvParams(BaseModel):
    """Parameters for read_csv block."""
    path: str = Field(..., description="Path to CSV file (relative or absolute)")


class EnrichLeadParams(BaseModel):
    """Parameters for enrich_lead block."""
    lead_mapping: Dict[str, str] = Field(..., description="Mapping from lead fields to CSV columns")
    struct: Dict[str, str] = Field(..., description="Structured data fields with instructions")
    research_plan: Optional[str] = Field(None, description="Optional research plan")
    output_prefix: str = Field("enrich_", description="Prefix for output columns")


class FindEmailParams(BaseModel):
    """Parameters for find_email block."""
    lead_mapping: Dict[str, str] = Field(..., description="Mapping from lead fields to CSV columns")
    mode: Literal["PROFESSIONAL", "PERSONAL"] = Field("PROFESSIONAL", description="Email search mode")
    output_prefix: str = Field("email_", description="Prefix for output columns")


class SaveCsvParams(BaseModel):
    """Parameters for save_csv block."""
    path: Optional[str] = Field(None, description="Output path (defaults to runs/{run_id}/output.csv)")

