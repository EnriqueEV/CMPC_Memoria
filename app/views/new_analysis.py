"""
New Analysis page – Auto-detect existing data, configure parameters, launch pipeline.
"""

import streamlit as st
import pandas as pd
from pathlib import Path

from app.pipeline import (
    MODELS,
    PROJECT_ROOT,
    run_analysis,
    UPLOAD_BASE,
)
from database.db import (
    create_analysis,
    update_analysis_results,
    update_analysis_status,
    save_recommendations,
    save_users_analyzed,
    get_all_recommendations,
    save_feedback_batch,
)

# ── File detection helpers ──────────────────────────────────────

DATA_DIR = PROJECT_ROOT / "data"


def _find_data_file(prefix: str) -> Path | None:
    """Find a data file by prefix (e.g. 'USER_ADDR_IDAD3') in data/."""
    for ext in (".csv", ".CSV", ".xlsx", ".XLSX"):
        candidate = DATA_DIR / f"{prefix}{ext}"
        if candidate.exists():
            return candidate
    # Also try case-insensitive glob
    for f in DATA_DIR.iterdir():
        if f.is_file() and f.stem.upper() == prefix.upper() and f.suffix.lower() in (".csv", ".xlsx"):
            return f
    return None


def _load_preview(path: Path, nrows: int = 500) -> pd.DataFrame | None:
    """Load a small preview DF from a file path."""
    try:
        if path.suffix.lower() == ".csv":
            return pd.read_csv(path, nrows=nrows)
        else:
            return pd.read_excel(path, nrows=nrows)
    except Exception:
        return None


# ── Main render ─────────────────────────────────────────────────

# Valores fijos del pipeline (originales del código backend)
SIM_THRESHOLD = 0.8
CLF_THRESHOLD = 0.5
MODEL_NAME = "CatBoost"


def render():
    st.markdown("## Nuevo análisis")

    # ── 1. Nombre del análisis ──────────────────────────────────
    st.markdown(
        '<p class="section-title">Nombre del análisis *</p>',
        unsafe_allow_html=True,
    )
    analysis_name = st.text_input(
        "Nombre del análisis",
        value="",
        placeholder="Ej: Análisis_Junio_2025",
        help="Nombre identificador para este análisis",
        label_visibility="collapsed",
    )

    # ── 2. Auto-detect existing data files ──────────────────────
    user_addr_path = _find_data_file("USER_ADDR_IDAD3")
    agr_users_path = _find_data_file("AGR_USERS")

    if user_addr_path and agr_users_path:
        data_ready = True
    else:
        # Files not found – require upload
        missing = []
        if not user_addr_path:
            missing.append("USER_ADDR_IDAD3")
        if not agr_users_path:
            missing.append("AGR_USERS")
        st.warning(
            f"No se encontraron los archivos: **{', '.join(missing)}** en `data/`. "
            f"Por favor, sube los archivos exportados de SAP."
        )

        col_f1, col_f2 = st.columns(2)
        with col_f1:
            new_user_addr = st.file_uploader(
                "USER_ADDR_IDAD3 *",
                type=["csv", "xlsx"],
                key="upload_user_addr",
                help="Archivo con columnas: Usuario, Departamento, Función",
            )
        with col_f2:
            new_agr_users = st.file_uploader(
                "AGR_USERS *",
                type=["csv", "xlsx"],
                key="upload_agr_users",
                help="Archivo con columnas: Usuario, Rol",
            )

        if new_user_addr or new_agr_users:
            if st.button("Guardar archivos en data/", type="primary"):
                _update_data_files(new_user_addr, new_agr_users)
                st.rerun()

        data_ready = bool(new_user_addr and new_agr_users) or (user_addr_path and agr_users_path)

    # ── 2. Resumen file (upload) ─────────────────────────────────
    st.markdown(
        '<p class="section-title">Archivo de validación *</p>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Sube un archivo resumen de asignaciones (.csv) para calcular métricas "
        "de validación (recall, precision). Este archivo debe contener las "
        "asignaciones reales de roles."
    )

    resumen_uploaded = st.file_uploader(
        "Resumen de asignaciones",
        type=["csv", "xlsx"],
        key="upload_resumen",
        help="Archivo resumen_*.csv con las asignaciones reales de roles para validación",
    )

    # ── 4. Optional user filter ─────────────────────────────────
    st.markdown(
        '<p class="section-title">Filtro por usuario (opcional)</p>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Si deseas analizar solo usuarios específicos, agrega sus IDs separados por coma."
    )

    user_filter_text = st.text_input(
        "IDs de usuario",
        placeholder="Ej: AABATTI, MRODRIGUEZ, JSCHULZ",
        label_visibility="collapsed",
    )
    user_filter = (
        [u.strip().upper() for u in user_filter_text.split(",") if u.strip()]
        if user_filter_text
        else None
    )

    if user_filter:
        st.info(f"Se analizarán {len(user_filter)} usuario(s): {', '.join(user_filter)}")

    # ── 5. Launch ───────────────────────────────────────────────
    can_run = data_ready and analysis_name and resumen_uploaded
    if not can_run:
        missing = []
        if not data_ready:
            missing.append("archivos de datos")
        if not resumen_uploaded:
            missing.append("archivo de validación")
        if not analysis_name:
            missing.append("nombre del análisis")
        if missing:
            st.caption(f"* Falta: {', '.join(missing)}.")

    if st.button(
        "Comenzar análisis",
        disabled=not can_run,
        type="primary",
        use_container_width=True,
        icon=":material/play_arrow:",
    ):
        _execute_analysis(
            analysis_name=analysis_name,
            resumen_uploaded=resumen_uploaded,
            sim_threshold=SIM_THRESHOLD,
            clf_threshold=CLF_THRESHOLD,
            model_name=MODEL_NAME,
            user_filter=user_filter,
        )


