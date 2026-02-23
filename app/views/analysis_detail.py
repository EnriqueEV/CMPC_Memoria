"""
Analysis Detail page – View results, browse recommendations, and give feedback.
"""

import math
import pandas as pd
import streamlit as st

from database.db import (
    get_analysis_by_id,
    get_recommendations,
    get_all_recommendations,
    get_users_analyzed,
    save_feedback_batch,
    get_feedback_for_analysis,
    export_feedback_to_csv,
    export_all_feedback_as_training_data,
    delete_analysis,
)
from app.styles import badge, metric_card, wrap_table_html


USERS_PER_PAGE = 8
USERS_REC_PER_PAGE = 15


def render():
    analysis_id = st.session_state.get("selected_analysis_id")
    if not analysis_id:
        st.warning("No se ha seleccionado ningún análisis.")
        return

    analysis = get_analysis_by_id(analysis_id)
    if not analysis:
        st.error("Análisis no encontrado.")
        return

    # ── Title ───────────────────────────────────────────────────
    status = analysis.get("status", "en_proceso")
    status_badge = badge(
        "Completado" if status == "completado" else ("Error" if status == "error" else "En proceso"),
        "completado" if status == "completado" else ("error" if status == "error" else "en_proceso"),
    )
    st.markdown(
            f"## Revisión de análisis: {analysis['name']} {status_badge}",
            unsafe_allow_html=True,
        )

    if status != "completado":
        st.info("Este análisis aún no ha terminado o tuvo un error.")
        return

    # ── Metrics ─────────────────────────────────────────────────
    _render_metrics(analysis)

    st.markdown("---")

    # ── Users section ───────────────────────────────────────────
    _render_users_section(analysis_id)

    st.markdown("---")

    # ── Recommendations section ─────────────────────────────────
    _render_recommendations_section(analysis_id)


# =====================================================================
# Metrics
# =====================================================================


def _render_metrics(analysis: dict):
    """Show top-level metric cards."""
    total_recs = analysis.get("total_recommendations", 0)
    total_users = analysis.get("total_users", 0)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            metric_card(f"{total_recs:,}", "Recomendaciones"),
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            metric_card(f"{total_users:,}", "Usuarios analizados"),
            unsafe_allow_html=True,
        )


# =====================================================================
# Users table
# =====================================================================


def _render_users_section(analysis_id: int):
    st.markdown(
        '<p class="section-title">Usuarios analizados</p>',
        unsafe_allow_html=True,
    )

    search_user = st.text_input(
        "Buscar por usuario, función o departamento…",
        placeholder="Buscar por usuario, función o departamento…",
        label_visibility="collapsed",
        key="user_search",
    )

    # Pagination
    if "users_page" not in st.session_state:
        st.session_state.users_page = 1
    page = st.session_state.users_page
    offset = (page - 1) * USERS_PER_PAGE

    users, total = get_users_analyzed(
        analysis_id, search=search_user, limit=USERS_PER_PAGE, offset=offset
    )
    total_pages = max(1, math.ceil(total / USERS_PER_PAGE))
    page = min(page, total_pages)

    if not users:
        st.info("No se encontraron usuarios.")
        return

    # Build HTML table
    html = """
    <table class="custom-table">
    <thead><tr>
        <th>Usuario</th>
        <th>Función</th>
        <th>Departamento</th>
        <th>Roles actuales</th>
    </tr></thead><tbody>
    """
    for u in users:
        html += f"""<tr>
            <td><strong>{u['usuario']}</strong></td>
            <td>{u.get('funcion', '')}</td>
            <td>{u.get('departamento', '')}</td>
            <td>{u.get('n_roles', 0)}</td>
        </tr>"""
    html += "</tbody></table>"
    st.html(wrap_table_html(html))

    # Pagination
    ic, nc = st.columns([2, 3])
    with ic:
        st.markdown(
            f'<p class="pagination-info">Mostrando {offset+1}-{min(offset+USERS_PER_PAGE, total)} de {total}</p>',
            unsafe_allow_html=True,
        )
    with nc:
        b1, b2, b3 = st.columns([1, 2, 1])
        with b1:
            if st.button("◀ Anterior", disabled=(page <= 1), key="usr_prev"):
                st.session_state.users_page = page - 1
                st.rerun()
        with b2:
            st.markdown(
                f"<p style='text-align:center;margin-top:8px;'>Página {page} de {total_pages}</p>",
                unsafe_allow_html=True,
            )
        with b3:
            if st.button("Siguiente ▶", disabled=(page >= total_pages), key="usr_next"):
                st.session_state.users_page = page + 1
                st.rerun()


