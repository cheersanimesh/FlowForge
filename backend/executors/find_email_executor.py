"""
Executor for find_email block.
"""
from typing import Optional
import pandas as pd

from models import Block, FindEmailParams
from .base import BlockExecutor, get_params
from core.context import RunContext
from api.sixtyfour_client import SixtyfourClient


class FindEmailExecutor(BlockExecutor):
    """Executor for find_email block."""
    
    def execute(
        self,
        df: Optional[pd.DataFrame],
        block: Block,
        run_ctx: RunContext,
        sixtyfour_client: Optional[SixtyfourClient] = None
    ) -> pd.DataFrame:
        """Find emails by calling Sixtyfour API."""
        if df is None:
            raise ValueError("DataFrame required for find_email block. Ensure read_csv appears first.")
        
        if sixtyfour_client is None:
            raise ValueError("Sixtyfour client required for find_email block")
        
        params = get_params(block, FindEmailParams)
        
        # Validate columns exist
        for csv_col in params.lead_mapping.values():
            if csv_col not in df.columns:
                raise ValueError(f"Column '{csv_col}' not found in DataFrame")
        
        run_ctx.log(f"Finding emails for {len(df)} leads...")
        
        # Process each row
        email_data = []
        for idx, row in df.iterrows():
            try:
                lead_info = {}
                for lead_field, csv_col in params.lead_mapping.items():
                    value = row.get(csv_col)
                    if pd.notna(value) and value != "":
                        lead_info[lead_field] = str(value)
                
                response = sixtyfour_client.find_email(
                    lead_info=lead_info,
                    mode=params.mode
                )
                
                emails = response.get("email", [])
                best_email = emails[0] if emails else None
                
                email_row = {
                    f"{params.output_prefix}best": best_email,
                    f"{params.output_prefix}status": response.get("status"),
                    f"{params.output_prefix}type": response.get("type"),
                    f"{params.output_prefix}confidence": response.get("confidence"),
                }
                
                if "personal_email" in response:
                    email_row[f"{params.output_prefix}personal_email"] = response["personal_email"]
                
                email_data.append(email_row)
                
            except Exception as e:
                run_ctx.log(f"Error finding email for row {idx}: {str(e)}", level="ERROR")
                email_data.append({})
        
        # Merge email data into DataFrame
        email_df = df.copy()
        for idx, email_row in enumerate(email_data):
            for col_name, value in email_row.items():
                email_df.loc[df.index[idx], col_name] = value
        
        run_ctx.log(f"Email finding complete. Added {len([k for k in email_df.columns if k.startswith(params.output_prefix)])} new columns")
        return email_df

