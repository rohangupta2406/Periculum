# Project Risk Predictor (Periculum)
### Quantitative Software Project Risk Assessment & Decision Support Tool

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![Tests Passing](https://img.shields.io/badge/pytest-40%20passed-brightgreen.svg)]()
[![Framework](https://img.shields.io/badge/UI-Streamlit-red.svg)](https://streamlit.io/)

---

## 1. Project Overview & Problem Statement

Software project delivery risks often remain unmonitored until critical deadlines are missed. Traditional status reporting relies heavily on subjective, qualitative assessments that obscure emerging bottlenecks in schedule, resources, quality, and scope.

**Periculum** is an explainable, rule-based decision support system designed to evaluate software project health quantitatively. It ingests standard project tracking metrics, calculates derived indicators, scores risk across core dimensions, classifies the overall risk level, provides an evidence-based breakdown of risk drivers, and recommends concrete mitigation strategies.

> [!NOTE]
> **Design Philosophy**: Periculum is a deterministic, rule-based prototype grounded in established software engineering and project management principles (Earned Value Management, defect growth tracking, workload allocation). It does not claim statistical machine learning prediction of real-world outcomes.

---

## 2. Implemented Features

| Feature Area | Description |
| :--- | :--- |
| **Interactive Web Dashboard** | Streamlit-based UI with organized inputs, presets, and real-time metric cards. |
| **Strict Input Validation** | Safeguards against negative values, impossible task bounds, and zero denominators. |
| **Derived Indicator Engine** | Automated computation of schedule variance, workload spread, defect growth, and scope churn. |
| **Four Core Risk Categories** | Schedule Risk (35%), Resource Risk (20%), Quality Risk (20%), Requirement Risk (20%). |
| **Composite Scoring & Classification** | Normalized score (0–100) and three-tier classification: `LOW` (0–39.9), `MEDIUM` (40–69.9), `HIGH` (70–100). |
| **Explainability & Recommendations** | Clear natural-language contributing factors and targeted mitigation strategies. |
| **Interactive Visualizations** | Plotly category comparison bar chart and multi-dimensional risk radar chart. |
| **Sample Datasets & Presets** | 4 curated test datasets with one-click sidebar loading in the UI. |
| **Automated Testing Suite** | 40 unit and integration tests passing with 100% success rate. |
| **Optional Budget Risk** | Optional 5th category (5% weight) comparing spending progress against delivered work. |

---

## 3. Technology Stack & Rationale

- **Language**: Python 3.11
  - Clean syntax, strong typing via `dataclasses`, and rich scientific/engineering libraries.
- **Frontend / Dashboard**: Streamlit (`streamlit>=1.35.0`)
  - Enables rapid, production-ready interactive web application development in pure Python with zero front-end overhead.
- **Data Visualization**: Plotly (`plotly>=5.20.0`)
  - Generates responsive, interactive web charts (bar charts, thresholds, and radar plots).
- **Data Processing**: Pandas (`pandas>=2.0.0`)
  - Facilitates tabular metric transformations and summaries.
- **Testing Framework**: Pytest (`pytest>=8.0.0`)
  - Industry-standard test runner providing clean assertions, parameterized testing, and granular reporting.

---

## 4. Project Directory Structure

```
Periculum/
├── app.py                      # Interactive Streamlit web application & presentation
├── calculations.py             # Data models, input validation, and derived indicators
├── risk_engine.py              # Component normalization, weighted scoring, and classification
├── recommendations.py          # Evidence-backed explainability & targeted mitigations
├── requirements.txt            # Python dependencies
├── README.md                   # Project overview, setup guide, and documentation
├── .gitignore                  # Git exclusions for Python, pytest, and caches
├── docs/
│   ├── architecture.md         # System design, data flow, and module responsibilities
│   ├── assumptions.md          # Complete mathematical formulas, weights, and assumptions
│   └── testing.md              # Test execution log and coverage report
├── sample_data/
│   ├── example_project.json    # Healthy baseline scenario (LOW risk)
│   ├── delayed_project.json    # Schedule slippage scenario (HIGH schedule risk)
│   ├── quality_crisis_project.json # Defect escalation scenario (HIGH quality risk)
│   └── understaffed_project.json   # Resource shortage scenario (HIGH resource risk)
└── tests/
    ├── __init__.py
    ├── test_calculations.py    # Unit tests for derived indicators and zero division
    ├── test_validation.py      # Boundary tests and input validation error checks
    ├── test_risk_engine.py     # Threshold, determinism, and weighted scoring tests
    └── test_end_to_end.py      # Integration tests validating all sample datasets
```

---

## 5. Installation and Setup Instructions

### Prerequisites
- Python 3.11 installed and available in your environment path.
- Git (optional, for version management).

### Step 1: Clone or Navigate to the Workspace
```powershell
cd c:\Users\rohan\OneDrive\Desktop\Periculum
```

### Step 2: (Optional) Create and Activate Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 3: Install Required Dependencies
```powershell
pip install -r requirements.txt
```

---

## 6. How to Run the Application

Launch the Streamlit web dashboard locally:

```powershell
streamlit run app.py
```

Streamlit will open the application in your default web browser at `http://localhost:8501`.

### Demonstration Workflow for Evaluators:
1. **Load a Preset**: Use the sidebar select-box to choose a preset (e.g., *Healthy Baseline*, *Severely Delayed*, *Quality Crisis*, or *Understaffed Team*).
2. **Review Inputs**: Observe how metrics pre-populate across Schedule, Resources, Quality, and Requirements.
3. **Execute Assessment**: Click **"Calculate Risk Assessment"**.
4. **Inspect Results**:
   - **Overall Risk Gauge & Badge**: View score and `LOW`, `MEDIUM`, or `HIGH` status.
   - **Key KPIs**: View task progress, schedule variance, team staffing %, and defect ratios.
   - **Interactive Charts**: Compare category scores against Medium (40) and High (70) threshold lines.
   - **Evidence & Mitigations**: Expand individual category cards to see the exact numerical indicators driving each score and corresponding SEPM recommendations.
5. **Export Report**: Click **"Download Assessment Report (JSON)"** to download the structured assessment file.

---

## 7. How to Run Automated Tests

To execute the entire 40-test automated suite with verbose reporting:

```powershell
pytest -v
```

Expected output:
```
============================= 40 passed in 0.14s ==============================
```

---

## 8. Sample Scenarios & Expected Behavior

| Scenario Dataset | Key Condition | Expected Category Risk | Expected Overall Risk |
| :--- | :--- | :--- | :--- |
| `example_project.json` | Schedule on track, full team, low defect count | All categories $< 40$ | **LOW RISK** ($\approx 12–25$) |
| `delayed_project.json` | 40% progress vs 83% time elapsed, 30 delayed tasks | Schedule Risk $\ge 70$ | **MEDIUM to HIGH RISK** |
| `quality_crisis_project.json` | 28 bugs, 9 critical, rapid defect influx | Quality Risk $\ge 75$ | **MEDIUM to HIGH RISK** |
| `understaffed_project.json` | 50% staffing deficit, 180% peak individual load | Resource Risk $\ge 75$ | **MEDIUM to HIGH RISK** |

---

## 9. Current Limitations

1. **Rule-Based Design**: Thresholds and weights are heuristic design assumptions rather than empirically trained machine learning parameters.
2. **Single-Snapshot Assessment**: The prototype assesses project state at a single point in time. Historical trends across sprints are represented via previous-period inputs rather than continuous database tracking.
3. **Subjective Workload Metrics**: Team workload percentages depend on honest self-reporting or estimation accuracy by the project manager.

---

## 10. Future Roadmap

- **v0.2.0 (Persistence & Tracking)**:
  - SQLite database storage for historical assessments and sprint-over-sprint trend graphs.
  - Interactive Risk Register with likelihood, impact, mitigation owner, and status tracking.
- **v0.3.0 (Governance & Integration)**:
  - Fully integrated budget and Earned Value Management (EVM) tracking (CPI/SPI).
  - Configurable risk thresholds and automated threshold alerts.
- **v1.0.0 (Advanced Analytics)**:
  - Optional statistical baselines and anomaly detection if historical project datasets are connected.
  - Retain the rule-based engine as an interpretable, transparent core.