# =====================================================================
# Recommendations + Feedback
# =====================================================================


def _render_recommendations_section(analysis_id: int):
    st.markdown(
        '<p class="section-title">Recomendaciones de roles</p>',
        unsafe_allow_html=True,
    )

    # Filter by user
    filter_user = st.text_input(
        "Buscar usuario…",
        placeholder="Buscar usuario…",
        label_visibility="collapsed",
        key="rec_user_filter",
    )

    # Get ALL recommendations and group by user
    all_recs = get_all_recommendations(analysis_id)
    if not all_recs:
        st.info("No se encontraron recomendaciones.")
        return

    # Load existing feedback to pre-fill
    existing_fb = get_feedback_for_analysis(analysis_id)
    fb_map = {f["recommendation_id"]: f["is_useful"] for f in existing_fb}

    # ── Feedback progress bar ───
    total_recs = len(all_recs)
    evaluated = len(existing_fb)
    auto_si = sum(1 for f in existing_fb if f["is_useful"])
    pct = evaluated / total_recs if total_recs > 0 else 0
    prog_col, pct_col = st.columns([5, 1])
    with prog_col:
        st.progress(pct, text=f"Feedback evaluado: {evaluated} / {total_recs}")
    with pct_col:
        st.markdown(
            f"<p style='text-align:center;font-size:1.5rem;font-weight:700;margin-top:0.3rem'>{pct*100:.0f}%</p>",
            unsafe_allow_html=True,
        )
    if auto_si > 0:
        st.caption(
            f"✅ {auto_si} recomendación{'es' if auto_si != 1 else ''} validada{'s' if auto_si != 1 else ''} "
            f"automáticamente contra el resumen ({auto_si}/{total_recs})"
        )

    # Group by user
    from collections import OrderedDict
    user_groups: OrderedDict[str, list] = OrderedDict()
    for rec in all_recs:
        user = rec["usuario"]
        if filter_user and filter_user.upper() not in user.upper():
            continue
        if user not in user_groups:
            user_groups[user] = []
        user_groups[user].append(rec)

    if not user_groups:
        st.info("No se encontraron usuarios con ese filtro.")
        return

    # Pagination over users
    users_list = list(user_groups.keys())
    total_users_with_recs = len(users_list)

    if "recs_user_page" not in st.session_state:
        st.session_state.recs_user_page = 1
    page = st.session_state.recs_user_page
    total_pages = max(1, math.ceil(total_users_with_recs / USERS_REC_PER_PAGE))
    page = min(page, total_pages)
    offset = (page - 1) * USERS_REC_PER_PAGE
    page_users = users_list[offset : offset + USERS_REC_PER_PAGE]

    st.caption(f"{total_users_with_recs} usuario(s) con recomendaciones")

    # ── Expand / Collapse all ───────────────────────────────────
    if "recs_expand_all" not in st.session_state:
        st.session_state.recs_expand_all = False
    _exp_col, _col_col, _ = st.columns([1, 1, 4])
    with _exp_col:
        if st.button("⊕ Expandir todo", key="btn_expand_all", use_container_width=True):
            st.session_state.recs_expand_all = True
            st.rerun()
    with _col_col:
        if st.button("⊖ Colapsar todo", key="btn_collapse_all", use_container_width=True):
            st.session_state.recs_expand_all = False
            st.rerun()

    # Collect all feedback inputs for saving
    feedback_inputs = {}

    for user in page_users:
        recs = user_groups[user]
        n_recs = len(recs)
        dept = recs[0].get("departamento", "")
        func = recs[0].get("funcion", "")
        label = f"👤 **{user}**  —  {func} · {dept}  ({n_recs} rol{'es' if n_recs != 1 else ''})"

        with st.expander(label, expanded=st.session_state.get("recs_expand_all", False)):
            for rec in recs:
                rec_id = rec["id"]
                confidence = rec.get("confidence")
                conf_str = f"{confidence:.2f}" if confidence is not None else "—"
                count_val = rec.get("count", "—")

                col_role, col_conf, col_count, col_fb = st.columns([3, 1, 1, 1.5])

                with col_role:
                    st.markdown(f"`{rec['recommended_role']}`")
                with col_conf:
                    st.caption("Confianza")
                    st.write(conf_str)
                with col_count:
                    st.caption("Similares")
                    st.write(count_val if count_val else "—")
                with col_fb:
                    existing = fb_map.get(rec_id)
                    if existing is not None:
                        default_idx = 1 if existing else 2
                    else:
                        default_idx = 0

                    fb_val = st.radio(
                        f"fb_{rec_id}",
                        options=["Sin evaluar", "Sí", "No"],
                        index=default_idx,
                        horizontal=True,
                        label_visibility="collapsed",
                        key=f"fb_{rec_id}",
                    )
                    feedback_inputs[rec_id] = {
                        "value": fb_val,
                        "usuario": rec["usuario"],
                        "recommended_role": rec["recommended_role"],
                    }

    # ── Pagination ─────────────────────────────────────────────
    if total_pages > 1:
        ic2, nc2 = st.columns([2, 3])
        with ic2:
            st.markdown(
                f'<p class="pagination-info">Usuarios {offset+1}-{min(offset+USERS_REC_PER_PAGE, total_users_with_recs)} de {total_users_with_recs}</p>',
                unsafe_allow_html=True,
            )
        with nc2:
            rb1, rb2, rb3 = st.columns([1, 2, 1])
            with rb1:
                if st.button("◀ Anterior", disabled=(page <= 1), key="rec_prev"):
                    st.session_state.recs_user_page = page - 1
                    st.rerun()
            with rb2:
                st.markdown(
                    f"<p style='text-align:center;margin-top:8px;'>Página {page} de {total_pages}</p>",
                    unsafe_allow_html=True,
                )
            with rb3:
                if st.button("Siguiente ▶", disabled=(page >= total_pages), key="rec_next"):
                    st.session_state.recs_user_page = page + 1
                    st.rerun()

    # ── Action buttons ──────────────────────────────────────────
    st.markdown("---")
    btn_col1, btn_col2, btn_col3 = st.columns(3)

    with btn_col1:
        if st.button(
            "Guardar feedback",
            type="primary",
            use_container_width=True,
            icon=":material/save:",
            key="btn_save_feedback",
        ):
            _save_feedback(analysis_id, feedback_inputs)

    with btn_col2:
        if st.button(
            "Eliminar análisis",
            type="secondary",
            use_container_width=True,
            icon=":material/delete:",
            key="detail_delete",
        ):
            delete_analysis(analysis_id)
            st.session_state.current_page = "home"
            st.session_state.selected_analysis_id = None
            st.toast("Análisis eliminado")
            st.rerun()

    with btn_col3:
        _render_download_button(analysis_id)


