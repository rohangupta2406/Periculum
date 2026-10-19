"""
test_calculations.py
======================
Unit tests for derived metric calculations and division-by-zero safeguards in calculations.py.
"""

import pytest
from calculations import (
    ScheduleMetrics,
    ResourceMetrics,
    QualityMetrics,
    RequirementMetrics,
    BudgetMetrics,
    calculate_schedule_indicators,
    calculate_resource_indicators,
    calculate_quality_indicators,
    calculate_requirement_indicators,
    calculate_budget_indicators,
)


def test_schedule_indicators_standard():
    """Verify schedule calculations for a standard in-flight project."""
    s = ScheduleMetrics(
        total_duration_days=100.0,
        days_elapsed=40.0,
        total_tasks=80,
        completed_tasks=40,
        delayed_tasks=4
    )
    ind = calculate_schedule_indicators(s)
    assert ind.task_progress_pct == 50.0
    assert ind.time_elapsed_pct == 40.0
    assert ind.schedule_variance == 10.0  # +10% ahead
    assert ind.remaining_work_pct == 50.0
    assert ind.remaining_time_pct == 60.0
    assert ind.delayed_task_ratio_pct == 5.0
    assert ind.is_overdue is False
    assert ind.days_overdue == 0.0


def test_schedule_indicators_zero_tasks():
    """Verify safe handling of 0 total tasks without ZeroDivisionError."""
    s = ScheduleMetrics(
        total_duration_days=50.0,
        days_elapsed=25.0,
        total_tasks=0,
        completed_tasks=0,
        delayed_tasks=0
    )
    ind = calculate_schedule_indicators(s)
    assert ind.task_progress_pct == 0.0
    assert ind.delayed_task_ratio_pct == 0.0
    assert ind.remaining_work_pct == 100.0
    assert ind.schedule_variance == -50.0


def test_schedule_indicators_overdue_project():
    """Verify overdue project calculations when days elapsed exceeds duration."""
    s = ScheduleMetrics(
        total_duration_days=60.0,
        days_elapsed=75.0,
        total_tasks=50,
        completed_tasks=35,
        delayed_tasks=10
    )
    ind = calculate_schedule_indicators(s)
    assert ind.is_overdue is True
    assert ind.days_overdue == 15.0
    assert ind.time_elapsed_pct == 125.0
    assert ind.task_progress_pct == 70.0
    assert ind.schedule_variance == -55.0
    assert ind.remaining_time_pct == 0.0
    assert ind.work_to_time_ratio == 999.0  # Safe maximal indicator for overdue with remaining work


def test_resource_indicators_shortage_and_imbalance():
    """Verify resource availability and workload imbalance calculations."""
    r = ResourceMetrics(
        required_team_members=10.0,
        available_team_members=7.0,
        team_workload_pct=110.0,
        highest_individual_workload_pct=140.0
    )
    ind = calculate_resource_indicators(r)
    assert ind.team_availability_pct == 70.0
    assert ind.availability_shortfall_pct == 30.0
    assert ind.resource_shortage_headcount == 3.0
    assert ind.workload_imbalance_pct == 30.0  # 140 - 110
    assert ind.average_overload_pct == 10.0     # 110 - 100
    assert ind.peak_overload_pct == 40.0        # 140 - 100


def test_quality_indicators_zero_previous_period():
    """Verify previous-period bug count == 0 avoids ZeroDivisionError and sets safe indicator."""
    q = QualityMetrics(
        open_bugs=5,
        critical_bugs=2,
        previous_period_bugs=0,
        current_period_bugs=4
    )
    ind = calculate_quality_indicators(q)
    assert ind.critical_bug_ratio_pct == 40.0
    assert ind.bug_growth_pct is None
    assert ind.bug_growth_absolute == 4
    assert ind.is_baseline_zero is True


def test_quality_indicators_with_positive_growth():
    """Verify bug growth percentage calculation when previous count > 0."""
    q = QualityMetrics(
        open_bugs=15,
        critical_bugs=3,
        previous_period_bugs=10,
        current_period_bugs=15
    )
    ind = calculate_quality_indicators(q)
    assert ind.critical_bug_ratio_pct == 20.0
    assert ind.bug_growth_pct == 50.0  # (15 - 10) / 10 * 100
    assert ind.bug_growth_absolute == 5
    assert ind.is_baseline_zero is False


def test_quality_indicators_zero_bugs_total():
    """Verify zero open bugs yields 0% critical ratio safely."""
    q = QualityMetrics(
        open_bugs=0,
        critical_bugs=0,
        previous_period_bugs=0,
        current_period_bugs=0
    )
    ind = calculate_quality_indicators(q)
    assert ind.critical_bug_ratio_pct == 0.0
    assert ind.bug_growth_pct is None
    assert ind.bug_growth_absolute == 0


def test_requirement_indicators():
    """Verify requirement churn and major changes ratios."""
    rq = RequirementMetrics(
        total_requirements=40,
        changed_requirements=10,
        current_period_changes=4,
        major_changes=2
    )
    ind = calculate_requirement_indicators(rq)
    assert ind.requirement_change_rate_pct == 25.0
    assert ind.change_frequency_pct == 10.0
    assert ind.major_change_ratio_pct == 20.0


def test_requirement_indicators_zero_total():
    """Verify 0 total requirements handled safely."""
    rq = RequirementMetrics(
        total_requirements=0,
        changed_requirements=0,
        current_period_changes=0,
        major_changes=0
    )
    ind = calculate_requirement_indicators(rq)
    assert ind.requirement_change_rate_pct == 0.0
    assert ind.major_change_ratio_pct == 0.0


def test_budget_indicators():
    """Verify optional budget cost variance and burn ratio."""
    b = BudgetMetrics(
        total_budget=100000.0,
        amount_spent=60000.0,
        work_completed_pct=40.0
    )
    ind = calculate_budget_indicators(b, work_progress_pct=40.0)
    assert ind.budget_spent_pct == 60.0
    assert ind.cost_variance_proxy == -20.0  # 40 - 60
    assert ind.burn_to_progress_ratio == 1.5   # 60 / 40
