from __future__ import annotations

import pandas as pd
from typing import Tuple, Optional
from sklearn.decomposition import KernelPCA


def compute_kpca(
    X: pd.DataFrame,
    n_components: int = 2,
    kernel: str = 'rbf',
    gamma: str | float | None = 'scale',
    random_state: Optional[int] = 42,
):
    """Compute Kernel PCA embeddings over a numeric feature matrix X.

    Returns (embedding_df, model) where embedding_df has the same index as X
    and columns ['kpca_1', 'kpca_2', ...].
    """
    # Normalize gamma option for older sklearn versions that don't accept strings
    gamma_value = gamma
    if isinstance(gamma, str):
        if gamma.lower() == 'scale':
            var = float(X.values.var())
            gamma_value = 1.0 / (X.shape[1] * var) if var > 0 else 1.0
        elif gamma.lower() == 'auto':
            gamma_value = 1.0 / X.shape[1] if X.shape[1] > 0 else 1.0
        else:
            # Fallback to None for unknown strings
            gamma_value = None

    kpca = KernelPCA(
        n_components=n_components,
        kernel=kernel,
        gamma=gamma_value,
        random_state=random_state,
    )
    Z = kpca.fit_transform(X.values)
    cols = [f"kpca_{i+1}" for i in range(n_components)]
    emb_df = pd.DataFrame(Z, index=X.index, columns=cols)
    return emb_df, kpca
