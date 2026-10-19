"""
recommendations.py
===================
Explainability and actionable mitigation recommendation engine for Periculum.
Synthesizes indicator metrics into natural-language factors and mitigation strategies.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from calculations import ProjectInput, ProjectIndicators
from risk_engine import OverallRiskResult, CategoryRiskResult, RiskLevel


@dataclass
class CategoryAssessment:
    category_name: str
    score: float
    level: RiskLevel
    contributing_factors: List[str]
    mitigations: List[str]


@dataclass
class ProjectAssessment:
    project_name: str
    overall_score: float
    overall_level: RiskLevel
    key_takeaways: List[str]
    categories: Dict[str, CategoryAssessment]


def generate_schedule_assessment(
    cat_result: CategoryRiskResult,
    project: ProjectInput,
    indicators: ProjectIndicators
) -> CategoryAssessment:
    """Generates explainable factors and targeted mitigations for Schedule Risk."""
    s_ind = indicators.schedule
    s_in = project.schedule
    factors: List[str] = []
    mitigations: List[str] = []

    # 1. Contributing Factors
    if s_ind.is_overdue:
        factors.append(
            f"Overdue Status: Project has exceeded planned timeline by {s_ind.days_overdue} days "
            f"({s_in.days_elapsed} days elapsed out of {s_in.total_duration_days} planned) "
            f"with {s_ind.remaining_work_pct:.1f}% of tasks still incomplete."
        )
    elif s_ind.schedule_variance < -5.0:
        factors.append(
            f"Negative Schedule Variance: Task progress ({s_ind.task_progress_pct:.1f}%) is trailing "
            f"elapsed project duration ({s_ind.time_elapsed_pct:.1f}%), resulting in a schedule variance of {s_ind.schedule_variance:.1f}%."
        )

    if s_in.delayed_tasks > 0:
        factors.append(
            f"Delayed Tasks: {s_in.delayed_tasks} out of {s_in.total_tasks} total tasks "
            f"({s_ind.delayed_task_ratio_pct:.1f}%) are flagged as behind schedule."
        )

    if not s_ind.is_overdue and s_ind.work_to_time_ratio > 1.2:
        factors.append(
            f"Pace Pressure: Remaining work ({s_ind.remaining_work_pct:.1f}%) significantly exceeds "
            f"remaining timeline ({s_ind.remaining_time_pct:.1f}%), requiring a {s_ind.work_to_time_ratio:.2f}x pace acceleration."
        )

    if s_ind.time_elapsed_pct >= 85.0 and s_ind.remaining_work_pct > 10.0:
        factors.append(
            f"Late-Stage Compression: Project has consumed {s_ind.time_elapsed_pct:.1f}% of its schedule, "
            f"leaving minimal contingency buffer for remaining deliverables."
        )

    if not factors:
        factors.append(
            f"Healthy Schedule: Task completion ({s_ind.task_progress_pct:.1f}%) is aligned with "
            f"elapsed time ({s_ind.time_elapsed_pct:.1f}%), with 0 delayed tasks."
        )

    # 2. Actionable Mitigations
    if s_ind.is_overdue:
        mitigations.append(
            "Convene an urgent stakeholder alignment to formalize an agreed schedule re-baseline "
            "and triage remaining scope into Must-Have vs Nice-to-Have."
        )
    if s_in.delayed_tasks > 0:
        mitigations.append(
            f"Conduct daily blocker-removal standups focused exclusively on the {s_in.delayed_tasks} delayed tasks "
            "and reassign unblocked items to available engineers."
        )
    if s_ind.schedule_variance < -15.0 or s_ind.work_to_time_ratio > 1.3:
        mitigations.append(
            "Implement schedule compression: explore fast-tracking (parallelizing non-dependent user stories) "
            "or de-scoping lower-priority backlog items to safeguard release targets."
        )
    if s_ind.time_elapsed_pct >= 80.0 and s_ind.remaining_work_pct > 15.0:
        mitigations.append(
            "Enact an immediate feature freeze; restrict development solely to critical-path completion and stabilization."
        )

    if not mitigations:
        mitigations.append(
            "Maintain current sprint cadence and continue monitoring weekly task velocity to protect schedule contingency."
        )

    return CategoryAssessment(
        category_name=cat_result.category_name,
        score=cat_result.score,
        level=cat_result.level,
        contributing_factors=factors,
        mitigations=mitigations
    )


def generate_resource_assessment(
    cat_result: CategoryRiskResult,
    project: ProjectInput,
    indicators: ProjectIndicators
) -> CategoryAssessment:
    """Generates explainable factors and targeted mitigations for Resource Risk."""
    r_ind = indicators.resource
    r_in = project.resource
    factors: List[str] = []
    mitigations: List[str] = []

    # 1. Contributing Factors
    if r_ind.team_availability_pct < 90.0:
        factors.append(
            f"Staffing Deficit: Available capacity ({r_in.available_team_members} members) is below "
            f"required staffing ({r_in.required_team_members} members), creating an availability shortfall of {r_ind.availability_shortfall_pct:.1f}%."
        )

    if r_ind.workload_imbalance_pct > 15.0:
        factors.append(
            f"Workload Imbalance: Substantial spread between highest individual workload ({r_in.highest_individual_workload_pct:.1f}%) "
            f"and team average ({r_in.team_workload_pct:.1f}%), highlighting bottleneck and single-point dependency risks."
        )

    if r_ind.peak_overload_pct > 10.0:
        factors.append(
            f"Key-Person Overload: The most heavily loaded team member is operating at {r_in.highest_individual_workload_pct:.1f}% "
            f"capacity, exceeding sustainable full-time allocation (100%)."
        )

    if r_ind.average_overload_pct > 5.0:
        factors.append(
            f"Team-Wide Over-allocation: Team average workload is {r_in.team_workload_pct:.1f}%, indicating systemic over-commitment."
        )

    if not factors:
        factors.append(
            f"Balanced Resourcing: Team is fully staffed ({r_ind.team_availability_pct:.1f}% availability) "
            f"with balanced workload distribution (spread of {r_ind.workload_imbalance_pct:.1f}%)."
        )

    # 2. Actionable Mitigations
    if r_ind.team_availability_pct < 85.0:
        mitigations.append(
            f"Escalate staffing deficit ({r_ind.resource_shortage_headcount:.1f} headcount) to resource management "
            "to request supplemental cross-functional support or contract assistance."
        )
    if r_ind.workload_imbalance_pct > 15.0 or r_ind.peak_overload_pct > 15.0:
        mitigations.append(
            f"Rebalance workload: reassign non-critical tickets from overloaded lead(s) (currently {r_in.highest_individual_workload_pct:.1f}%) "
            "to team members with available bandwidth."
        )
    if r_ind.average_overload_pct > 10.0:
        mitigations.append(
            "Renegotiate current milestone commitments or adjust story point velocity to bring average workload down to sustainable levels."
        )

    if not mitigations:
        mitigations.append(
            "Preserve cross-skilling and peer reviews to avoid developing siloed knowledge in critical subsystems."
        )

    return CategoryAssessment(
        category_name=cat_result.category_name,
        score=cat_result.score,
        level=cat_result.level,
        contributing_factors=factors,
        mitigations=mitigations
    )


def generate_quality_assessment(
    cat_result: CategoryRiskResult,
    project: ProjectInput,
    indicators: ProjectIndicators
) -> CategoryAssessment:
    """Generates explainable factors and targeted mitigations for Quality Risk."""
    q_ind = indicators.quality
    q_in = project.quality
    factors: List[str] = []
    mitigations: List[str] = []

    # 1. Contributing Factors
    if q_in.critical_bugs > 0:
        factors.append(
            f"Critical Defects Present: {q_in.critical_bugs} critical defect(s) logged "
            f"({q_ind.critical_bug_ratio_pct:.1f}% of {q_in.open_bugs} open bugs), representing immediate delivery and reliability threats."
        )

    if q_in.open_bugs >= 8:
        factors.append(
            f"High Defect Volume: {q_in.open_bugs} open defects currently active in the backlog."
        )

    if q_ind.is_baseline_zero:
        if q_in.current_period_bugs > 0:
            factors.append(
                f"Defect Influx from Zero Baseline: {q_in.current_period_bugs} new defects recorded this period "
                "where previously 0 defects were tracked."
            )
    else:
        if q_ind.bug_growth_pct is not None and q_ind.bug_growth_pct > 10.0:
            factors.append(
                f"Accelerating Defect Trend: Open bugs grew by {q_ind.bug_growth_pct:.1f}% "
                f"(from {q_in.previous_period_bugs} to {q_in.current_period_bugs} bugs) in the current reporting cycle."
            )

    if not factors:
        factors.append(
            f"Stable Quality Profile: Defect backlog is low ({q_in.open_bugs} open, 0 critical), "
            "indicating robust code quality and low defect injection rates."
        )

    # 2. Actionable Mitigations
    if q_in.critical_bugs > 0:
        mitigations.append(
            f"Halt non-critical feature work and mandate an immediate swarm on the {q_in.critical_bugs} critical defect(s)."
        )
    if (q_ind.bug_growth_pct is not None and q_ind.bug_growth_pct > 20.0) or (q_ind.is_baseline_zero and q_in.current_period_bugs >= 3):
        mitigations.append(
            "Conduct root-cause analysis on recent commits; tighten definition-of-done and require automated unit/integration tests before merge."
        )
    if q_in.open_bugs >= 10:
        mitigations.append(
            "Dedicate a 1-week bug-bash / technical debt stabilization sprint to reduce the defect inventory."
        )

    if not mitigations:
        mitigations.append(
            "Maintain automated test coverage and regular static analysis scans during pull request reviews."
        )

    return CategoryAssessment(
        category_name=cat_result.category_name,
        score=cat_result.score,
        level=cat_result.level,
        contributing_factors=factors,
        mitigations=mitigations
    )


def generate_requirement_assessment(
    cat_result: CategoryRiskResult,
    project: ProjectInput,
    indicators: ProjectIndicators
) -> CategoryAssessment:
    """Generates explainable factors and targeted mitigations for Requirement Risk."""
    rq_ind = indicators.requirement
    rq_in = project.requirement
    factors: List[str] = []
    mitigations: List[str] = []

    # 1. Contributing Factors
    if rq_ind.requirement_change_rate_pct > 15.0:
        factors.append(
            f"Scope Churn: {rq_ind.requirement_change_rate_pct:.1f}% of total requirements have been altered "
            f"({rq_in.changed_requirements} out of {rq_in.total_requirements}), indicating scope instability."
        )

    if rq_in.current_period_changes > 0:
        factors.append(
            f"Recent Volatility: {rq_in.current_period_changes} requirement changes introduced in the current period alone "
            f"({rq_ind.change_frequency_pct:.1f}% of total scope)."
        )

    if rq_in.major_changes > 0:
        factors.append(
            f"Major Architectural Changes: {rq_in.major_changes} major/structural modifications reported "
            f"({rq_ind.major_change_ratio_pct:.1f}% of all modified requirements)."
        )

    if not factors:
        factors.append(
            f"Stable Requirement Scope: Requirement change rate is low ({rq_ind.requirement_change_rate_pct:.1f}%) "
            "with zero major structural changes."
        )

    # 2. Actionable Mitigations
    if rq_ind.requirement_change_rate_pct > 20.0:
        mitigations.append(
            "Institute a formal Change Control Board (CCB) process: freeze incoming scope changes "
            "unless accompanied by approved budget or schedule extensions."
        )
    if rq_in.major_changes > 0:
        mitigations.append(
            f"Conduct rigorous architectural impact analysis for the {rq_in.major_changes} major changes "
            "to assess database, API, and regression implications before implementation."
        )
    if rq_ind.change_frequency_pct > 15.0:
        mitigations.append(
            "Enact a temporary requirement freeze for the upcoming milestone release to allow developers to hit a stable target."
        )

    if not mitigations:
        mitigations.append(
            "Continue tracking requirement clarification items in user-story acceptance criteria without altering core scope."
        )

    return CategoryAssessment(
        category_name=cat_result.category_name,
        score=cat_result.score,
        level=cat_result.level,
        contributing_factors=factors,
        mitigations=mitigations
    )


def generate_budget_assessment(
    cat_result: CategoryRiskResult,
    project: ProjectInput,
    indicators: ProjectIndicators
) -> CategoryAssessment:
    """Generates explainable factors and targeted mitigations for optional Budget Risk."""
    b_ind = indicators.budget
    b_in = project.budget
    factors: List[str] = []
    mitigations: List[str] = []

    if b_ind and b_in:
        if b_ind.cost_variance_proxy < -5.0:
            factors.append(
                f"Expenditure Outpacing Work: Budget spent is {b_ind.budget_spent_pct:.1f}% (${b_in.amount_spent:,.0f} / ${b_in.total_budget:,.0f}), "
                f"while completed work is only {b_in.work_completed_pct:.1f}%, yielding a -{abs(b_ind.cost_variance_proxy):.1f}% cost variance."
            )
        if b_ind.burn_to_progress_ratio > 1.2:
            factors.append(
                f"Elevated Burn Rate: Project cost burn ratio is {b_ind.burn_to_progress_ratio:.2f}x relative to earned progress."
            )

        if not factors:
            factors.append(
                f"Healthy Cost Performance: Spending ({b_ind.budget_spent_pct:.1f}%) is in line with "
                f"completed work progress ({b_in.work_completed_pct:.1f}%)."
            )

        if b_ind.cost_variance_proxy < -10.0:
            mitigations.append(
                "Perform an Earned Value Management (EVM) audit; audit contractor billing and freeze non-essential project procurement."
            )
        else:
            mitigations.append(
                "Continue tracking milestone burn rates against planned deliverables."
            )

    return CategoryAssessment(
        category_name="Budget Risk",
        score=cat_result.score,
        level=cat_result.level,
        contributing_factors=factors or ["Budget evaluation enabled with standard spending metrics."],
        mitigations=mitigations or ["Review budget monthly against deliverable progress."]
    )


def generate_assessment(
    overall_result: OverallRiskResult,
    project: ProjectInput
) -> ProjectAssessment:
    """
    Synthesizes complete explainable assessments across all active risk categories.
    """
    indicators = overall_result.indicators
    categories: Dict[str, CategoryAssessment] = {}

    categories["Schedule"] = generate_schedule_assessment(
        overall_result.category_results["Schedule"],
        project,
        indicators
    )
    categories["Resource"] = generate_resource_assessment(
        overall_result.category_results["Resource"],
        project,
        indicators
    )
    categories["Quality"] = generate_quality_assessment(
        overall_result.category_results["Quality"],
        project,
        indicators
    )
    categories["Requirement"] = generate_requirement_assessment(
        overall_result.category_results["Requirement"],
        project,
        indicators
    )

    if overall_result.is_budget_enabled and "Budget" in overall_result.category_results:
        categories["Budget"] = generate_budget_assessment(
            overall_result.category_results["Budget"],
            project,
            indicators
        )

    # Key Takeaways
    key_takeaways: List[str] = []
    # Identify top 2 highest scoring categories
    sorted_cats = sorted(
        overall_result.category_results.items(),
        key=lambda item: item[1].score,
        reverse=True
    )
    top_cat = sorted_cats[0]
    key_takeaways.append(
        f"Primary risk driver is **{top_cat[0]} Risk** ({top_cat[1].score}/100, {top_cat[1].level.value})."
    )

    if len(sorted_cats) > 1 and sorted_cats[1][1].score >= 40.0:
        key_takeaways.append(
            f"Secondary risk driver is **{sorted_cats[1][0]} Risk** ({sorted_cats[1][1].score}/100, {sorted_cats[1][1].level.value})."
        )

    if overall_result.overall_level == RiskLevel.HIGH:
        key_takeaways.append(
            "Overall Project Status is **HIGH RISK**. Immediate executive intervention and mitigation measures are required."
        )
    elif overall_result.overall_level == RiskLevel.MEDIUM:
        key_takeaways.append(
            "Overall Project Status is **MEDIUM RISK**. Targeted corrective actions recommended to prevent risk escalation."
        )
    else:
        key_takeaways.append(
            "Overall Project Status is **LOW RISK**. Project is operating within expected tolerance parameters."
        )

    return ProjectAssessment(
        project_name=overall_result.project_name,
        overall_score=overall_result.overall_score,
        overall_level=overall_result.overall_level,
        key_takeaways=key_takeaways,
        categories=categories
    )
