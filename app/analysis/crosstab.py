from __future__ import annotations
from typing import List
import pandas as pd
import numpy as np
try:
    from scipy.stats import chi2_contingency  # type: ignore
    _HAS_SCIPY = True
except Exception:  # noqa: BLE001
    chi2_contingency = None  # type: ignore
    _HAS_SCIPY = False


def format_html_table(title: str, df: pd.DataFrame, footnotes: list[str] | None = None) -> str:
    style = """
    <style>
      table { border-collapse: collapse; font-family: Arial, sans-serif; font-size: 13px; }
      th, td { border: 1px solid #ccc; padding: 6px 8px; text-align: right; }
      th { background: #f5f5f5; text-align: center; }
      caption { text-align: left; font-weight: bold; margin-bottom: 8px; }
    </style>
    """
    html = df.to_html(classes="statx-table", border=0, justify="right")
    if footnotes:
        notes = "<br>".join(f"<em>{n}</em>" for n in footnotes)
    else:
        notes = ""
    return f"{style}<div><h3>{title}</h3>{html}{notes}</div>"


def run_crosstab(df: pd.DataFrame, rows: List[str], cols: List[str]) -> str:
    # Build multi-way crosstab using pandas crosstab. For multi-column, combine keys.
    row_key = df[rows].astype(str).agg(" | ", axis=1)
    col_key = df[cols].astype(str).agg(" | ", axis=1)

    ct = pd.crosstab(row_key, col_key, dropna=False)
    total = ct.values.sum()
    with np.errstate(divide="ignore", invalid="ignore"):
        row_pct = ct.div(ct.sum(axis=1), axis=0) * 100.0
        col_pct = ct.div(ct.sum(axis=0), axis=1) * 100.0
        tot_pct = (ct / total) * 100.0 if total else ct * 0

    # Interleave counts and percentages for readability
    interleaved = []
    for col in ct.columns:
        interleaved.append(ct[col].rename((col, "Count")))
        interleaved.append(row_pct[col].round(1).rename((col, "% Row")))
        interleaved.append(col_pct[col].round(1).rename((col, "% Col")))
        interleaved.append(tot_pct[col].round(1).rename((col, "% Total")))
    inter_df = pd.concat(interleaved, axis=1)
    inter_df.columns = pd.MultiIndex.from_tuples(inter_df.columns)

    # Add totals
    totals = pd.DataFrame(index=inter_df.index)
    totals[("Total", "Count")] = ct.sum(axis=1)
    totals[("Total", "% Row")] = row_pct.sum(axis=1).round(1)
    totals[("Total", "% Col")] = np.nan
    totals[("Total", "% Total")] = tot_pct.sum(axis=1).round(1)
    inter_df = pd.concat([inter_df, totals], axis=1)

    # Chi-square test of independence on raw counts
    if _HAS_SCIPY and chi2_contingency is not None:
        try:
            chi2, p, dof, expected = chi2_contingency(ct.values)  # type: ignore[misc]
            foot = [
                f"Chi-square={chi2:.3f}, df={dof}, p-value={p:.4g}",
            ]
        except Exception as exc:  # noqa: BLE001
            foot = [f"Chi-square could not be computed: {exc}"]
    else:
        foot = ["Chi-square requires SciPy; counts and percentages shown only."]

    inter_df.index.name = " x ".join(rows)
    inter_df = inter_df.sort_index()

    return format_html_table(
        title=f"Crosstab: {' x '.join(rows)} by {' x '.join(cols)}",
        df=inter_df,
        footnotes=foot,
    )
