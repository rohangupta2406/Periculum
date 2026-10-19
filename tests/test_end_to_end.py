"""
test_end_to_end.py
===================
End-to-end integration tests loading each sample project dataset,
running complete risk assessments, generating mitigations, and verifying output consistency.
"""

import json
from pathlib import Path
import pytest

from calculations import (
    ProjectInput,
    ScheduleMetrics,
    ResourceMetrics,
    QualityMetrics,
    RequirementMetrics,
    BudgetMetrics,
    validate_project_input,
    calculate_all_indicators,
)
from risk_engine import calculate_overall_risk, RiskLevel
from recommendations import generate_assessment


SAMPLE_DATA_DIR = Path(__file__).parent.parent / "sample_data"


def load_project_from_json(filename: str) -> ProjectInput:
    filepath = SAMPLE_DATA_DIR / filename
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    b_data = data.get("budget")
    budget_obj = None
    if b_data:
        budget_obj = BudgetMetrics(
            total_budget=float(b_data["total_budget"]),
            amount_spent=float(b_data["amount_spent"]),
            work_completed_pct=float(b_data["work_completed_pct"])
        )

    return ProjectInput(
        project_name=data["project_name"],
        schedule=ScheduleMetrics(**data["schedule"]),
        resource=ResourceMetrics(**data["resource"]),
        quality=QualityMetrics(**data["quality"]),
        requirement=RequirementMetrics(**data["requirement"]),
        enable_budget=data.get("enable_budget", False),
        budget=budget_obj
    )


def test_example_project_healthy():
    """Verify healthy project sample data runs cleanly and evaluates as LOW risk."""
    project = load_project_from_json("example_project.json")
    val = validate_project_input(project)
    assert val.is_valid is True

    indicators = calculate_all_indicators(project)
    assert indicators.schedule.task_progress_pct > 50.0

    result = calculate_overall_risk(project, indicators)
    assert result.overall_level == RiskLevel.LOW
    assert result.overall_score < 40.0

    assessment = generate_assessment(result, project)
    assert len(assessment.key_takeaways) > 0
    assert "Schedule" in assessment.categories
    assert "Resource" in assessment.categories
    assert "Quality" in assessment.categories
    assert "Requirement" in assessment.categories


def test_delayed_project_evaluates_high_schedule_risk():
    """Verify delayed project dataset triggers high schedule risk and proper mitigations."""
    project = load_project_from_json("delayed_project.json")
    val = validate_project_input(project)
    assert val.is_valid is True

    indicators = calculate_all_indicators(project)
    assert indicators.schedule.schedule_variance < 0

    result = calculate_overall_risk(project, indicators)
    assert result.category_results["Schedule"].score >= 70.0
    assert result.category_results["Schedule"].level == RiskLevel.HIGH

    assessment = generate_assessment(result, project)
    sched_assessment = assessment.categories["Schedule"]
    assert any("Delayed Tasks: 30" in f for f in sched_assessment.contributing_factors)
    assert len(sched_assessment.mitigations) > 0


def test_quality_crisis_project_evaluates_high_quality_risk():
    """Verify quality crisis dataset triggers high quality risk and swarm recommendations."""
    project = load_project_from_json("quality_crisis_project.json")
    val = validate_project_input(project)
    assert val.is_valid is True

    indicators = calculate_all_indicators(project)
    assert indicators.quality.critical_bug_ratio_pct > 0

    result = calculate_overall_risk(project, indicators)
    assert result.category_results["Quality"].score >= 70.0
    assert result.category_results["Quality"].level == RiskLevel.HIGH

    assessment = generate_assessment(result, project)
    qual_assessment = assessment.categories["Quality"]
    assert any("Critical Defects Present: 9" in f for f in qual_assessment.contributing_factors)
    assert any("critical defect" in m.lower() for m in qual_assessment.mitigations)


def test_understaffed_project_evaluates_high_resource_risk():
    """Verify understaffed dataset triggers high resource risk and rebalance recommendations."""
    project = load_project_from_json("understaffed_project.json")
    val = validate_project_input(project)
    assert val.is_valid is True

    indicators = calculate_all_indicators(project)
    assert indicators.resource.team_availability_pct == 50.0

    result = calculate_overall_risk(project, indicators)
    assert result.category_results["Resource"].score >= 70.0
    assert result.category_results["Resource"].level == RiskLevel.HIGH

    assessment = generate_assessment(result, project)
    res_assessment = assessment.categories["Resource"]
    assert any("Staffing Deficit" in f for f in res_assessment.contributing_factors)
    assert any("rebalance" in m.lower() or "staffing" in m.lower() for m in res_assessment.mitigations)
