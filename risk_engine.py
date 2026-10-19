"""
risk_engine.py
===============
Deterministic risk scoring engine for Periculum.
Normalizes indicators, computes weighted category scores, and assigns classifications.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List
from calculations import (
    ProjectInput,
    ProjectIndicators,
    calculate_all_indicators,
    validate_project_input,
)


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


# Provisional Classification Thresholds
THRESHOLD_LOW_UPPER = 39.9999
THRESHOLD_MEDIUM_UPPER = 69.9999


def classify_risk(score: float) -> RiskLevel:
    """
    Classifies a 0–100 score into LOW, MEDIUM, or HIGH risk categories.
    Boundary rules:
      - 0.0 to 39.99... -> LOW
      - 40.0 to 69.99... -> MEDIUM
      - 70.0 to 100.0   -> HIGH
    """
    clamped_score = max(0.0, min(100.0, score))
    if clamped_score < 40.0:
        return RiskLevel.LOW
    elif clamped_score < 70.0:
        return RiskLevel.MEDIUM
    else:
        return RiskLevel.HIGH


@dataclass
class ComponentScore:
    name: str
    raw_value: Any
    score: float
    weight: float
    formula_description: str


@dataclass
class CategoryRiskResult:
    category_name: str
    score: float
    level: RiskLevel
    weight_in_overall: float
    components: Dict[str, ComponentScore]


@dataclass
class OverallRiskResult:
    project_name: str
    overall_score: float
    overall_level: RiskLevel
    is_budget_enabled: bool
    category_results: Dict[str, CategoryRiskResult]
    category_weights: Dict[str, float]
    indicators: ProjectIndicators


def clamp(val: float, min_val: float = 0.0, max_val: float = 100.0) -> float:
    """Clamps a floating point value within [min_val, max_val]."""
    return max(min_val, min(max_val, val))


# ---------------------------------------------------------------------------
# Component Scoring Functions
# ---------------------------------------------------------------------------

def calculate_schedule_risk(
    project: ProjectInput,
    indicators: ProjectIndicators
) -> CategoryRiskResult:
    """
    Schedule Risk Category:
      - 40% schedule-variance risk
      - 30% remaining-work pressure
      - 20% delayed-task risk
      - 10% deadline-proximity risk
    """
    s_ind = indicators.schedule
    s_in = project.schedule

    # 1. Schedule Variance Risk (40%)
    # If SV >= 0, ahead of schedule -> 0 risk.
    # If SV < 0, behind schedule -> 2x SV magnitude clamped to 100.
    # If project is overdue, baseline risk is set to 70 + days overdue scaling.
    if s_ind.is_overdue:
        sv_score = clamp(70.0 + s_ind.days_overdue * 2.0, 70.0, 100.0)
        sv_desc = f"Project overdue by {s_ind.days_overdue} days with unfinished tasks."
    elif s_ind.schedule_variance < 0:
        sv_score = clamp(abs(s_ind.schedule_variance) * 2.0, 0.0, 100.0)
        sv_desc = f"Behind schedule: variance {s_ind.schedule_variance}%, mapped at 2.0x."
    else:
        sv_score = 0.0
        sv_desc = f"On or ahead of schedule (variance {s_ind.schedule_variance}%)."

    # 2. Remaining-Work Pressure Risk (30%)
    # Ratio of remaining work % to remaining time %.
    if s_ind.remaining_work_pct <= 0:
        pressure_score = 0.0
        pressure_desc = "All tasks completed (0% work remaining)."
    elif s_ind.is_overdue or s_ind.remaining_time_pct <= 0:
        pressure_score = 100.0
        pressure_desc = f"Schedule exhausted but {s_ind.remaining_work_pct}% work remains."
    else:
        ratio = s_ind.work_to_time_ratio
        if ratio <= 1.0:
            pressure_score = clamp(ratio * 20.0, 0.0, 20.0)
            pressure_desc = f"Work pace required is sustainable (work/time ratio {ratio:.2f})."
        else:
            # ratio > 1.0 requires acceleration
            # ratio 1.0 -> 20, ratio 1.75 -> 60, ratio >= 2.5 -> 100
            pressure_score = clamp(20.0 + (ratio - 1.0) * 53.33, 20.0, 100.0)
            pressure_desc = f"Acceleration required: {s_ind.remaining_work_pct}% work vs {s_ind.remaining_time_pct}% time left (ratio {ratio:.2f})."

    # 3. Delayed-Task Risk (20%)
    # Ratio of delayed tasks to total tasks
    delayed_ratio = s_ind.delayed_task_ratio_pct
    delayed_score = clamp(delayed_ratio * 2.5, 0.0, 100.0)
    delayed_desc = f"{delayed_ratio:.1f}% of total tasks delayed ({s_in.delayed_tasks}/{s_in.total_tasks})."

    # 4. Deadline-Proximity Risk (10%)
    # Schedule flexibility diminishes as deadline approaches
    if s_ind.remaining_work_pct <= 0:
        deadline_score = 0.0
        deadline_desc = "Work completed; deadline proximity poses no delivery risk."
    elif s_ind.time_elapsed_pct <= 50.0:
        deadline_score = 10.0
        deadline_desc = f"Early project stage ({s_ind.time_elapsed_pct}% elapsed); high buffer."
    elif s_ind.time_elapsed_pct <= 85.0:
        deadline_score = clamp(10.0 + (s_ind.time_elapsed_pct - 50.0) * 1.4, 10.0, 60.0)
        deadline_desc = f"Mid-to-late stage ({s_ind.time_elapsed_pct}% elapsed); buffer narrowing."
    else:
        deadline_score = clamp(60.0 + (s_ind.time_elapsed_pct - 85.0) * 2.67, 60.0, 100.0)
        deadline_desc = f"Critical final phase ({s_ind.time_elapsed_pct}% elapsed); very limited schedule contingency."

    components = {
        "schedule_variance": ComponentScore(
            name="Schedule Variance",
            raw_value=f"{s_ind.schedule_variance}%",
            score=round(sv_score, 2),
            weight=0.40,
            formula_description=sv_desc
        ),
        "remaining_work_pressure": ComponentScore(
            name="Remaining Work Pressure",
            raw_value=f"{s_ind.work_to_time_ratio:.2f}x",
            score=round(pressure_score, 2),
            weight=0.30,
            formula_description=pressure_desc
        ),
        "delayed_tasks": ComponentScore(
            name="Delayed Tasks",
            raw_value=f"{s_in.delayed_tasks} tasks ({delayed_ratio:.1f}%)",
            score=round(delayed_score, 2),
            weight=0.20,
            formula_description=delayed_desc
        ),
        "deadline_proximity": ComponentScore(
            name="Deadline Proximity",
            raw_value=f"{s_ind.time_elapsed_pct:.1f}% elapsed",
            score=round(deadline_score, 2),
            weight=0.10,
            formula_description=deadline_desc
        )
    }

    category_score = (
        0.40 * sv_score +
        0.30 * pressure_score +
        0.20 * delayed_score +
        0.10 * deadline_score
    )
    category_score = round(clamp(category_score, 0.0, 100.0), 2)

    return CategoryRiskResult(
        category_name="Schedule Risk",
        score=category_score,
        level=classify_risk(category_score),
        weight_in_overall=0.35,  # Baseline; overridden in overall calculation
        components=components
    )


def calculate_resource_risk(
    project: ProjectInput,
    indicators: ProjectIndicators
) -> CategoryRiskResult:
    """
    Resource Risk Category:
      - 40% team-availability risk
      - 40% workload-imbalance risk
      - 20% resource-shortage risk
    """
    r_ind = indicators.resource
    r_in = project.resource

    # 1. Team-Availability Risk (40%)
    shortfall = r_ind.availability_shortfall_pct
    avail_score = clamp(shortfall * 2.0, 0.0, 100.0)
    avail_desc = f"Availability is {r_ind.team_availability_pct:.1f}% ({r_in.available_team_members}/{r_in.required_team_members}); shortfall {shortfall:.1f}%."

    # 2. Workload-Imbalance Risk (40%)
    # Captures delta between top overloaded individual and average, plus individual peak overload
    imbalance_score = clamp(
        r_ind.workload_imbalance_pct * 1.2 + r_ind.peak_overload_pct * 0.8,
        0.0,
        100.0
    )
    imbalance_desc = (
        f"Workload spread: highest is {r_in.highest_individual_workload_pct}% vs team avg {r_in.team_workload_pct}%. "
        f"Imbalance delta: {r_ind.workload_imbalance_pct}%, peak overload: {r_ind.peak_overload_pct}%."
    )

    # 3. Resource-Shortage Risk (20%)
    # Overall team overloading and headcount gap
    shortage_score = clamp(
        shortfall * 0.5 + r_ind.average_overload_pct * 1.5,
        0.0,
        100.0
    )
    shortage_desc = (
        f"Headcount gap: {r_ind.resource_shortage_headcount:.1f} members; "
        f"average team overload above 100%: {r_ind.average_overload_pct:.1f}%."
    )

    components = {
        "team_availability": ComponentScore(
            name="Team Availability",
            raw_value=f"{r_ind.team_availability_pct:.1f}%",
            score=round(avail_score, 2),
            weight=0.40,
            formula_description=avail_desc
        ),
        "workload_imbalance": ComponentScore(
            name="Workload Imbalance",
            raw_value=f"{r_ind.workload_imbalance_pct:.1f}% spread",
            score=round(imbalance_score, 2),
            weight=0.40,
            formula_description=imbalance_desc
        ),
        "resource_shortage": ComponentScore(
            name="Resource Shortage",
            raw_value=f"{r_ind.resource_shortage_headcount:.1f} deficit / {r_ind.average_overload_pct:.1f}% overload",
            score=round(shortage_score, 2),
            weight=0.20,
            formula_description=shortage_desc
        )
    }

    category_score = (
        0.40 * avail_score +
        0.40 * imbalance_score +
        0.20 * shortage_score
    )
    category_score = round(clamp(category_score, 0.0, 100.0), 2)

    return CategoryRiskResult(
        category_name="Resource Risk",
        score=category_score,
        level=classify_risk(category_score),
        weight_in_overall=0.20,
        components=components
    )


def calculate_quality_risk(
    project: ProjectInput,
    indicators: ProjectIndicators
) -> CategoryRiskResult:
    """
    Quality Risk Category:
      - 30% open-bug risk
      - 35% critical-bug risk
      - 35% bug-growth risk
    """
    q_ind = indicators.quality
    q_in = project.quality

    # 1. Open Bug Risk (30%)
    # 0 bugs -> 0, 10 bugs -> 50, 20+ bugs -> 100
    open_bug_score = clamp(q_in.open_bugs * 5.0, 0.0, 100.0)
    open_desc = f"{q_in.open_bugs} open defects logged (5 pts/bug up to 20 defects)."

    # 2. Critical Bug Risk (35%)
    # Combines critical bug ratio (severity concentration) and absolute count
    crit_ratio = q_ind.critical_bug_ratio_pct
    crit_score = clamp(crit_ratio * 0.6 + q_in.critical_bugs * 15.0, 0.0, 100.0)
    crit_desc = f"{q_in.critical_bugs} critical defects out of {q_in.open_bugs} open ({crit_ratio:.1f}% critical ratio)."

    # 3. Bug Growth Risk (35%)
    # Handles previous_period_bugs == 0 cleanly
    if q_ind.is_baseline_zero:
        if q_in.current_period_bugs == 0:
            growth_score = 0.0
            growth_desc = "No defects in previous period (0) and none in current period (0)."
        else:
            growth_score = clamp(q_in.current_period_bugs * 15.0, 15.0, 85.0)
            growth_desc = (
                f"Previous baseline was 0 defects; evaluated on new influx of "
                f"{q_in.current_period_bugs} defects in current period."
            )
    else:
        growth_pct = q_ind.bug_growth_pct if q_ind.bug_growth_pct is not None else 0.0
        if growth_pct <= 0:
            growth_score = 0.0
            growth_desc = f"Defects declining or stable ({growth_pct:.1f}% change from {q_in.previous_period_bugs} to {q_in.current_period_bugs})."
        else:
            growth_score = clamp(growth_pct * 1.0, 0.0, 100.0)
            growth_desc = f"Defect count grew by {growth_pct:.1f}% (from {q_in.previous_period_bugs} to {q_in.current_period_bugs})."

    components = {
        "open_bugs": ComponentScore(
            name="Open Defects Volume",
            raw_value=f"{q_in.open_bugs} bugs",
            score=round(open_bug_score, 2),
            weight=0.30,
            formula_description=open_desc
        ),
        "critical_bugs": ComponentScore(
            name="Critical Defect Severity",
            raw_value=f"{q_in.critical_bugs} critical ({crit_ratio:.1f}%)",
            score=round(crit_score, 2),
            weight=0.35,
            formula_description=crit_desc
        ),
        "bug_growth": ComponentScore(
            name="Defect Growth Trend",
            raw_value=(
                f"{q_ind.bug_growth_pct:.1f}%"
                if q_ind.bug_growth_pct is not None
                else f"+{q_in.current_period_bugs} new (0 baseline)"
            ),
            score=round(growth_score, 2),
            weight=0.35,
            formula_description=growth_desc
        )
    }

    category_score = (
        0.30 * open_bug_score +
        0.35 * crit_score +
        0.35 * growth_score
    )
    category_score = round(clamp(category_score, 0.0, 100.0), 2)

    return CategoryRiskResult(
        category_name="Quality Risk",
        score=category_score,
        level=classify_risk(category_score),
        weight_in_overall=0.20,
        components=components
    )


def calculate_requirement_risk(
    project: ProjectInput,
    indicators: ProjectIndicators
) -> CategoryRiskResult:
    """
    Requirement Risk Category:
      - 50% requirement-change-rate risk
      - 30% change-frequency risk
      - 20% major-change risk
    """
    rq_ind = indicators.requirement
    rq_in = project.requirement

    # 1. Requirement Change Rate Risk (50%)
    # Standard SEPM benchmark: >25% churn introduces high rework risk
    rate = rq_ind.requirement_change_rate_pct
    rate_score = clamp(rate * 2.5, 0.0, 100.0)
    rate_desc = f"{rate:.1f}% of total requirements modified ({rq_in.changed_requirements}/{rq_in.total_requirements})."

    # 2. Change Frequency Risk (30%)
    # Volume of changes introduced specifically in current reporting cycle
    freq = rq_ind.change_frequency_pct
    freq_score = clamp(freq * 3.5, 0.0, 100.0)
    freq_desc = f"{rq_in.current_period_changes} requirement changes in current period ({freq:.1f}% of total)."

    # 3. Major-Change Risk (20%)
    # Impact of high-severity architectural requirement shifts
    major_ratio = rq_ind.major_change_ratio_pct
    major_score = clamp(major_ratio * 0.6 + rq_in.major_changes * 15.0, 0.0, 100.0)
    major_desc = f"{rq_in.major_changes} major/architectural changes ({major_ratio:.1f}% of changed requirements)."

    components = {
        "change_rate": ComponentScore(
            name="Requirement Volatility (Change Rate)",
            raw_value=f"{rate:.1f}%",
            score=round(rate_score, 2),
            weight=0.50,
            formula_description=rate_desc
        ),
        "change_frequency": ComponentScore(
            name="Current Change Velocity",
            raw_value=f"{rq_in.current_period_changes} current ({freq:.1f}%)",
            score=round(freq_score, 2),
            weight=0.30,
            formula_description=freq_desc
        ),
        "major_changes": ComponentScore(
            name="Major / Architectural Scope Changes",
            raw_value=f"{rq_in.major_changes} major ({major_ratio:.1f}%)",
            score=round(major_score, 2),
            weight=0.20,
            formula_description=major_desc
        )
    }

    category_score = (
        0.50 * rate_score +
        0.30 * freq_score +
        0.20 * major_score
    )
    category_score = round(clamp(category_score, 0.0, 100.0), 2)

    return CategoryRiskResult(
        category_name="Requirement Risk",
        score=category_score,
        level=classify_risk(category_score),
        weight_in_overall=0.20,
        components=components
    )


def calculate_budget_risk(
    project: ProjectInput,
    indicators: ProjectIndicators
) -> CategoryRiskResult:
    """
    Optional Budget Risk Category:
      Compares spending progress with work completed.
      Budget usage alone is not risk; spending outpacing progress constitutes risk.
    """
    b_ind = indicators.budget
    b_in = project.budget
    if not b_ind or not b_in:
        return CategoryRiskResult(
            category_name="Budget Risk",
            score=0.0,
            level=RiskLevel.LOW,
            weight_in_overall=0.05,
            components={}
        )

    # Cost Variance Proxy: Work completed % - Spend %
    # If negative, spend is higher than work delivered
    cost_variance = b_ind.cost_variance_proxy
    if cost_variance >= 0:
        overspend_score = 0.0
        overspend_desc = f"Spending ({b_ind.budget_spent_pct:.1f}%) aligns with work completion ({b_in.work_completed_pct:.1f}%)."
    else:
        overspend_score = clamp(abs(cost_variance) * 2.5, 0.0, 100.0)
        overspend_desc = (
            f"Spend progress ({b_ind.budget_spent_pct:.1f}%) exceeds work progress "
            f"({b_in.work_completed_pct:.1f}%) by {abs(cost_variance):.1f}%."
        )

    burn_score = clamp((b_ind.burn_to_progress_ratio - 1.0) * 100.0, 0.0, 100.0) if b_ind.burn_to_progress_ratio > 1.0 else 0.0
    burn_desc = f"Burn-to-progress ratio is {b_ind.burn_to_progress_ratio:.2f}x."

    components = {
        "cost_variance": ComponentScore(
            name="Cost-to-Work Variance",
            raw_value=f"{cost_variance:.1f}%",
            score=round(overspend_score, 2),
            weight=0.70,
            formula_description=overspend_desc
        ),
        "burn_ratio": ComponentScore(
            name="Cost Burn Ratio",
            raw_value=f"{b_ind.burn_to_progress_ratio:.2f}x",
            score=round(burn_score, 2),
            weight=0.30,
            formula_description=burn_desc
        )
    }

    category_score = 0.70 * overspend_score + 0.30 * burn_score
    category_score = round(clamp(category_score, 0.0, 100.0), 2)

    return CategoryRiskResult(
        category_name="Budget Risk",
        score=category_score,
        level=classify_risk(category_score),
        weight_in_overall=0.05,
        components=components
    )


# ---------------------------------------------------------------------------
# Overall Risk Scoring Engine
# ---------------------------------------------------------------------------

def calculate_overall_risk(
    project: ProjectInput,
    indicators: Optional[ProjectIndicators] = None
) -> OverallRiskResult:
    """
    Computes overall risk score from category scores.
    Handles weight redistribution:
      - When Budget is disabled (default):
          Redistributes 5% weight proportionally across 4 categories:
          Schedule: 35 / 95 = 36.8421%
          Resource: 20 / 95 = 21.0526%
          Quality:  20 / 95 = 21.0526%
          Requirement: 20 / 95 = 21.0526%
          Sum = 100.0%
      - When Budget is enabled:
          Schedule: 35.0%
          Resource: 20.0%
          Quality:  20.0%
          Requirement: 20.0%
          Budget:    5.0%
          Sum = 100.0%
    """
    if indicators is None:
        indicators = calculate_all_indicators(project)

    sched_res = calculate_schedule_risk(project, indicators)
    res_res = calculate_resource_risk(project, indicators)
    qual_res = calculate_quality_risk(project, indicators)
    req_res = calculate_requirement_risk(project, indicators)

    category_results: Dict[str, CategoryRiskResult] = {
        "Schedule": sched_res,
        "Resource": res_res,
        "Quality": qual_res,
        "Requirement": req_res
    }

    weights: Dict[str, float] = {}
    if project.enable_budget and project.budget:
        budget_res = calculate_budget_risk(project, indicators)
        category_results["Budget"] = budget_res
        weights = {
            "Schedule": 0.35,
            "Resource": 0.20,
            "Quality": 0.20,
            "Requirement": 0.20,
            "Budget": 0.05
        }
    else:
        # Proportionally redistribute the 5% budget weight across 4 categories
        weights = {
            "Schedule": 35.0 / 95.0,     # ~0.368421
            "Resource": 20.0 / 95.0,     # ~0.210526
            "Quality": 20.0 / 95.0,      # ~0.210526
            "Requirement": 20.0 / 95.0   # ~0.210526
        }

    # Update assigned weights in category result objects
    for cat_name, w in weights.items():
        if cat_name in category_results:
            category_results[cat_name].weight_in_overall = round(w, 4)

    # Compute overall score
    overall_score = sum(
        category_results[cat].score * w
        for cat, w in weights.items()
    )
    overall_score = round(clamp(overall_score, 0.0, 100.0), 2)
    overall_level = classify_risk(overall_score)

    return OverallRiskResult(
        project_name=project.project_name or "Untitled Project",
        overall_score=overall_score,
        overall_level=overall_level,
        is_budget_enabled=bool(project.enable_budget and project.budget),
        category_results=category_results,
        category_weights={k: round(v * 100.0, 2) for k, v in weights.items()},
        indicators=indicators
    )
