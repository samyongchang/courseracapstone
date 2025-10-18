from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Tuple
import pandas as pd


@dataclass(frozen=True)
class VariableInfo:
    name: str
    kind: str  # 'numeric' or 'categorical'


class DatasetManager:
    def __init__(self) -> None:
        self._dataframe: Optional[pd.DataFrame] = None
        self._variables_cache: Optional[List[VariableInfo]] = None

    def is_loaded(self) -> bool:
        return self._dataframe is not None

    def load_csv(self, file_path: str, encoding: Optional[str] = None) -> Tuple[int, int]:
        df = pd.read_csv(file_path, encoding=encoding) if encoding else pd.read_csv(file_path)
        # Normalize column names to strings
        df.columns = [str(c) for c in df.columns]
        self._dataframe = df
        self._variables_cache = None
        return df.shape[0], df.shape[1]

    def get_dataframe(self) -> pd.DataFrame:
        if self._dataframe is None:
            raise RuntimeError("No dataset loaded")
        return self._dataframe

    def _infer_variables(self) -> List[VariableInfo]:
        assert self._dataframe is not None
        variables: List[VariableInfo] = []
        for col in self._dataframe.columns:
            series = self._dataframe[col]
            if pd.api.types.is_numeric_dtype(series):
                variables.append(VariableInfo(name=col, kind="numeric"))
            else:
                variables.append(VariableInfo(name=col, kind="categorical"))
        return variables

    def get_variables(self) -> List[VariableInfo]:
        if self._dataframe is None:
            return []
        if self._variables_cache is None:
            self._variables_cache = self._infer_variables()
        return self._variables_cache

    def get_variable_names(self) -> List[str]:
        return [v.name for v in self.get_variables()]

    def get_numeric_variables(self) -> List[str]:
        return [v.name for v in self.get_variables() if v.kind == "numeric"]

    def get_categorical_variables(self) -> List[str]:
        return [v.name for v in self.get_variables() if v.kind == "categorical"]
