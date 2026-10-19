"""
test_risk_engine.py
====================
Automated test suite for the risk scoring engine, weight redistribution,
classification boundaries, determinism, and recommendations.
"""

import pytest
from calculations import (
    ProjectInput,
    ScheduleMetrics,
    ResourceMetrics,
    QualityMetrics,
    RequirementMetrics,
    BudgetMetrics,
)
from risk_engine import (
    RiskLevel,
    classify_risk,
    calculate_overall_risk,
    calculate_schedule_risk,
    calculate_resource_risk,
    calculate_quality_risk,
    calculate_requirement_risk,
)
from recommendations import generate_assessment


def create_healthy_project() -> ProjectInput:
    """Returns a healthy, low-risk project."""
    return ProjectInput(
        project_name="Healthy Project",
        schedule=ScheduleMetrics(
            total_duration_days=100.0,
            days_elapsed=40.0,
            total_tasks=100,
            completed_tasks=45,
            delayed_tasks=0
        ),
        resource=ResourceMetrics(
            required_team_members=6.0,
            available_team_members=6.0,
            team_workload_pct=90.0,
            highest_individual_workload_pct=95.0
        ),
        quality=QualityMetrics(
            open_bugs=2,
            critical_bugs=0,
            previous_period_bugs=3,
            current_period_bugs=2
        ),
        requirement=RequirementMetrics(
            total_requirements=40,
            changed_requirements=2,
            current_period_changes=0,
            major_changes=0
        ),
        enable_budget=False,
        budget=None
    )


def test_classification_threshold_boundaries():
    """
    Test risk classification immediately below, at, and above classification thresholds:
      - 0 to 39.999... -> LOW
      - 40.0 to 69.999... -> MEDIUM
      - 70.0 to 100.0   -> HIGH
    """
    # LOW boundaries
    assert classify_risk(0.0) == RiskLevel.LOW
    assert classify_risk(39.9) == RiskLevel.LOW
    assert classify_risk(39.99) == RiskLevel.LOW

    # Boundary at 40.0
    assert classify_risk(40.0) == RiskLevel.MEDIUM
    assert classify_risk(40.01) == RiskLevel.MEDIUM

    # MEDIUM boundaries
    assert classify_risk(55.0) == RiskLevel.MEDIUM
    assert classify_risk(69.9) == RiskLevel.MEDIUM
    assert classify_risk(69.99) == RiskLevel.MEDIUM

    # Boundary at 70.0
    assert classify_risk(70.0) == RiskLevel.HIGH
    assert classify_risk(70.01) == RiskLevel.HIGH

    # HIGH boundaries
    assert classify_risk(100.0) == RiskLevel.HIGH

    # Out of range clamped safely
    assert classify_risk(-10.0) == RiskLevel.LOW
    assert classify_risk(150.0) == RiskLevel.HIGH


def test_healthy_project_scores_low_risk():
    """A healthy project should yield a LOW overall risk classification and score < 40."""
    project = create_healthy_project()
    result = calculate_overall_risk(project)

    assert result.overall_level == RiskLevel.LOW
    assert 0.0 <= result.overall_score < 40.0
    for cat_name, cat_res in result.category_results.items():
        assert 0.0 <= cat_res.score <= 100.0
        assert cat_res.level == RiskLevel.LOW


def test_project_significantly_behind_schedule():
    """A project significantly behind schedule should yield high schedule risk."""
    project = create_healthy_project()
    project.schedule.days_elapsed = 80.0
    project.schedule.completed_tasks = 20  # 20% progress vs 80% time elapsed
    project.schedule.delayed_tasks = 35    # 35% delayed tasks

    result = calculate_overall_risk(project)
    sched_res = result.category_results["Schedule"]

    assert sched_res.score >= 70.0
    assert sched_res.level == RiskLevel.HIGH
    # Confirm overall risk score increased accordingly
    assert result.overall_score > 35.0


def test_team_availability_shortage_scores_high_resource_risk():
    """A project with 50% staffing shortage and overload should trigger high resource risk."""
    project = create_healthy_project()
    project.resource.required_team_members = 10.0
    project.resource.available_team_members = 5.0  # 50% shortfall
    project.resource.team_workload_pct = 140.0
    project.resource.highest_individual_workload_pct = 180.0

    result = calculate_overall_risk(project)
    res_res = result.category_results["Resource"]

    assert res_res.score >= 70.0
    assert res_res.level == RiskLevel.HIGH


def test_high_critical_defects_scores_high_quality_risk():
    """A project with multiple critical defects should trigger high quality risk."""
    project = create_healthy_project()
    project.quality.open_bugs = 15
    project.quality.critical_bugs = 7
    project.quality.previous_period_bugs = 10
    project.quality.current_period_bugs = 15

    result = calculate_overall_risk(project)
    qual_res = result.category_results["Quality"]

    assert qual_res.score >= 70.0
    assert qual_res.level == RiskLevel.HIGH


