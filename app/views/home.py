"""
Home page – Lists all previous analyses in a searchable, paginated table.
"""

import io
import math

import pandas as pd
import streamlit as st

from database.db import (
    get_all_analyses,
    get_all_recommendations,
    delete_analysis,
    export_all_feedback_as_training_data,
)
from app.styles import badge
from main.modulo_recomendacion_roles.data.generate_negative_cases import retrain_with_feedback


ROWS_PER_PAGE = 6

_HELP_TEXT = """
**¿Cómo funciona el sistema?**

1. **Crear un análisis** — Haz clic en **Nuevo análisis** en la barra lateral. Sube el archivo de usuarios SAP y el sistema identificará qué roles adicionales podrían necesitar.
2. **Revisar resultados** — Una vez completado, abre el análisis para ver las recomendaciones de roles por usuario, junto con los usuarios similares que fundamentan cada sugerencia.
3. **Dar feedback** — En el detalle de cada análisis puedes marcar cada recomendación como útil (Sí) o no útil (No) y guardar tu evaluación con **Guardar feedback**.
4. **Reentrenar el modelo** — Cuando hayas acumulado feedback suficiente, usa el botón **Reentrenar modelo con feedback** para que el clasificador aprenda de tus correcciones y mejore futuras recomendaciones.
5. **Descargar y eliminar** — Puedes descargar las recomendaciones como CSV o eliminar un análisis en cualquier momento.
"""


