# Feedback System – Technical Documentation

## Overview

The system includes a multi-layer feedback loop that allows users to evaluate ML recommendations and use those evaluations to improve the model over time. Feedback is stored in SQLite, aggregated into training data, and used to retrain the CatBoost classifier on demand.

---

## Feedback Layers

### Layer 1 – Negative Feedback Filter (Pipeline)

When a new analysis runs, `app/pipeline.py` calls `get_all_negative_feedback_pairs()` from `database/db.py` to retrieve all `(usuario, recommended_role)` pairs previously marked as "not useful" across all analyses. These pairs are passed to `CmpcRoleRecommender` and **excluded from the output recommendations**.

```python
# app/pipeline.py
negative_pairs = get_all_negative_feedback_pairs()
results = run_analysis(..., negative_feedback_pairs=negative_pairs)
```

This means once a user marks a recommendation as unhelpful, it will not appear in future analyses.

---

### Layer 2 – Auto-Feedback from Validation File

During each analysis, `app/pipeline.py` compares the new recommendations against the uploaded `resumen_*.csv` (ground-truth role assignments). Any recommendation that matches an actual assignment is **automatically pre-marked as useful** (`is_useful = True`) and saved to the `feedback` table.

This bootstraps the feedback database without manual effort, giving the model signal from confirmed assignments.

```python
# pipeline result includes:
results["auto_feedback"] = [
    {"usuario": "DJAEKEL", "recommended_role": "ZD_DOMMIM0", ...},
    ...
]
# Saved in new_analysis.py via save_feedback_batch(auto_fb_batch)
```

---

### Layer 3 – Manual Feedback (UI)

In `app/views/analysis_detail.py`, the user can review each recommendation and mark it:
- **Sí** — the recommendation is useful
- **No** — the recommendation is not useful
- **Sin evaluar** — no opinion (default)

The UI pre-fills existing feedback from the DB. On "Guardar feedback":

1. `save_feedback_batch(feedbacks)` — upserts rows into `feedback` table in SQLite
2. `export_feedback_to_csv(analysis_id, path)` — saves a per-analysis CSV to `data/feedback/`
3. `export_all_feedback_as_training_data(path)` — exports all accumulated feedback as a training-compatible CSV to `data/feedback/feedback_training_data.csv`

If feedback is re-saved with different values, the previous entry is **overwritten** (no history is kept). This represents the user's current opinion.

---

## SQLite Schema – `feedback` Table

```sql
CREATE TABLE IF NOT EXISTS feedback (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    recommendation_id INTEGER NOT NULL,
    analysis_id       INTEGER NOT NULL,
    usuario           TEXT    NOT NULL,
    recommended_role  TEXT    NOT NULL,
    is_useful         INTEGER NOT NULL,   -- 1 = useful, 0 = not useful
    created_at        TEXT    NOT NULL,
    FOREIGN KEY (recommendation_id) REFERENCES recommendations(id) ON DELETE CASCADE,
    FOREIGN KEY (analysis_id) REFERENCES analyses(id) ON DELETE CASCADE
);
```

---

## Retraining the Model

From the home page, the "Reentrenar modelo con feedback" button triggers the following sequence:

1. `export_all_feedback_as_training_data(feedback_path)` — exports all feedback from SQLite to `data/feedback/feedback_training_data.csv` with columns: `DEPARTAMETNO`, `FUNCION`, `ROL`, `ASIGNADO` (1=useful, 0=not useful)

2. `retrain_with_feedback(feedback_training_csv, original_training_csv, model_output_path)` — defined in `main/modulo_recomendacion_roles/data/generate_negative_cases.py`:

   - Loads the feedback CSV
   - If `original_training_csv` exists, combines it with the feedback data
   - Trains a new CatBoost model (iterations=300, depth=6, learning_rate=0.1)
   - Saves the retrained model to `models/modulo_recomendacion_roles/catboost_retrained.joblib`
   - Returns a status dict: `{"status": "ok", "n_feedback": N, "n_total": M, "model_path": "..."}`

3. The UI displays the result (rows used, model path) or an error message.

```
feedback table (SQLite)
    ↓ export_all_feedback_as_training_data()
data/feedback/feedback_training_data.csv
    ↓ retrain_with_feedback()
models/modulo_recomendacion_roles/catboost_retrained.joblib
```

---

## Key Functions Reference

| Function | File | Description |
|----------|------|-------------|
| `save_feedback_batch(feedbacks)` | `database/db.py` | Upsert list of feedback dicts into SQLite |
| `get_feedback_for_analysis(analysis_id)` | `database/db.py` | Load all feedback for an analysis |
| `get_all_negative_feedback_pairs()` | `database/db.py` | Return set of (user, role) marked not useful |
| `export_feedback_to_csv(analysis_id, path)` | `database/db.py` | Export one analysis feedback to CSV |
| `export_all_feedback_as_training_data(path)` | `database/db.py` | Export all feedback as training CSV |
| `retrain_with_feedback(...)` | `generate_negative_cases.py` | Retrain CatBoost with feedback data |

---

## Important Considerations

- **No feedback history**: feedback is overwritten on each save. The model always trains on the user's latest opinion.
- **Retraining is manual**: the user must explicitly click the retrain button. The system does not auto-retrain.
- **Retrained model path**: `catboost_retrained.joblib` is a separate file from the original pre-trained model. The pipeline must be configured to load this file for the retrained model to take effect in future analyses.
- **Auto-feedback scale**: the system can accumulate hundreds of confirmed assignments from `resumen_*.csv` files across multiple analyses before any manual feedback is needed.
