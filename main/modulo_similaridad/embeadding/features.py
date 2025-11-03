from __future__ import annotations

import pandas as pd
from typing import Optional

# Reuse existing, proven implementation
from utils.utils import create_user_multihot_vectors


def build_user_features(
    split_df: pd.DataFrame,
    department_weight: float = 1.0,
    function_weight: float = 1.0,
    roles_weight: float = 1.0,
) -> pd.DataFrame:
    """Create a user feature matrix (multi-hot) from split_roles-like DataFrame.

    The function delegates to utils.utils.create_user_multihot_vectors but
    provides a clear, domain-specific entrypoint for the similarity module.
    Index of the returned DataFrame is 'Usuario'.
    """
    return create_user_multihot_vectors(
        split_df,
        department_weight=department_weight,
        function_weight=function_weight,
        roles_weight=roles_weight,
    )
