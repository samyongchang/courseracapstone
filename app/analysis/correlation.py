from __future__ import annotations
from typing import Literal
import pandas as pd


def run_correlation(df: pd.DataFrame, method: Literal["pearson", "spearman"] = "pearson") -> str:
    numeric_df = df.select_dtypes(include=["number"]).copy()
    corr = numeric_df.corr(method=method)

    style = """
    <style>
      table { border-collapse: collapse; font-family: Arial, sans-serif; font-size: 13px; }
      th, td { border: 1px solid #ccc; padding: 6px 8px; text-align: right; }
      th { background: #f5f5f5; text-align: center; }
      caption { text-align: left; font-weight: bold; margin-bottom: 8px; }
    </style>
    """
    html = corr.to_html(classes="statx-table", border=0, justify="right")
    return f"{style}<div><h3>Correlation Matrix ({method.title()})</h3>{html}</div>"
