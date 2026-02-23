"""
Pipeline wrapper — bridges the Streamlit UI with CmpcRoleRecommender.

Handles file management, runs the pipeline, and returns structured results
ready for storage in SQLite and display in the frontend.
"""

import sys
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional

import pandas as pd

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from main.cmpc_role_recomender import CmpcRoleRecommender
from database.db import get_all_negative_feedback_pairs
from main.modulo_recomendacion_roles.data.generate_negative_cases import generate_training_dataset_uniform

# Available pre-trained models
MODELS = {
    "CatBoost": "models/modulo_recomendacion_roles/grid_search/catboost_best_model_20251102_183656.joblib",
    "LightGBM": "models/modulo_recomendacion_roles/grid_search/lightgbm_best_model_20251102_183656.joblib",
}

UPLOAD_BASE = PROJECT_ROOT / "data" / "uploads"
FEEDBACK_BASE = PROJECT_ROOT / "data" / "feedback"


def _ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)


def list_resumen_files() -> List[str]:
    """Return a list of available resumen_*.csv files in data/processed/."""
    processed = PROJECT_ROOT / "data" / "processed"
    if not processed.exists():
        return []
    return sorted(
        [f.name for f in processed.glob("resumen_*.csv")],
        reverse=True,
    )


def save_uploaded_files(
    analysis_id: int,
    user_addr_file,
    agr_users_file,
) -> Path:
    """Save uploaded Streamlit files to a unique folder and return folder path."""
    dest = UPLOAD_BASE / str(analysis_id)
    _ensure_dir(dest)

    for uploaded, prefix in [
        (user_addr_file, "USER_ADDR_IDAD3"),
        (agr_users_file, "AGR_USERS"),
    ]:
        suffix = Path(uploaded.name).suffix  # .csv or .xlsx
        target = dest / f"{prefix}{suffix}"
        target.write_bytes(uploaded.getvalue())

    return dest


