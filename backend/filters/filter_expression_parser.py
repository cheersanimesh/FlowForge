"""
Parser for simple filter expressions.
"""
import pandas as pd
import re


class FilterExpressionParser:
    """Parser for simple filter expressions."""
    
    # Pattern: <col> contains '<text>' or <col> equals '<text>'
    EXPR_PATTERN = re.compile(
        r'^(\w+)\s+(contains|equals)\s+[\'"](.+?)[\'"]$',
        re.IGNORECASE
    )
    
    @staticmethod
    def parse_and_evaluate(df: pd.DataFrame, expr: str) -> pd.Series:
        """
        Parse a simple expression and return a boolean Series.
        
        Supported formats:
        - "<col> contains '<text>'"
        - "<col> equals '<text>'"
        
        Args:
            df: DataFrame to filter
            expr: Expression string
            
        Returns:
            Boolean Series indicating which rows match
            
        Raises:
            ValueError: If expression is invalid or column doesn't exist
        """
        expr = expr.strip()
        match = FilterExpressionParser.EXPR_PATTERN.match(expr)
        
        if not match:
            raise ValueError(
                f"Invalid expression format: {expr}. "
                "Supported: '<col> contains \"<text>\"' or '<col> equals \"<text>\"'"
            )
        
        col_name, operator, value = match.groups()
        col_name = col_name.strip()
        operator = operator.lower()
        value = value.strip()
        
        if col_name not in df.columns:
            raise ValueError(f"Column '{col_name}' not found in DataFrame")
        
        # Get column as string series (handle NaN)
        col_series = df[col_name].astype(str).str.lower()
        value_lower = value.lower()
        
        if operator == "contains":
            return col_series.str.contains(value_lower, na=False, regex=False)
        elif operator == "equals":
            return col_series == value_lower
        else:
            raise ValueError(f"Unsupported operator: {operator}")

