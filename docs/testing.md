# Automated Testing and Verification Report

## 1. Testing Philosophy and Strategy

The **Project Risk Predictor** incorporates a comprehensive automated test suite engineered with `pytest`. Testing focuses on **actual business logic behavior, mathematical correctness, edge cases, and safety bounds**, rather than superficial smoke checks.

Key testing principles enforced:
1. **Zero Division Safeguards**: All derived ratios and percentages protect against zero denominators (`total_tasks=0`, `total_duration=0`, `previous_period_bugs=0`, `total_requirements=0`, `open_bugs=0`).
2. **Boundary and Threshold Rigor**: Tests evaluate classification logic at $39.9$, $40.0$, $69.9$, and $70.0$ to guarantee strict classification fidelity.
3. **Determinism**: Validates that identical inputs strictly yield identical scores across executions.
4. **Range Clamping**: Confirms that even under catastrophic input states, all component, category, and overall scores clamp strictly within $[0.0, 100.0]$.
5. **Traceable Explanations**: Asserts that qualitative explanations and mitigation suggestions correspond directly to computed numerical evidence.

---

## 2. Test Execution Results

All **40 automated tests** passed with **0 failures and 0 warnings**.

### Test Suite Summary

```
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\rohan\OneDrive\Desktop\Periculum
plugins: anyio-4.13.0
collected 40 items

tests/test_calculations.py::test_schedule_indicators_standard PASSED     [  2%]
tests/test_calculations.py::test_schedule_indicators_zero_tasks PASSED   [  5%]
tests/test_calculations.py::test_schedule_indicators_overdue_project PASSED [  7%]
tests/test_calculations.py::test_resource_indicators_shortage_and_imbalance PASSED [ 10%]
tests/test_calculations.py::test_quality_indicators_zero_previous_period PASSED [ 12%]
tests/test_calculations.py::test_quality_indicators_with_positive_growth PASSED [ 15%]
tests/test_calculations.py::test_quality_indicators_zero_bugs_total PASSED [ 17%]
tests/test_calculations.py::test_requirement_indicators PASSED           [ 20%]
tests/test_calculations.py::test_requirement_indicators_zero_total PASSED [ 22%]
tests/test_calculations.py::test_budget_indicators PASSED                [ 25%]
tests/test_end_to_end.py::test_example_project_healthy PASSED            [ 27%]
tests/test_end_to_end.py::test_delayed_project_evaluates_high_schedule_risk PASSED [ 30%]
tests/test_end_to_end.py::test_quality_crisis_project_evaluates_high_quality_risk PASSED [ 32%]
tests/test_end_to_end.py::test_understaffed_project_evaluates_high_resource_risk PASSED [ 35%]
tests/test_risk_engine.py::test_classification_threshold_boundaries PASSED [ 37%]
tests/test_risk_engine.py::test_healthy_project_scores_low_risk PASSED   [ 40%]
tests/test_risk_engine.py::test_project_significantly_behind_schedule PASSED [ 42%]
tests/test_risk_engine.py::test_team_availability_shortage_scores_high_resource_risk PASSED [ 45%]
tests/test_risk_engine.py::test_high_critical_defects_scores_high_quality_risk PASSED [ 47%]
tests/test_risk_engine.py::test_increasing_bug_count_with_previous_count_zero PASSED [ 50%]
tests/test_risk_engine.py::test_high_requirement_change_rate_scores_high_requirement_risk PASSED [ 52%]
tests/test_risk_engine.py::test_overall_weights_sum_to_100_percent_when_budget_disabled PASSED [ 55%]
tests/test_risk_engine.py::test_overall_weights_sum_to_100_percent_when_budget_enabled PASSED [ 57%]
tests/test_risk_engine.py::test_score_range_clamping PASSED              [ 60%]
tests/test_risk_engine.py::test_engine_determinism PASSED                [ 62%]
tests/test_risk_engine.py::test_recommendations_and_explanations_correspond_to_indicators PASSED [ 65%]
tests/test_validation.py::test_valid_project_passes_validation PASSED    [ 67%]
tests/test_validation.py::test_invalid_negative_duration PASSED          [ 70%]
tests/test_validation.py::test_zero_duration PASSED                      [ 72%]
tests/test_validation.py::test_negative_days_elapsed PASSED              [ 75%]
tests/test_validation.py::test_completed_tasks_exceeding_total_tasks PASSED [ 77%]
tests/test_validation.py::test_delayed_tasks_exceeding_total_tasks PASSED [ 80%]
tests/test_validation.py::test_zero_total_tasks_is_handled_safely PASSED [ 82%]
tests/test_validation.py::test_overdue_project_produces_warning PASSED   [ 85%]
tests/test_validation.py::test_resource_negative_team_members PASSED     [ 87%]
tests/test_validation.py::test_quality_critical_exceeding_open_bugs PASSED [ 90%]
tests/test_validation.py::test_quality_negative_bugs PASSED              [ 92%]
tests/test_validation.py::test_requirements_changed_exceeding_total PASSED [ 95%]
tests/test_validation.py::test_requirements_major_exceeding_changed PASSED [ 97%]
tests/test_validation.py::test_optional_budget_validation PASSED         [100%]

============================= 40 passed in 0.14s ==============================
```

