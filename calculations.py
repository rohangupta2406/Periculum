"""
calculations.py
================
Data models, validation, and derived metric calculations for Periculum.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class ScheduleMetrics:
    total_duration_days: float
    days_elapsed: float
    total_tasks: int
    completed_tasks: int
    delayed_tasks: int


@dataclass
class ResourceMetrics:
    required_team_members: float
    available_team_members: float
    team_workload_pct: float            # Average workload % (100% = nominal full capacity)
    highest_individual_workload_pct: float  # Maximum workload on any single team member (%)


@dataclass
class QualityMetrics:
    open_bugs: int
    critical_bugs: int
    previous_period_bugs: int
    current_period_bugs: int


@dataclass
class RequirementMetrics:
    total_requirements: int
    changed_requirements: int
    current_period_changes: int
    major_changes: int                  # Proxy for high-impact / architectural changes


@dataclass
class BudgetMetrics:
    total_budget: float
    amount_spent: float
    work_completed_pct: float           # Work progress percentage for cost-to-work comparison


@dataclass
class ProjectInput:
    project_name: str
    schedule: ScheduleMetrics
    resource: ResourceMetrics
    quality: QualityMetrics
    requirement: RequirementMetrics
    budget: Optional[BudgetMetrics] = None
    enable_budget: bool = False


@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class ScheduleIndicators:
    task_progress_pct: float
    time_elapsed_pct: float
    schedule_variance: float
    remaining_work_pct: float
    remaining_time_pct: float
    is_overdue: bool
    days_overdue: float
    delayed_task_ratio_pct: float
    work_to_time_ratio: float


@dataclass
class ResourceIndicators:
    team_availability_pct: float
    availability_shortfall_pct: float
    resource_shortage_headcount: float
    workload_imbalance_pct: float
    average_overload_pct: float
    peak_overload_pct: float


@dataclass
class QualityIndicators:
    critical_bug_ratio_pct: float
    bug_growth_pct: Optional[float]
    bug_growth_absolute: int
    is_baseline_zero: bool


@dataclass
class RequirementIndicators:
    requirement_change_rate_pct: float
    change_frequency_pct: float
    major_change_ratio_pct: float


@dataclass
class BudgetIndicators:
    budget_spent_pct: float
    cost_variance_proxy: float
    burn_to_progress_ratio: float


@dataclass
class ProjectIndicators:
    schedule: ScheduleIndicators
    resource: ResourceIndicators
    quality: QualityIndicators
    requirement: RequirementIndicators
    budget: Optional[BudgetIndicators] = None


def validate_project_input(project: ProjectInput) -> ValidationResult:
    """
    Validates user project inputs to prevent invalid math, illogical state,
    and out-of-bounds metrics. Returns a ValidationResult with errors and warnings.
    """
    errors: List[str] = []
    warnings: List[str] = []

    # Project Name
    if not project.project_name or not project.project_name.strip():
        warnings.append("Project name is blank; using 'Untitled Project'.")

    # Schedule Validation
    s = project.schedule
    if s.total_duration_days <= 0:
        errors.append("Total project duration must be greater than 0 days.")
    if s.days_elapsed < 0:
        errors.append("Days elapsed cannot be negative.")
    if s.total_tasks < 0:
        errors.append("Total tasks cannot be negative.")
    if s.completed_tasks < 0:
        errors.append("Completed tasks cannot be negative.")
    if s.delayed_tasks < 0:
        errors.append("Delayed tasks cannot be negative.")

    if s.completed_tasks > s.total_tasks:
        errors.append(
            f"Completed tasks ({s.completed_tasks}) cannot exceed total tasks ({s.total_tasks})."
        )
    if s.delayed_tasks > s.total_tasks:
        errors.append(
            f"Delayed tasks ({s.delayed_tasks}) cannot exceed total tasks ({s.total_tasks})."
        )
    if s.total_tasks > 0:
        if s.completed_tasks + s.delayed_tasks > s.total_tasks:
            warnings.append(
                f"Completed tasks ({s.completed_tasks}) + delayed tasks ({s.delayed_tasks}) "
                f"exceeds total tasks ({s.total_tasks}); assuming some completed tasks were previously delayed."
            )
    elif s.total_tasks == 0:
        if s.completed_tasks == 0 and s.delayed_tasks == 0:
            warnings.append("Total tasks is 0; task progress and delayed ratios will default to 0%.")

    if s.total_duration_days > 0 and s.days_elapsed > s.total_duration_days:
        warnings.append(
            f"Project is overdue: {s.days_elapsed} days elapsed out of {s.total_duration_days} planned days."
        )

    # Resource Validation
    r = project.resource
    if r.required_team_members <= 0:
        errors.append("Required team members must be greater than 0.")
    if r.available_team_members < 0:
        errors.append("Available team members cannot be negative.")
    if r.team_workload_pct < 0:
        errors.append("Team workload percentage cannot be negative.")
    if r.highest_individual_workload_pct < 0:
        errors.append("Highest individual workload percentage cannot be negative.")
    if r.highest_individual_workload_pct < r.team_workload_pct:
        warnings.append(
            f"Highest individual workload ({r.highest_individual_workload_pct}%) is lower than "
            f"team average ({r.team_workload_pct}%); resetting highest individual workload to match team average."
        )

    # Quality Validation
    q = project.quality
    if q.open_bugs < 0:
        errors.append("Open bugs cannot be negative.")
    if q.critical_bugs < 0:
        errors.append("Critical bugs cannot be negative.")
    if q.critical_bugs > q.open_bugs:
        errors.append(
            f"Critical bugs ({q.critical_bugs}) cannot exceed total open bugs ({q.open_bugs})."
        )
    if q.previous_period_bugs < 0:
        errors.append("Previous period bugs cannot be negative.")
    if q.current_period_bugs < 0:
        errors.append("Current period bugs cannot be negative.")

    # Requirement Validation
    rq = project.requirement
    if rq.total_requirements < 0:
        errors.append("Total requirements cannot be negative.")
    if rq.changed_requirements < 0:
        errors.append("Changed requirements cannot be negative.")
    if rq.current_period_changes < 0:
        errors.append("Current period changes cannot be negative.")
    if rq.major_changes < 0:
        errors.append("Major changes cannot be negative.")

    if rq.changed_requirements > rq.total_requirements:
        errors.append(
            f"Changed requirements ({rq.changed_requirements}) cannot exceed total requirements ({rq.total_requirements})."
        )
    if rq.total_requirements > 0:
        if rq.current_period_changes > rq.total_requirements:
            warnings.append(
                f"Current period changes ({rq.current_period_changes}) exceeds total requirements ({rq.total_requirements}), "
                f"indicating multiple revisions per requirement."
            )
    elif rq.total_requirements == 0:
        if rq.changed_requirements == 0:
            warnings.append("Total requirements is 0; change rates will default to 0%.")

    if rq.changed_requirements > 0:
        if rq.major_changes > rq.changed_requirements:
            errors.append(
                f"Major changes ({rq.major_changes}) cannot exceed changed requirements ({rq.changed_requirements})."
            )
    elif rq.major_changes > 0:
        errors.append("Major changes cannot be greater than 0 if changed requirements is 0.")

    # Optional Budget Validation
    if project.enable_budget and project.budget:
        b = project.budget
        if b.total_budget <= 0:
            errors.append("Total budget must be greater than 0 when budget evaluation is enabled.")
        if b.amount_spent < 0:
            errors.append("Amount spent cannot be negative.")
        if b.work_completed_pct < 0 or b.work_completed_pct > 100:
            errors.append("Budget work completed percentage must be between 0% and 100%.")

    return ValidationResult(
        is_valid=(len(errors) == 0),
        errors=errors,
        warnings=warnings
    )


def calculate_schedule_indicators(s: ScheduleMetrics) -> ScheduleIndicators:
    """
    Computes derived schedule indicators with zero-division safeguards
    and overdue status detection.
    """
    if s.total_tasks > 0:
        task_progress_pct = (s.completed_tasks / s.total_tasks) * 100.0
        delayed_task_ratio_pct = (s.delayed_tasks / s.total_tasks) * 100.0
    else:
        task_progress_pct = 0.0
        delayed_task_ratio_pct = 0.0

    if s.total_duration_days > 0:
        time_elapsed_pct = (s.days_elapsed / s.total_duration_days) * 100.0
    else:
        time_elapsed_pct = 0.0

    # Negative variance indicates tasks completion is behind elapsed time
    schedule_variance = task_progress_pct - time_elapsed_pct
    remaining_work_pct = max(0.0, 100.0 - task_progress_pct)
    remaining_time_pct = max(0.0, 100.0 - time_elapsed_pct)

    is_overdue = (s.days_elapsed > s.total_duration_days) and (task_progress_pct < 100.0)
    days_overdue = max(0.0, s.days_elapsed - s.total_duration_days) if is_overdue else 0.0

    if remaining_time_pct > 0:
        work_to_time_ratio = remaining_work_pct / remaining_time_pct
    else:
        # If time is exhausted but work remains, pressure is maximal
        work_to_time_ratio = 999.0 if remaining_work_pct > 0 else 0.0

    return ScheduleIndicators(
        task_progress_pct=round(task_progress_pct, 2),
        time_elapsed_pct=round(time_elapsed_pct, 2),
        schedule_variance=round(schedule_variance, 2),
        remaining_work_pct=round(remaining_work_pct, 2),
        remaining_time_pct=round(remaining_time_pct, 2),
        is_overdue=is_overdue,
        days_overdue=round(days_overdue, 1),
        delayed_task_ratio_pct=round(delayed_task_ratio_pct, 2),
        work_to_time_ratio=round(work_to_time_ratio, 2)
    )


def calculate_resource_indicators(r: ResourceMetrics) -> ResourceIndicators:
    """
    Computes team availability and workload imbalance indicators.
    Workload scale assumption: 100% represents nominal full-time allocation.
    """
    if r.required_team_members > 0:
        team_availability_pct = (r.available_team_members / r.required_team_members) * 100.0
    else:
        team_availability_pct = 0.0

    availability_shortfall_pct = max(0.0, 100.0 - team_availability_pct)
    resource_shortage_headcount = max(0.0, r.required_team_members - r.available_team_members)

    # Highest individual workload shouldn't be logically lower than average workload
    effective_highest = max(r.highest_individual_workload_pct, r.team_workload_pct)
    workload_imbalance_pct = max(0.0, effective_highest - r.team_workload_pct)

    average_overload_pct = max(0.0, r.team_workload_pct - 100.0)
    peak_overload_pct = max(0.0, effective_highest - 100.0)

    return ResourceIndicators(
        team_availability_pct=round(team_availability_pct, 2),
        availability_shortfall_pct=round(availability_shortfall_pct, 2),
        resource_shortage_headcount=round(resource_shortage_headcount, 1),
        workload_imbalance_pct=round(workload_imbalance_pct, 2),
        average_overload_pct=round(average_overload_pct, 2),
        peak_overload_pct=round(peak_overload_pct, 2)
    )


def calculate_quality_indicators(q: QualityMetrics) -> QualityIndicators:
    """
    Computes quality indicators. Handles zero bugs in previous period safely
    without division-by-zero or misleading infinite percentages.
    """
    if q.open_bugs > 0:
        critical_bug_ratio_pct = (q.critical_bugs / q.open_bugs) * 100.0
    else:
        critical_bug_ratio_pct = 0.0

    bug_growth_absolute = q.current_period_bugs - q.previous_period_bugs

    if q.previous_period_bugs > 0:
        bug_growth_pct = (bug_growth_absolute / q.previous_period_bugs) * 100.0
        is_baseline_zero = False
    else:
        # Explicitly represented as None so downstream engine handles as a new baseline
        bug_growth_pct = None
        is_baseline_zero = True

    return QualityIndicators(
        critical_bug_ratio_pct=round(critical_bug_ratio_pct, 2),
        bug_growth_pct=round(bug_growth_pct, 2) if bug_growth_pct is not None else None,
        bug_growth_absolute=bug_growth_absolute,
        is_baseline_zero=is_baseline_zero
    )


def calculate_requirement_indicators(rq: RequirementMetrics) -> RequirementIndicators:
    """
    Computes requirement change rate and volatility indicators.
    """
    if rq.total_requirements > 0:
        requirement_change_rate_pct = (rq.changed_requirements / rq.total_requirements) * 100.0
        change_frequency_pct = (rq.current_period_changes / rq.total_requirements) * 100.0
    else:
        requirement_change_rate_pct = 0.0
        change_frequency_pct = 0.0

    if rq.changed_requirements > 0:
        major_change_ratio_pct = (rq.major_changes / rq.changed_requirements) * 100.0
    else:
        major_change_ratio_pct = 0.0

    return RequirementIndicators(
        requirement_change_rate_pct=round(requirement_change_rate_pct, 2),
        change_frequency_pct=round(change_frequency_pct, 2),
        major_change_ratio_pct=round(major_change_ratio_pct, 2)
    )


def calculate_budget_indicators(
    b: BudgetMetrics,
    work_progress_pct: float
) -> BudgetIndicators:
    """
    Computes optional budget indicators comparing spend progress with work progress.
    """
    if b.total_budget > 0:
        budget_spent_pct = (b.amount_spent / b.total_budget) * 100.0
    else:
        budget_spent_pct = 0.0

    # Negative cost variance proxy indicates spending percentage exceeds work completion
    cost_variance_proxy = work_progress_pct - budget_spent_pct

    if work_progress_pct > 0:
        burn_to_progress_ratio = budget_spent_pct / work_progress_pct
    else:
        burn_to_progress_ratio = 999.0 if budget_spent_pct > 0 else 1.0

    return BudgetIndicators(
        budget_spent_pct=round(budget_spent_pct, 2),
        cost_variance_proxy=round(cost_variance_proxy, 2),
        burn_to_progress_ratio=round(burn_to_progress_ratio, 2)
    )


def calculate_all_indicators(project: ProjectInput) -> ProjectIndicators:
    """
    Computes all derived project indicators for a validated project input.
    """
    sched_ind = calculate_schedule_indicators(project.schedule)
    res_ind = calculate_resource_indicators(project.resource)
    qual_ind = calculate_quality_indicators(project.quality)
    req_ind = calculate_requirement_indicators(project.requirement)

    budget_ind = None
    if project.enable_budget and project.budget:
        budget_ind = calculate_budget_indicators(
            project.budget,
            sched_ind.task_progress_pct
        )

    return ProjectIndicators(
        schedule=sched_ind,
        resource=res_ind,
        quality=qual_ind,
        requirement=req_ind,
        budget=budget_ind
    )