def render():
    # ── Title + help button ─────────────────────────────────────
    title_col, help_col = st.columns([9, 1])
    with title_col:
        st.markdown("## Sus análisis")
    with help_col:
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        if st.button("", key="help_btn", help="¿Cómo funciona el sistema?", use_container_width=True, icon=":material/help:"):
            _show_help_dialog()

    # ── Search bar ──────────────────────────────────────────────
    search = st.text_input(
        "Buscar por nombre…",
        placeholder="Buscar por nombre…",
        label_visibility="collapsed",
    )

    # ── Fetch data ──────────────────────────────────────────────
    analyses = get_all_analyses()

    if search:
        q = search.lower()
        analyses = [
            a
            for a in analyses
            if q in a["name"].lower()
        ]

    if not analyses:
        st.info("No hay análisis previos. Haz clic en **Nuevo análisis** en la barra lateral para comenzar.")
        st.markdown(_HELP_TEXT)
        return

    # ── Pagination state ────────────────────────────────────────
    total = len(analyses)
    total_pages = max(1, math.ceil(total / ROWS_PER_PAGE))

    if "home_page" not in st.session_state:
        st.session_state.home_page = 1
    page = st.session_state.home_page
    page = min(page, total_pages)

    start = (page - 1) * ROWS_PER_PAGE
    page_items = analyses[start : start + ROWS_PER_PAGE]

    # ── Table header ────────────────────────────────────────────
    hcols = st.columns([3, 2, 2, 2, 1, 1, 1])
    headers = ["Análisis", "Fecha creación", "Recomendaciones", "Estado", "", "", ""]
    for col, label in zip(hcols, headers):
        col.markdown(f"**{label}**")

    # ── Rows ────────────────────────────────────────────────────
    for a in page_items:
        status = a.get("status", "en_proceso")
        status_label = "Completado" if status == "completado" else ("Error" if status == "error" else "En proceso")
        status_color = "#166534" if status == "completado" else ("#dc2626" if status == "error" else "#f59e0b")
        recs_val = f'{a["total_recommendations"]:,}' if a.get("total_recommendations") else "—"

        c1, c2, c3, c4, c5, c6, c7 = st.columns([3, 2, 2, 2, 1, 1, 1])
        with c1:
            if st.button(a["name"], key=f"name_{a['id']}", use_container_width=True, type="tertiary"):
                st.session_state.current_page = "detail"
                st.session_state.selected_analysis_id = a["id"]
                st.rerun()
        c2.markdown(a["created_at"][:10])
        c3.markdown(recs_val)
        c4.markdown(
            f'<span style="background-color:{status_color};color:white;padding:3px 10px;'
            f'border-radius:6px;font-size:0.8rem;font-weight:600">{status_label}</span>',
            unsafe_allow_html=True,
        )
        with c5:
            if st.button("", key=f"open_{a['id']}", help="Ver detalle", use_container_width=True, icon=":material/folder_open:"):
                st.session_state.current_page = "detail"
                st.session_state.selected_analysis_id = a["id"]
                st.rerun()
        with c6:
            _download_button(a)
        with c7:
            if st.button("", key=f"del_{a['id']}", help="Eliminar análisis", use_container_width=True, icon=":material/delete:"):
                delete_analysis(a["id"])
                st.toast("Análisis eliminado")
                st.rerun()

    # ── Pagination controls ─────────────────────────────────────
    st.markdown("")
    info_col, nav_col = st.columns([2, 3])
    with info_col:
        st.markdown(
            f'<p class="pagination-info">Mostrando {start+1}-{min(start+ROWS_PER_PAGE, total)} de {total}</p>',
            unsafe_allow_html=True,
        )
    with nav_col:
        c1, c2, c3 = st.columns([1, 2, 1])
        with c1:
            if st.button("◀ Anterior", disabled=(page <= 1), key="home_prev"):
                st.session_state.home_page = page - 1
                st.rerun()
        with c2:
            st.markdown(
                f"<p style='text-align:center; margin-top:8px;'>Página {page} de {total_pages}</p>",
                unsafe_allow_html=True,
            )
        with c3:
            if st.button("Siguiente ▶", disabled=(page >= total_pages), key="home_next"):
                st.session_state.home_page = page + 1
                st.rerun()

    # ── Retrain button ──────────────────────────────────────────
    st.markdown("---")
    _retrain_col, _spacer = st.columns([2, 5])
    with _retrain_col:
        if st.button("Reentrenar modelo con feedback", use_container_width=True, type="primary", icon=":material/model_training:"):
            with st.spinner("Exportando feedback y reentrenando modelo…"):
                feedback_path = "data/feedback/feedback_training_data.csv"
                export_all_feedback_as_training_data(feedback_path)

                result = retrain_with_feedback(
                    feedback_training_csv=feedback_path,
                    original_training_csv="data/modulo_recomendacion_roles/training_pairs_uniform_with_negatives.csv",
                    model_output_path="models/modulo_recomendacion_roles/catboost_retrained.joblib",
                )

            if result["status"] == "ok":
                st.success(
                    f"Modelo reentrenado exitosamente. "
                    f"Feedback: {result['n_feedback']} filas · "
                    f"Total entrenamiento: {result['n_total']} filas · "
                    f"Guardado en: {result['model_path']}"
                )
            elif result["status"] == "insufficient_data":
                st.warning(result["message"])
            else:
                st.error(f"Error: {result.get('message', 'desconocido')}")


@st.dialog("¿Cómo funciona el sistema?", width="large")
def _show_help_dialog():
    st.markdown(_HELP_TEXT)


def _download_button(analysis: dict):
    """Render a download button for an analysis's recommendations."""
    aid = analysis["id"]
    recs = get_all_recommendations(aid)
    if not recs:
        st.button("", key=f"dl_{aid}", help="Sin recomendaciones", disabled=True, use_container_width=True, icon=":material/download:")
        return
    df = pd.DataFrame(recs)
    cols_keep = [c for c in ["usuario", "recommended_role", "confidence", "count", "avg_similarity", "similar_users"] if c in df.columns]
    csv_bytes = df[cols_keep].to_csv(index=False).encode("utf-8")
    st.download_button(
        "",
        data=csv_bytes,
        icon=":material/download:",
        file_name=f"recomendaciones_{analysis['name']}.csv",
        mime="text/csv",
        key=f"dl_{aid}",
        help="Descargar recomendaciones CSV",
        use_container_width=True,
    )
