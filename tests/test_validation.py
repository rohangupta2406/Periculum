"""
test_validation.py
===================
Unit tests for input validation and boundary checks in calculations.py.
"""

import pytest
from calculations import (
    ProjectInput,
    ScheduleMetrics,
    ResourceMetrics,
    QualityMetrics,
    RequirementMetrics,
    BudgetMetrics,
    validate_project_input,
)


def get_base_project() -> ProjectInput:
    """Returns a valid baseline project input."""
    return ProjectInput(
        project_name="Base Project",
        schedule=ScheduleMetrics(
            total_duration_days=100.0,
            days_elapsed=50.0,
            total_tasks=50,
            completed_tasks=25,
            delayed_tasks=2
        ),
        resource=ResourceMetrics(
            required_team_members=5.0,
            available_team_members=5.0,
            team_workload_pct=100.0,
            highest_individual_workload_pct=100.0
        ),
        quality=QualityMetrics(
            open_bugs=4,
            critical_bugs=1,
            previous_period_bugs=5,
            current_period_bugs=4
        ),
        requirement=RequirementMetrics(
            total_requirements=30,
            changed_requirements=3,
            current_period_changes=1,
            major_changes=0
        ),
        enable_budget=False,
        budget=None
    )


def test_valid_project_passes_validation():
    """A completely valid project should pass validation without errors."""
    project = get_base_project()
    res = validate_project_input(project)
    assert res.is_valid is True
    assert len(res.errors) == 0


def test_invalid_negative_duration():
    """Negative total duration must fail validation."""
    project = get_base_project()
    project.schedule.total_duration_days = -10.0
    res = validate_project_input(project)
    assert res.is_valid is False
    assert any("duration must be greater than 0" in e for e in res.errors)


def test_zero_duration():
    """Zero total duration must fail validation (division by zero prevention)."""
    project = get_base_project()
    project.schedule.total_duration_days = 0.0
    res = validate_project_input(project)
    assert res.is_valid is False
    assert any("duration must be greater than 0" in e for e in res.errors)


def test_negative_days_elapsed():
    """Negative elapsed days must fail validation."""
    project = get_base_project()
    project.schedule.days_elapsed = -5.0
    res = validate_project_input(project)
    assert res.is_valid is False
    assert any("Days elapsed cannot be negative" in e for e in res.errors)


def test_completed_tasks_exceeding_total_tasks():
    """Completed tasks > total tasks must fail validation."""
    project = get_base_project()
    project.schedule.total_tasks = 20
    project.schedule.completed_tasks = 25
    res = validate_project_input(project)
    assert res.is_valid is False
    assert any("Completed tasks (25) cannot exceed total tasks (20)" in e for e in res.errors)


def test_delayed_tasks_exceeding_total_tasks():
    """Delayed tasks > total tasks must fail validation."""
    project = get_base_project()
    project.schedule.total_tasks = 20
    project.schedule.delayed_tasks = 25
    res = validate_project_input(project)
    assert res.is_valid is False
    assert any("Delayed tasks (25) cannot exceed total tasks (20)" in e for e in res.errors)


def test_zero_total_tasks_is_handled_safely():
    """Zero total tasks with zero completed/delayed should be valid with a warning."""
    project = get_base_project()
    project.schedule.total_tasks = 0
    project.schedule.completed_tasks = 0
    project.schedule.delayed_tasks = 0
    res = validate_project_input(project)
    assert res.is_valid is True
    assert any("Total tasks is 0" in w for w in res.warnings)


def test_completed_tasks_exceeding_zero_total_tasks():
    """Completed tasks > 0 when total_tasks == 0 must fail validation."""
    project = get_base_project()
    project.schedule.total_tasks = 0
    project.schedule.completed_tasks = 3
    project.schedule.delayed_tasks = 0
    res = validate_project_input(project)
    assert res.is_valid is False
    assert any("Completed tasks (3) cannot exceed total tasks (0)" in e for e in res.errors)


def test_delayed_tasks_exceeding_zero_total_tasks():
    """Delayed tasks > 0 when total_tasks == 0 must fail validation."""
    project = get_base_project()
    project.schedule.total_tasks = 0
    project.schedule.completed_tasks = 0
    project.schedule.delayed_tasks = 2
    res = validate_project_input(project)
    assert res.is_valid is False
    assert any("Delayed tasks (2) cannot exceed total tasks (0)" in e for e in res.errors)


def test_overdue_project_produces_warning():
    """An overdue project is allowed with an explicit warning."""
    project = get_base_project()
    project.schedule.total_duration_days = 100.0
    project.schedule.days_elapsed = 110.0
    res = validate_project_input(project)
    assert res.is_valid is True
    assert any("Project is overdue" in w for w in res.warnings)


def test_resource_negative_team_members():
    """Required team members <= 0 must fail validation."""
    project = get_base_project()
    project.resource.required_team_members = 0
    res = validate_project_input(project)
    assert res.is_valid is False
    assert any("Required team members must be greater than 0" in e for e in res.errors)


def test_quality_critical_exceeding_open_bugs():
    """Critical bugs > open bugs must fail validation."""
    project = get_base_project()
    project.quality.open_bugs = 3
    project.quality.critical_bugs = 5
    res = validate_project_input(project)
    assert res.is_valid is False
    assert any("Critical bugs (5) cannot exceed total open bugs (3)" in e for e in res.errors)


def test_quality_negative_bugs():
    """Negative bug counts must fail validation."""
    project = get_base_project()
    project.quality.open_bugs = -2
    res = validate_project_input(project)
    assert res.is_valid is False
    assert any("Open bugs cannot be negative" in e for e in res.errors)


def test_requirements_changed_exceeding_total():
    """Changed requirements > total requirements must fail validation."""
    project = get_base_project()
    project.requirement.total_requirements = 10
    project.requirement.changed_requirements = 15
    res = validate_project_input(project)
    assert res.is_valid is False
    assert any("Changed requirements (15) cannot exceed total requirements (10)" in e for e in res.errors)


def test_changed_requirements_exceeding_zero_total_requirements():
    """Changed requirements > 0 when total_requirements == 0 must fail validation."""
    project = get_base_project()
    project.requirement.total_requirements = 0
    project.requirement.changed_requirements = 2
    res = validate_project_input(project)
    assert res.is_valid is False
    assert any("Changed requirements (2) cannot exceed total requirements (0)" in e for e in res.errors)


def test_zero_total_requirements_with_zero_changed_is_valid():
    """Zero total requirements with zero changed requirements is valid with a warning."""
    project = get_base_project()
    project.requirement.total_requirements = 0
    project.requirement.changed_requirements = 0
    project.requirement.current_period_changes = 0
    project.requirement.major_changes = 0
    res = validate_project_input(project)
    assert res.is_valid is True
    assert any("Total requirements is 0" in w for w in res.warnings)


def test_requirements_major_exceeding_changed():
    """Major changes > changed requirements must fail validation."""
    project = get_base_project()
    project.requirement.changed_requirements = 2
    project.requirement.major_changes = 5
    res = validate_project_input(project)
    assert res.is_valid is False
    assert any("Major changes (5) cannot exceed changed requirements (2)" in e for e in res.errors)


def test_optional_budget_validation():
    """When budget is enabled, invalid budget figures must fail validation."""
    project = get_base_project()
    project.enable_budget = True
    project.budget = BudgetMetrics(
        total_budget=-5000.0,
        amount_spent=1000.0,
        work_completed_pct=50.0
    )
    res = validate_project_input(project)
    assert res.is_valid is False
    assert any("Total budget must be greater than 0" in e for e in res.errors)