def test_increasing_bug_count_with_previous_count_zero():
    """Verify bug count increase from zero baseline is handled safely and produces risk."""
    project = create_healthy_project()
    project.quality.open_bugs = 6
    project.quality.critical_bugs = 1
    project.quality.previous_period_bugs = 0
    project.quality.current_period_bugs = 6

    result = calculate_overall_risk(project)
    qual_res = result.category_results["Quality"]

    # Must calculate safely without division error
    assert 0.0 <= qual_res.score <= 100.0
    assert "bug_growth" in qual_res.components
    assert qual_res.components["bug_growth"].score > 0.0


def test_high_requirement_change_rate_scores_high_requirement_risk():
    """A project with 40% requirement changes and architectural revisions triggers high risk."""
    project = create_healthy_project()
    project.requirement.total_requirements = 50
    project.requirement.changed_requirements = 25  # 50% change rate
    project.requirement.current_period_changes = 15
    project.requirement.major_changes = 6

    result = calculate_overall_risk(project)
    req_res = result.category_results["Requirement"]

    assert req_res.score >= 70.0
    assert req_res.level == RiskLevel.HIGH


def test_overall_weights_sum_to_100_percent_when_budget_disabled():
    """When budget is disabled, redistributed weights must sum to 100%."""
    project = create_healthy_project()
    project.enable_budget = False
    result = calculate_overall_risk(project)

    weights_sum = sum(result.category_weights.values())
    assert abs(weights_sum - 100.0) < 0.05
    assert "Budget" not in result.category_weights
    # Schedule should be 35/95 * 100 = 36.84%
    assert abs(result.category_weights["Schedule"] - 36.84) < 0.05
    # Resource, Quality, Requirement should each be 20/95 * 100 = 21.05%
    assert abs(result.category_weights["Resource"] - 21.05) < 0.05


def test_overall_weights_sum_to_100_percent_when_budget_enabled():
    """When budget is enabled, weights (35, 20, 20, 20, 5) must sum to 100%."""
    project = create_healthy_project()
    project.enable_budget = True
    project.budget = BudgetMetrics(
        total_budget=100000.0,
        amount_spent=80000.0,
        work_completed_pct=40.0
    )
    result = calculate_overall_risk(project)

    weights_sum = sum(result.category_weights.values())
    assert abs(weights_sum - 100.0) < 0.05
    assert "Budget" in result.category_weights
    assert result.category_weights["Budget"] == 5.0
    assert result.category_weights["Schedule"] == 35.0


def test_score_range_clamping():
    """Even with extreme catastrophic inputs, all scores must remain <= 100.0 and >= 0.0."""
    project = ProjectInput(
        project_name="Catastrophic Project",
        schedule=ScheduleMetrics(
            total_duration_days=50.0,
            days_elapsed=200.0,  # 300% overdue
            total_tasks=100,
            completed_tasks=5,
            delayed_tasks=90
        ),
        resource=ResourceMetrics(
            required_team_members=20.0,
            available_team_members=1.0,
            team_workload_pct=300.0,
            highest_individual_workload_pct=350.0
        ),
        quality=QualityMetrics(
            open_bugs=100,
            critical_bugs=50,
            previous_period_bugs=5,
            current_period_bugs=90
        ),
        requirement=RequirementMetrics(
            total_requirements=100,
            changed_requirements=100,
            current_period_changes=80,
            major_changes=40
        ),
        enable_budget=True,
        budget=BudgetMetrics(
            total_budget=100000.0,
            amount_spent=300000.0,
            work_completed_pct=5.0
        )
    )

    result = calculate_overall_risk(project)
    assert 0.0 <= result.overall_score <= 100.0
    assert result.overall_level == RiskLevel.HIGH
    for cat_res in result.category_results.values():
        assert 0.0 <= cat_res.score <= 100.0


def test_engine_determinism():
    """Identical valid inputs must produce identical numerical outputs across repeated executions."""
    project = create_healthy_project()
    res1 = calculate_overall_risk(project)
    res2 = calculate_overall_risk(project)

    assert res1.overall_score == res2.overall_score
    assert res1.overall_level == res2.overall_level
    for cat in res1.category_results:
        assert res1.category_results[cat].score == res2.category_results[cat].score


def test_recommendations_and_explanations_correspond_to_indicators():
    """Verify that explainability and recommendations reflect real computed indicators."""
    project = create_healthy_project()
    # Induce specific quality and schedule conditions
    project.schedule.delayed_tasks = 20
    project.quality.critical_bugs = 3
    project.quality.open_bugs = 10

    overall_res = calculate_overall_risk(project)
    assessment = generate_assessment(overall_res, project)

    # Check schedule assessment contains delayed tasks mention
    sched_assessment = assessment.categories["Schedule"]
    assert any("Delayed Tasks: 20" in f for f in sched_assessment.contributing_factors)
    assert any("delayed tasks" in m.lower() for m in sched_assessment.mitigations)

    # Check quality assessment contains critical defect mention
    qual_assessment = assessment.categories["Quality"]
    assert any("Critical Defects Present: 3" in f for f in qual_assessment.contributing_factors)
    assert any("critical defect" in m.lower() for m in qual_assessment.mitigations)
