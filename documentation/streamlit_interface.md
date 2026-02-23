# Streamlit Interface – Technical Documentation

## Overview

The CMPC SAP Role Recommender includes a Streamlit web application that provides a user-friendly interface for running analyses, reviewing ML recommendations, giving feedback, and retraining the model. The interface was built using Streamlit 1.54+, SQLite for persistence, and Material Symbols for iconography.

---

## Entry Point

The app is launched from the project root via:

```bash
streamlit run streamlit_app.py
```

`streamlit_app.py` uses `runpy.run_path()` to delegate execution to `app/app.py`. This indirection is required because running `app/app.py` directly adds `app/` to `sys.path`, which causes a module name collision (`app` vs the `app/` directory).

```python
# streamlit_app.py
import runpy, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
runpy.run_path(str(ROOT / "app" / "app.py"), run_name="__main__")
```

---

## Architecture

```
streamlit_app.py
    └── app/app.py              ← page config, sidebar, router
            ├── app/views/home.py
            ├── app/views/new_analysis.py
            └── app/views/analysis_detail.py
                    ↕
            app/pipeline.py     ← bridges UI ↔ ML pipeline
                    ↕
            database/db.py      ← SQLite persistence
```

### Page Routing

All navigation is handled through `st.session_state`. There are no multi-page Streamlit files — a single script with an explicit router:

```python
page = st.session_state.current_page  # "home" | "new" | "detail"

if page == "home":       home.render()
elif page == "new":      new_analysis.render()
elif page == "detail":   analysis_detail.render()
```

Navigation triggers `st.session_state.current_page = "..."` followed by `st.rerun()`.

---

## Views

### `home.py` — Analysis List

- Displays all past analyses in a paginated table (6 per page) with search.
- Each row: analysis name (clickable link), date, recommendations count, status badge, folder icon (detail), download icon (CSV), delete icon.
- Analysis name uses `type="tertiary"` button rendered as an underlined link via CSS.
- **Retrain button**: triggers `retrain_with_feedback()` from `generate_negative_cases.py`.
- **Help dialog**: `@st.dialog` modal opened by a `?` button, explaining the 5-step workflow.

### `new_analysis.py` — Create Analysis

- Auto-detects `AGR_USERS` and `USER_ADDR_IDAD3` in `data/`. If found, proceeds silently.
- If files are missing, shows upload widgets.
- User uploads a `resumen_*.csv` validation file.
- Optional user filter (comma-separated IDs).
- Executes the ML pipeline via `app/pipeline.py` with a progress bar.
- On completion, navigates directly to the detail view.

### `analysis_detail.py` — Results & Feedback

- Shows metrics: total recommendations and users analyzed.
- Paginated recommendation table grouped by user (~15 recs/page, 8 users/page).
- Feedback progress bar showing evaluated/total recommendations.
- Per-recommendation radio buttons: `Sí` / `No` / `Sin evaluar`, pre-filled from DB.
- **Save feedback button**: persists to SQLite and also auto-exports an accumulated training CSV.
- **Download button**: exports all recommendations as CSV.
- **Delete button**: removes the analysis (CASCADE) and returns to home.

---

## Sidebar

Defined in `app/app.py`:

- CMPC logo (100px)
- "Inicio" button (`primary`, `:material/home:`)
- "Nuevo análisis" button (`primary`, `:material/add:`)
- Separator + list of last 15 analyses (name only, navigates to detail)

---

## Styling

All CSS is in `app/styles.py` and injected via `st.markdown(get_custom_css(), unsafe_allow_html=True)`.

Key rules:
- **Light theme** forced via `.streamlit/config.toml` (`base = "light"`, `primaryColor = "#22c55e"`)
- **Sidebar**: `#f9fafb` background, `border-right: 1px solid #e5e7eb`
- **Primary buttons** (sidebar actions): green `#22c55e`
- **Tertiary buttons** (analysis name links): underlined, blue `#1d4ed8`
- **Status badges**: inline `<span>` with green/red/yellow background
- **Table rendering** (detail view): isolated in `<iframe>` via `wrap_table_html()` + `st.html()` to prevent style leakage

### Icons

All icons use **Material Symbols** via Streamlit's built-in `icon=` parameter on `st.button()` and `st.download_button()`:

| Action | Icon |
|--------|------|
| Home | `:material/home:` |
| New analysis | `:material/add:` |
| View detail | `:material/folder_open:` |
| Download | `:material/download:` |
| Delete | `:material/delete:` |
| Help | `:material/help:` |
| Save feedback | `:material/save:` |
| Retrain model | `:material/model_training:` |
| Start analysis | `:material/play_arrow:` |

---

## Database

`database/db.py` manages a SQLite database at `database/cmpc.db` (created at runtime, not tracked in git).

Key tables:

| Table | Purpose |
|-------|---------|
| `analyses` | Analysis metadata (name, status, thresholds, stats) |
| `recommendations` | One row per (analysis, user, role) recommendation |
| `feedback` | User evaluations of recommendations |
| `users_analyzed` | Users processed in each analysis |

`init_db()` is called on every app startup and creates tables if they don't exist.

---

## Configuration

`.streamlit/config.toml` sets the forced light theme:

```toml
[theme]
base = "light"
primaryColor = "#22c55e"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f9fafb"
textColor = "#1f2937"
```
