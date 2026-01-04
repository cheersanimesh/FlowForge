"""
Evaluator for rule-based filters.
"""
import pandas as pd


class FilterRuleEvaluator:
    """Evaluator for rule-based filters."""
    
    @staticmethod
    def evaluate_rule(df: pd.DataFrame, rule: dict) -> pd.Series:
        """
        Evaluate a single filter rule.
        
        Args:
            df: DataFrame to filter
            rule: Rule dict with 'col', 'op', and optionally 'value'
            
        Returns:
            Boolean Series indicating which rows match the rule
        """
        col = rule['col']
        op_str = rule['op']
        value = rule.get('value')
        
        if col not in df.columns:
            raise ValueError(f"Column '{col}' not found in DataFrame")
        
        col_series = df[col]
        
        if op_str == "not_null":
            return col_series.notna()
        elif op_str == "is_true":
            return col_series == True
        elif op_str == "is_false":
            return col_series == False
        elif op_str == "contains":
            if value is None:
                raise ValueError("value required for 'contains' operator")
            return col_series.astype(str).str.contains(str(value), na=False, regex=False, case=False)
        elif op_str == "equals":
            if value is None:
                raise ValueError("value required for 'equals' operator")
            return col_series.astype(str).str.lower() == str(value).lower()
        elif op_str == "starts_with":
            if value is None:
                raise ValueError("value required for 'starts_with' operator")
            return col_series.astype(str).str.startswith(str(value), na=False)
        elif op_str == "ends_with":
            if value is None:
                raise ValueError("value required for 'ends_with' operator")
            return col_series.astype(str).str.endswith(str(value), na=False)
        elif op_str == "in":
            if value is None:
                raise ValueError("value required for 'in' operator")
            if not isinstance(value, list):
                raise ValueError("value must be a list for 'in' operator")
            return col_series.isin(value)
        else:
            raise ValueError(f"Unsupported operator: {op_str}")
    
    @staticmethod
    def evaluate_rules(
        df: pd.DataFrame,
        rules: list,
        combine: str = "and"
    ) -> pd.Series:
        """
        Evaluate multiple rules and combine them.
        
        Args:
            df: DataFrame to filter
            rules: List of rule dicts
            combine: How to combine rules ('and' or 'or')
            
        Returns:
            Boolean Series indicating which rows match all/any rules
        """
        if not rules:
            return pd.Series([True] * len(df), index=df.index)
        
        results = []
        for rule in rules:
            results.append(FilterRuleEvaluator.evaluate_rule(df, rule))
        
        if combine == "and":
            combined = results[0]
            for r in results[1:]:
                combined = combined & r
            return combined
        elif combine == "or":
            combined = results[0]
            for r in results[1:]:
                combined = combined | r
            return combined
        else:
            raise ValueError(f"Invalid combine mode: {combine}. Must be 'and' or 'or'")