---

## 3. Test Coverage Breakdown

### Group A: Input Validation & Edge Conditions (`test_validation.py`)
- `test_valid_project_passes_validation`: Valid inputs return `is_valid=True` and no error messages.
- `test_invalid_negative_duration`: Flagged when total duration $\le 0$.
- `test_zero_duration`: Zero duration safely rejected before division.
- `test_negative_days_elapsed`: Rejects negative time progression.
- `test_completed_tasks_exceeding_total_tasks`: Semantic rule: completed cannot exceed total.
- `test_delayed_tasks_exceeding_total_tasks`: Semantic rule: delayed cannot exceed total.
- `test_zero_total_tasks_is_handled_safely`: Safe fallback to $0\%$ progress without crashing.
- `test_overdue_project_produces_warning`: Meaningful representation of project past planned deadline.
- `test_resource_negative_team_members`: Required headcount must be $> 0$.
- `test_quality_critical_exceeding_open_bugs`: Critical defects cannot exceed total open bugs.
- `test_quality_negative_bugs`: Bug counts cannot be negative.
- `test_requirements_changed_exceeding_total`: Changed requirements cannot exceed total scope.
- `test_requirements_major_exceeding_changed`: Major changes cannot exceed changed requirements.
- `test_optional_budget_validation`: Budget must be positive when enabled.

### Group B: Derived Metrics Calculations (`test_calculations.py`)
- `test_schedule_indicators_standard`: Standard schedule variance calculation.
- `test_schedule_indicators_zero_tasks`: Zero tasks produces $0\%$ progress without error.
- `test_schedule_indicators_overdue_project`: Overdue flags and days overdue correctly computed.
- `test_resource_indicators_shortage_and_imbalance`: Team availability shortfall and workload spread.
- `test_quality_indicators_zero_previous_period`: Zero baseline handled cleanly without returning `inf`.
- `test_quality_indicators_with_positive_growth`: Defect growth percentage calculated correctly.
- `test_quality_indicators_zero_bugs_total`: Zero open defects gives $0\%$ critical ratio.
- `test_requirement_indicators`: Scope churn rate and major change ratio.
- `test_budget_indicators`: Cost-to-progress variance and burn ratio.

### Group C: Risk Scoring Engine & Heuristics (`test_risk_engine.py`)
- `test_classification_threshold_boundaries`: Boundary tests for $39.9 \to \text{LOW}$, $40.0 \to \text{MEDIUM}$, $69.9 \to \text{MEDIUM}$, $70.0 \to \text{HIGH}$.
- `test_healthy_project_scores_low_risk`: Healthy inputs evaluate to `LOW` ($< 40$).
- `test_project_significantly_behind_schedule`: Severe schedule delay triggers `HIGH` schedule risk ($\ge 70$).
- `test_team_availability_shortage_scores_high_resource_risk`: Staffing deficit triggers `HIGH` resource risk ($\ge 70$).
- `test_high_critical_defects_scores_high_quality_risk`: Release-blocking defects trigger `HIGH` quality risk ($\ge 70$).
- `test_increasing_bug_count_with_previous_count_zero`: Safe, positive risk calculation for new defect influx from zero baseline.
- `test_high_requirement_change_rate_scores_high_requirement_risk`: High scope churn triggers `HIGH` requirement risk ($\ge 70$).
- `test_overall_weights_sum_to_100_percent_when_budget_disabled`: Proportional redistribution of weights sums strictly to $100\%$.
- `test_overall_weights_sum_to_100_percent_when_budget_enabled`: Five-category weights sum strictly to $100\%$.
- `test_score_range_clamping`: Catastrophic multi-failure inputs remain clamped in $[0, 100]$.
- `test_engine_determinism`: Validates identical output across repeated runs.
- `test_recommendations_and_explanations_correspond_to_indicators`: Links mitigation text to real metrics.

### Group D: End-to-End Integration Tests (`test_end_to_end.py`)
- `test_example_project_healthy`: Validates `sample_data/example_project.json`.
- `test_delayed_project_evaluates_high_schedule_risk`: Validates `sample_data/delayed_project.json`.
- `test_quality_crisis_project_evaluates_high_quality_risk`: Validates `sample_data/quality_crisis_project.json`.
- `test_understaffed_project_evaluates_high_resource_risk`: Validates `sample_data/understaffed_project.json`.

---

## 4. How to Execute Tests

To run the automated suite with full verbose reporting:

```powershell
pytest -v
```
