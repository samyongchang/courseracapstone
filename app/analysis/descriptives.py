from __future__ import annotations
from typing import List
import pandas as pd
import numpy as np


def _describe_numeric(series: pd.Series) -> pd.Series:
    clean = pd.to_numeric(series, errors="coerce")
    desc = {
        "Count": int(clean.count()),
        "Mean": float(clean.mean()),
        "Std": float(clean.std(ddof=1)) if clean.count() > 1 else float("nan"),
        "Min": float(clean.min()),
        "25%": float(clean.quantile(0.25)),
        "50%": float(clean.quantile(0.50)),
        "75%": float(clean.quantile(0.75)),
        "Max": float(clean.max()),
    }
    return pd.Series(desc)


def _describe_categorical(series: pd.Series) -> pd.Series:
    counts = series.astype(str).replace({"nan": np.nan}).value_counts(dropna=False)
    top = counts.index[0] if len(counts) else np.nan
    freq = int(counts.iloc[0]) if len(counts) else 0
    return pd.Series({
        "Count": int(series.size - series.isna().sum()),
        "Unique": int(series.nunique(dropna=True)),
        "Top": top,
        "Freq": freq,
    })


def run_descriptives(df: pd.DataFrame, variables: List[str]) -> str:
    frames: list[pd.DataFrame] = []
    for var in variables:
        s = df[var]
        if pd.api.types.is_numeric_dtype(s):
            stats = _describe_numeric(s)
        else:
            stats = _describe_categorical(s)
        frames.append(stats.to_frame(name=var))

    result = pd.concat(frames, axis=1)

    style = """
    <style>
      table { border-collapse: collapse; font-family: Arial, sans-serif; font-size: 13px; }
      th, td { border: 1px solid #ccc; padding: 6px 8px; text-align: right; }
      th { background: #f5f5f5; text-align: center; }
      caption { text-align: left; font-weight: bold; margin-bottom: 8px; }
    </style>
    """
    html = result.to_html(classes="statx-table", border=0, justify="right")
    return f"{style}<div><h3>Descriptive Statistics</h3>{html}</div>"
