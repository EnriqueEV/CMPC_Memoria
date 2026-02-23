"""
Custom CSS styles for the CMPC Streamlit application.
Matches the reference design: green corporate palette, clean tables, status badges.
"""


def get_custom_css() -> str:
    """Return the full custom CSS as a string."""
    return """
<style>
    /* ── Global ─────────────────────────────────────────────────── */
    .block-container { padding-top: 1.5rem; }

    /* ── Sidebar ────────────────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background-color: #f9fafb;
        border-right: 1px solid #e5e7eb;
    }

    /* Logo: pequeño y centrado */
    [data-testid="stSidebar"] img {
        max-width: 110px !important;
        width: 110px !important;
        display: block;
        margin: 0 auto 0.2rem auto;
    }

    [data-testid="stSidebar"] h1 {
        color: #166534;
        font-size: 1.6rem;
    }

    /* Base reset for all sidebar buttons */
    [data-testid="stSidebar"] .stButton > button {
        border-radius: 6px;
        width: 100%;
        font-weight: 600;
        padding: 0.55rem 1rem;
    }
    /* Primary action buttons (Inicio, Nuevo análisis) → green */
    [data-testid="stSidebar"] [data-testid="baseButton-primary"] {
        background-color: #22c55e;
        color: white;
        border: none;
    }
    [data-testid="stSidebar"] [data-testid="baseButton-primary"]:hover {
        background-color: #16a34a;
        color: white;
        border: none;
    }
    /* Secondary / default buttons (analysis list) → grey/white */
    [data-testid="stSidebar"] [data-testid="baseButton-secondary"] {
        background-color: #f3f4f6;
        color: #374151;
        border: 1px solid #e5e7eb;
    }
    [data-testid="stSidebar"] [data-testid="baseButton-secondary"]:hover {
        background-color: #e5e7eb;
        color: #111827;
        border-color: #d1d5db;
    }

    /* ── Status badges ──────────────────────────────────────────── */

    /* Analysis name links (tertiary buttons styled as underlined links) */
    [data-testid="baseButton-tertiary"] {
        text-decoration: underline !important;
        color: #1d4ed8 !important;
        padding: 0 !important;
        text-align: left !important;
    }
    [data-testid="baseButton-tertiary"]:hover {
        color: #1e40af !important;
    }

    .badge {
        display: inline-block;
        padding: 4px 14px;
        border-radius: 6px;
        font-size: 0.82rem;
        font-weight: 600;
        text-align: center;
    }
    .badge-completado {
        background-color: #166534;
        color: white;
    }
    .badge-en-proceso {
        background-color: #f59e0b;
        color: white;
    }
    .badge-error {
        background-color: #dc2626;
        color: white;
    }
    .badge-ok {
        background-color: #22c55e;
        color: white;
        padding: 2px 10px;
    }

    /* ── Metric cards ───────────────────────────────────────────── */
    .metric-card {
        background-color: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-radius: 10px;
        padding: 1.1rem 1.4rem;
        text-align: center;
    }
    .metric-card h3 {
        margin: 0 0 0.3rem 0;
        color: #166534;
        font-size: 1.9rem;
    }
    .metric-card p {
        margin: 0;
        color: #4b5563;
        font-size: 0.85rem;
    }

    /* ── Custom table ───────────────────────────────────────────── */
    .custom-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.88rem;
    }
    .custom-table thead th {
        background-color: #dbeafe;
        color: #1e3a5f;
        padding: 10px 14px;
        text-align: left;
        font-weight: 600;
        border-bottom: 2px solid #93c5fd;
    }
    .custom-table tbody tr {
        border-bottom: 1px solid #e5e7eb;
    }
    .custom-table tbody tr:hover {
        background-color: #f0f9ff;
    }
    .custom-table td {
        padding: 9px 14px;
    }

    /* ── Pagination ─────────────────────────────────────────────── */
    .pagination-info {
        color: #6b7280;
        font-size: 0.85rem;
        margin-top: 0.4rem;
    }

    /* ── Section titles ─────────────────────────────────────────── */
    .section-title {
        font-size: 1.15rem;
        font-weight: 600;
        color: #1f2937;
        margin: 1.5rem 0 0.7rem 0;
        border-bottom: 2px solid #e5e7eb;
        padding-bottom: 0.35rem;
    }

    /* ── Download / action buttons ──────────────────────────────── */
    .action-btn {
        display: inline-block;
        padding: 8px 22px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.88rem;
        cursor: pointer;
        text-align: center;
    }
    .btn-green {
        background-color: #bbf7d0;
        color: #166534;
        border: 1px solid #86efac;
    }
    .btn-yellow {
        background-color: #fef9c3;
        color: #854d0e;
        border: 1px solid #fde68a;
    }

    /* ── Sidebar analysis list ──────────────────────────────────── */
    .sidebar-analysis-item {
        padding: 6px 10px;
        border-radius: 5px;
        margin-bottom: 2px;
        cursor: pointer;
        font-size: 0.88rem;
        color: #374151;
    }
    .sidebar-analysis-item:hover {
        background-color: #e5e7eb;
    }

    /* ── Hide Streamlit default hamburger + footer ───────────────── */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }

    /* ── Feedback radio horizontal ──────────────────────────────── */
    .feedback-row {
        display: flex;
        align-items: center;
        gap: 18px;
    }
</style>
"""


def badge(text: str, kind: str = "completado") -> str:
    """Return HTML for a coloured badge.

    kind: 'completado' | 'en_proceso' | 'error' | 'ok'
    """
    return f'<span class="badge badge-{kind}">{text}</span>'


def metric_card(value, label: str) -> str:
    """Return HTML for a metric card."""
    return f"""
    <div class="metric-card">
        <h3>{value}</h3>
        <p>{label}</p>
    </div>
    """


# CSS snippet embedded inside st.html() calls (which render in an isolated iframe)
_TABLE_CSS = """
<style>
.custom-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.88rem;
}
.custom-table thead th {
    background-color: #dbeafe;
    color: #1e3a5f;
    padding: 10px 14px;
    text-align: left;
    font-weight: 600;
    border-bottom: 2px solid #93c5fd;
}
.custom-table tbody tr {
    border-bottom: 1px solid #e5e7eb;
}
.custom-table tbody tr:hover {
    background-color: #f0f9ff;
}
.custom-table td {
    padding: 9px 14px;
}
.badge {
    display: inline-block;
    padding: 4px 14px;
    border-radius: 6px;
    font-size: 0.82rem;
    font-weight: 600;
    text-align: center;
}
.badge-completado { background-color: #166534; color: white; }
.badge-en-proceso { background-color: #f59e0b; color: white; }
.badge-error      { background-color: #dc2626; color: white; }
.badge-ok         { background-color: #22c55e; color: white; padding: 2px 10px; }
</style>
"""


def wrap_table_html(html_content: str) -> str:
    """Wrap an HTML snippet with the table/badge CSS so it renders correctly
    inside :func:`st.html`, which uses an isolated iframe."""
    return _TABLE_CSS + html_content
