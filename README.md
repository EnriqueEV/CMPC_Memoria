En la carpeta data tienen que ir los siguientes archivos XLSX

* AGR_1251
* AGR_USERS
* TSTCT
* USER_ADDR_IDAD3
* USR02

Resumen de los datos relevantes de cada archivo:

USER_ADDR_IDAD3.XLSX
  * Usuario: 1041 unique values
  * Departamento: 201 unique values
  * Función: 452 unique values

TSTCT.XLSX
  * CódT: 4016 unique values (Valor de la autorización)

AGR_1251.XLSX
  * Rol: 3091 unique values
  * Valor de la autorización: 4909 unique values

AGR_USERS.XLSX
  * Rol: 3619 unique values
  * Usuario: 1041 unique values

En el archivo /data/AGR_USERS_summary.csv se encuentra un resumen de los roles y el numero de usuarios que tiene cada rol

Los archivos que se terminaron usando para la ejecución del programa son:

- AGR_USERS.XLSX
- USER_ADDR_IDAD3.XLSX

---

# GUI Implementation and ejecution

## Prerequisites

- Python 3.11+
- The following SAP data export files placed in the `data/` directory (not tracked in git):
  - `AGR_USERS.xlsx` — role assignments per user
  - `USER_ADDR_IDAD3.xlsx` — user attributes (department, function)

---

## Installation

```bash
# 1. Clone the repository
git clone <repository-url>
cd CMPC_Memoria

# 2. Create and activate a virtual environment (recommended)
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

---

## Running the Interface

```bash
streamlit run streamlit_app.py
```

The app will open at **http://localhost:8501**

> **Note:** Do not run `streamlit run app/app.py` directly — use `streamlit_app.py` from the project root to ensure all imports resolve correctly.

---

## Usage

1. **New Analysis** — Click "Nuevo análisis" in the sidebar. Enter a name, upload the validation file (`resumen_*.csv`), and click "Comenzar análisis".
2. **Review Results** — Once complete, click on the analysis name or the folder icon to open the detail view with paginated recommendations per user.
3. **Give Feedback** — In the detail view, mark each recommendation as useful (Sí) or not useful (No), then click "Guardar feedback".
4. **Retrain Model** — From the home page, click "Reentrenar modelo con feedback" after accumulating enough feedback. The retrained model is saved to `models/modulo_recomendacion_roles/catboost_retrained.joblib`.
5. **Download / Delete** — Use the download (↓) and delete icons on each analysis row.

---

## Project Structure

```
CMPC_Memoria/
├── streamlit_app.py          # Entry point: streamlit run streamlit_app.py
├── requirements.txt
├── app/
│   ├── app.py                # Streamlit app & routing
│   ├── pipeline.py           # Bridge between UI and ML pipeline
│   ├── styles.py             # CSS & theming
│   └── views/
│       ├── home.py           # Analysis list + retrain button
│       ├── new_analysis.py   # Create new analysis
│       └── analysis_detail.py# Results, feedback, download
├── database/
│   └── db.py                 # SQLite persistence (cmpc.db created at runtime)
├── main/
│   ├── cmpc_role_recomender.py
│   ├── modulo_similaridad/   # User similarity (KernelPCA + cosine)
│   └── modulo_recomendacion_roles/
│       ├── predictor.py      # CatBoost/LightGBM inference
│       └── data/
│           └── generate_negative_cases.py  # Training data + retrain
├── models/
│   └── modulo_recomendacion_roles/
│       └── grid_search/      # Pre-trained model .joblib files
├── data/                     # NOT in git – place SAP exports here
│   └── processed/            # resumen_*.csv validation files
└── documentation/            # Technical documentation
```

---

## Data Files Required in `data/`

| File | Description |
|------|-------------|
| `AGR_USERS.xlsx` | User–role assignments from SAP |
| `USER_ADDR_IDAD3.xlsx` | User attributes: department, function |

Validation files (`resumen_YYYY.csv`) are uploaded through the interface.

---

## Documentation

- [Streamlit Interface](documentation/streamlit_interface.md) — Architecture, routing, views, styling
- [Feedback System](documentation/feedback_system.md) — Feedback pipeline, retraining process