# ── Action helpers ──────────────────────────────────────────────


def _render_download_button(analysis_id: int):
    """Generate and offer a CSV download of all recommendations."""
    all_recs = get_all_recommendations(analysis_id)
    if not all_recs:
        st.info("Sin recomendaciones para descargar.")
        return

    df = pd.DataFrame(all_recs)
    cols_export = [
        c
        for c in [
            "usuario",
            "recommended_role",
            "confidence",
            "count",
            "avg_similarity",
            "similar_users",
            "departamento",
            "funcion",
        ]
        if c in df.columns
    ]
    csv = df[cols_export].to_csv(index=False).encode("utf-8")

    analysis = get_analysis_by_id(analysis_id)
    filename = f"recomendaciones_{analysis['name']}.csv" if analysis else "recomendaciones.csv"

    st.download_button(
        label="Descargar recomendaciones (CSV)",
        icon=":material/download:",
        data=csv,
        file_name=filename,
        mime="text/csv",
        use_container_width=True,
        key="btn_download_recs",
    )


def _save_feedback(analysis_id: int, feedback_inputs: dict):
    """Persist feedback entries to SQLite and export to CSV."""
    feedbacks = []
    for rec_id, info in feedback_inputs.items():
        val = info["value"]
        if val == "Sin evaluar":
            continue
        feedbacks.append(
            {
                "recommendation_id": rec_id,
                "analysis_id": analysis_id,
                "usuario": info["usuario"],
                "recommended_role": info["recommended_role"],
                "is_useful": val == "Sí",
            }
        )

    if not feedbacks:
        st.warning("No hay feedback para guardar. Marca al menos una recomendación.")
        return

    save_feedback_batch(feedbacks)

    # Export per-analysis CSV
    from pathlib import Path
    csv_path = Path("data") / "feedback" / f"feedback_analysis_{analysis_id}.csv"
    export_feedback_to_csv(analysis_id, str(csv_path))

    # Capa 2: export accumulated feedback as training data for retraining
    training_path = Path("data") / "feedback" / "feedback_training_data.csv"
    n_exported = export_all_feedback_as_training_data(str(training_path))
    if n_exported:
        st.info(f"Datos de entrenamiento actualizados: {n_exported} pares en `{training_path}`")

    st.success(f"{len(feedbacks)} feedback(s) guardado(s) correctamente.")
    st.rerun()