# ── Helpers ─────────────────────────────────────────────────────


def _update_data_files(new_user_addr, new_agr_users):
    """Save uploaded files into data/ folder, replacing existing ones."""
    saved = []
    for uploaded, prefix in [(new_user_addr, "USER_ADDR_IDAD3"), (new_agr_users, "AGR_USERS")]:
        if uploaded is not None:
            suffix = Path(uploaded.name).suffix
            target = DATA_DIR / f"{prefix}{suffix}"
            target.write_bytes(uploaded.getvalue())
            saved.append(prefix)
    if saved:
        st.success(f"Archivos actualizados: {', '.join(saved)}")


def _save_resumen_file(resumen_uploaded) -> str:
    """Save the uploaded resumen file to a temp location and return its path."""
    dest = UPLOAD_BASE / "resumen"
    dest.mkdir(parents=True, exist_ok=True)
    suffix = Path(resumen_uploaded.name).suffix
    target = dest / f"resumen_uploaded{suffix}"
    target.write_bytes(resumen_uploaded.getvalue())
    return str(target)


def _execute_analysis(
    analysis_name,
    resumen_uploaded,
    sim_threshold,
    clf_threshold,
    model_name,
    user_filter,
):
    """Run the pipeline with progress feedback using existing data/ files."""

    # 1. Save uploaded resumen to disk
    resumen_path = _save_resumen_file(resumen_uploaded)

    # 2. Create DB record
    analysis_id = create_analysis(
        name=analysis_name,
        similarity_threshold=sim_threshold,
        classifier_threshold=clf_threshold,
        model_used=model_name,
        data_folder=str(DATA_DIR),
        resumen_file=resumen_uploaded.name,
        user_filter=", ".join(user_filter) if user_filter else "",
    )

    progress = st.progress(0, text="Iniciando análisis…")

    try:
        progress.progress(5, text="Ejecutando pipeline de similitud…")

        # 3. Run pipeline directly on data/ folder
        results = run_analysis(
            analysis_id=analysis_id,
            data_folder=str(DATA_DIR),
            resumen_path=resumen_path,
            similarity_threshold=sim_threshold,
            classifier_threshold=clf_threshold,
            model_name=model_name,
            user_filter=user_filter,
        )
        progress.progress(70, text="Guardando resultados…")

        # 3. Save to DB
        if results["recommendations"]:
            save_recommendations(analysis_id, results["recommendations"])
        if results["users"]:
            save_users_analyzed(analysis_id, results["users"])

        # Auto-feedback: pre-mark recommendations confirmed by resumen as "Sí"
        if results.get("auto_feedback"):
            saved_recs = get_all_recommendations(analysis_id)
            rec_id_map = {
                (r["usuario"], r["recommended_role"]): r["id"] for r in saved_recs
            }
            auto_fb_batch = []
            for af in results["auto_feedback"]:
                rec_id = rec_id_map.get((af["usuario"], af["recommended_role"]))
                if rec_id:
                    auto_fb_batch.append(
                        {
                            "recommendation_id": rec_id,
                            "analysis_id": analysis_id,
                            "usuario": af["usuario"],
                            "recommended_role": af["recommended_role"],
                            "is_useful": True,
                        }
                    )
            if auto_fb_batch:
                save_feedback_batch(auto_fb_batch)

        stats = results["stats"]
        update_analysis_results(
            analysis_id=analysis_id,
            recall=stats["recall"],
            precision=stats["precision"],
            total_recommendations=stats["total_recommendations"],
            total_users=stats["total_users"],
            status="completado",
        )
        progress.progress(100, text="¡Análisis completado!")

        # 4. Navigate to detail
        st.success(
            f"Análisis **{analysis_name}** completado. "
            f"{stats['total_recommendations']:,} recomendaciones generadas."
        )
        st.session_state.current_page = "detail"
        st.session_state.selected_analysis_id = analysis_id
        st.rerun()

    except Exception as e:
        update_analysis_status(analysis_id, "error")
        progress.empty()
        st.error(f"Error durante el análisis: {e}")
        st.exception(e)