def run_analysis(
    analysis_id: int,
    data_folder: str = "",
    resumen_path: str = "",
    similarity_threshold: float = 0.8,
    classifier_threshold: float = 0.5,
    model_name: str = "CatBoost",
    user_filter: Optional[List[str]] = None,
    date_filter: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Execute the full recommendation pipeline.

    Parameters:
        resumen_path  – absolute path to the uploaded resumen CSV/XLSX file.

    Returns a dict with:
        recommendations  – list[dict]  ready for DB insertion
        users            – list[dict]  ready for DB insertion
        validation       – dict with recall, precision, etc.
        stats            – dict with total_recommendations, total_users
    """
    if not data_folder:
        data_folder = str(PROJECT_ROOT / "data")

    if not resumen_path:
        raise ValueError(
            "Se requiere un archivo de validación (resumen). "
            "Sube un archivo resumen desde la interfaz."
        )

    model_path = str(PROJECT_ROOT / MODELS.get(model_name, MODELS["CatBoost"]))
    data_type = _detect_data_type(Path(data_folder))

    # ---------- run pipeline ----------
    recommender = CmpcRoleRecommender(
        similarity_metric="cosine",
        resumen_data_path=resumen_path,
        n_top=10,
        data_folder=data_folder,
        threshold=similarity_threshold,
        data_type=data_type,
        date_filter=date_filter,
    )

    recommender.run_recommendations()

    # Validate raw recommendations
    validation_before = recommender.validate_results()

    # Classify & filter
    recommender.classify_recommendations(
        model_path=model_path,
        threshold=classifier_threshold,
    )

    # Validate after classification
    validation_after = recommender.validate_classification_results()

    # ---------- gather results ----------
    predictions_df: pd.DataFrame = recommender.get_recomendation()
    split_roles_df: pd.DataFrame = recommender.get_split_roles()

    # Build user list
    users = _build_users_list(split_roles_df, user_filter)

    # Filter recommendations to requested users if needed
    if user_filter:
        upper_filter = {u.upper() for u in user_filter}
        predictions_df = predictions_df[
            predictions_df["Usuario"].str.upper().isin(upper_filter)
        ]

    # Build recommendations list
    recommendations = _build_recommendations_list(predictions_df, split_roles_df)

    # ── Capa 1: filter out pairs with historical negative feedback ──────────
    negative_pairs = get_all_negative_feedback_pairs()
    if negative_pairs:
        before_count = len(recommendations)
        recommendations = [
            r for r in recommendations
            if (r["usuario"], r["recommended_role"]) not in negative_pairs
        ]
        filtered_count = before_count - len(recommendations)
        if filtered_count:
            print(f"[Capa 1] {filtered_count} recomendaciones excluidas por feedback negativo hist\u00f3rico.")

    # ── Auto-feedback: cross-check recommendations against resumen ──────────
    auto_feedback = _build_auto_feedback_from_resumen(recommendations, resumen_path)

    total_recs = len(recommendations)
    total_users = len(users)
    recall = validation_after.get("recall", 0.0)
    precision = validation_after.get("precision", 0.0)

    # ── Save split_roles + generate base training pairs for retraining ──────
    try:
        split_roles_path = PROJECT_ROOT / "data" / "processed" / "split_roles.csv"
        split_roles_df.to_csv(str(split_roles_path), index=False)
        training_pairs_out = PROJECT_ROOT / "data" / "modulo_recomendacion_roles" / "training_pairs_uniform_with_negatives.csv"
        training_pairs_out.parent.mkdir(parents=True, exist_ok=True)
        generate_training_dataset_uniform(
            input_csv_path=str(split_roles_path),
            output_csv_path=str(training_pairs_out),
            negative_ratio=3,
            random_state=42,
            include_usuario_col=False,
        )
    except Exception as e:
        print(f"[pipeline] Warning: no se pudo exportar split_roles/training_pairs: {e}")

    return {
        "recommendations": recommendations,
        "users": users,
        "auto_feedback": auto_feedback,
        "validation_before": validation_before,
        "validation_after": validation_after,
        "stats": {
            "total_recommendations": total_recs,
            "total_users": total_users,
            "recall": recall,
            "precision": precision,
        },
    }


# ── internal helpers ─────────────────────────────────────────────


def _build_auto_feedback_from_resumen(recommendations: List[Dict], resumen_path: str) -> List[Dict]:
    """
    Cross-check recommendations against the resumen file.
    Returns list of {usuario, recommended_role, is_useful=True} for confirmed pairs.
    """
    try:
        path = Path(resumen_path)
        if path.suffix.lower() in (".xlsx", ".xls"):
            resumen_df = pd.read_excel(resumen_path)
        else:
            resumen_df = pd.read_csv(resumen_path)

        if "Usuario" not in resumen_df.columns or "Rol" not in resumen_df.columns:
            return []

        # Extract role prefix: "ZD_VIMMPUR-001-07-001:0504" → "ZD_VIMMPUR"
        resumen_df["Rol_Prefix"] = resumen_df["Rol"].apply(
            lambda r: str(r).split("-")[0].strip() if pd.notna(r) else ""
        )
        confirmed = set(
            zip(resumen_df["Usuario"].str.strip(), resumen_df["Rol_Prefix"])
        )

        auto_fb = []
        for rec in recommendations:
            if (rec["usuario"], rec["recommended_role"]) in confirmed:
                auto_fb.append(
                    {
                        "usuario": rec["usuario"],
                        "recommended_role": rec["recommended_role"],
                        "is_useful": True,
                    }
                )
        print(f"[Auto-feedback] {len(auto_fb)} recomendaciones pre-marcadas como S\u00ed desde resumen.")
        return auto_fb
    except Exception as e:
        print(f"[Auto-feedback] Error: {e}")
        return []


def _detect_data_type(folder: Path) -> str:
    """Detect if data files are .csv or .xlsx based on USER_ADDR_IDAD3 file."""
    if list(folder.glob("USER_ADDR_IDAD3*.csv")) or list(folder.glob("USER_ADDR_IDAD3*.CSV")):
        return ".csv"
    if list(folder.glob("USER_ADDR_IDAD3*.xlsx")) or list(folder.glob("USER_ADDR_IDAD3*.XLSX")):
        return ".xlsx"
    # Fallback: check AGR_USERS
    if list(folder.glob("AGR_USERS*.csv")) or list(folder.glob("AGR_USERS*.CSV")):
        return ".csv"
    return ".xlsx"


def _build_users_list(
    split_df: pd.DataFrame,
    user_filter: Optional[List[str]] = None,
) -> List[Dict]:
    """Convert split_roles DataFrame into list of user dicts."""
    users = []
    for _, row in split_df.iterrows():
        usuario = row.get("Usuario", "")
        if user_filter:
            if usuario.upper() not in {u.upper() for u in user_filter}:
                continue
        roles = row.get("Rol", [])
        n_roles = len(roles) if isinstance(roles, list) else 0
        users.append(
            {
                "usuario": usuario,
                "departamento": row.get("Departamento", ""),
                "funcion": row.get("Función", ""),
                "n_roles": n_roles,
            }
        )
    return users


def _build_recommendations_list(
    predictions_df: pd.DataFrame,
    split_df: pd.DataFrame,
) -> List[Dict]:
    """Convert predictions DataFrame into list of dicts for DB storage."""
    # Build user metadata map
    user_meta = {}
    for _, row in split_df.iterrows():
        user_meta[row["Usuario"]] = {
            "departamento": row.get("Departamento", ""),
            "funcion": row.get("Función", ""),
        }

    role_col = (
        "Recommended_Role"
        if "Recommended_Role" in predictions_df.columns
        else "Recomendation"
    )

    recs = []
    for _, row in predictions_df.iterrows():
        usuario = row.get("Usuario", "")
        meta = user_meta.get(usuario, {})
        recs.append(
            {
                "usuario": usuario,
                "recommended_role": row.get(role_col, ""),
                "confidence": row.get("Confidence", None),
                "count": row.get("Count", None),
                "avg_similarity": row.get("Avg_Similarity", None),
                "similar_users": row.get("Similar_Users", ""),
                "departamento": meta.get("departamento", ""),
                "funcion": meta.get("funcion", ""),
            }
        )
    return recs
