"""
app.py
======
Interactive Streamlit Dashboard for Periculum: Software Project Risk Assessment.

Features:
- Structured metric inputs for Schedule, Resource, Quality, Requirement, and optional Budget.
- Preset loader for realistic project scenarios.
- Strict input validation with visual alerts.
- Real-time risk scoring and classification (Low / Medium / High).
- Interactive Plotly visualizations for Category Risk Comparison and Radar Profile.
- Explainability dashboard detailing driving risk factors and targeted mitigations.
- Export assessment report as JSON.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional

import streamlit as st
import plotly.graph_objects as go

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
from risk_engine import (
    calculate_overall_risk,
    RiskLevel,
    OverallRiskResult,
)
from recommendations import generate_assessment, ProjectAssessment


st.set_page_config(
    page_title="Project Risk Predictor | SEPM",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for polished SEPM dashboard aesthetics
st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 16px;
        border-left: 5px solid #0d6efd;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        margin-bottom: 12px;
    }
    .risk-badge-low {
        background-color: #d1e7dd;
        color: #0f5132;
        padding: 6px 14px;
        border-radius: 16px;
        font-weight: 700;
        display: inline-block;
    }
    .risk-badge-med {
        background-color: #fff3cd;
        color: #664d03;
        padding: 6px 14px;
        border-radius: 16px;
        font-weight: 700;
        display: inline-block;
    }
    .risk-badge-high {
        background-color: #f8d7da;
        color: #842029;
        padding: 6px 14px;
        border-radius: 16px;
        font-weight: 700;
        display: inline-block;
    }
    .disclaimer-box {
        background-color: #e9ecef;
        border-left: 4px solid #6c757d;
        padding: 10px 14px;
        border-radius: 4px;
        font-size: 0.88rem;
        color: #495057;
        margin-top: 25px;
    }
</style>
""", unsafe_allow_html=True)


SAMPLE_DATA_DIR = Path(__file__).parent / "sample_data"

PRESETS = {
    "Healthy Baseline (Phoenix ERP)": "example_project.json",
    "Severely Delayed (Titan Banking)": "delayed_project.json",
    "Quality Crisis (MediCare Platform)": "quality_crisis_project.json",
    "Understaffed Team (Atlas Migration)": "understaffed_project.json",
    "Custom Project": None
}


def load_preset_data(preset_name: str) -> Optional[Dict[str, Any]]:
    filename = PRESETS.get(preset_name)
    if not filename:
        return None
    file_path = SAMPLE_DATA_DIR / filename
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


# ---------------------------------------------------------------------------
# Sidebar: Presets & Configuration
# ---------------------------------------------------------------------------
st.sidebar.title("🛡️ Periculum")
st.sidebar.caption("Software Project Risk Assessment Engine")

selected_preset = st.sidebar.selectbox(
    "📂 Load Project Preset",
    options=list(PRESETS.keys()),
    index=0,
    help="Select a scenario to demonstrate different project risk profiles."
)

preset_data = load_preset_data(selected_preset) if selected_preset != "Custom Project" else None

enable_budget_toggle = st.sidebar.checkbox(
    "💰 Enable Optional Budget Risk (5%)",
    value=preset_data.get("enable_budget", False) if preset_data else False,
    help="When enabled, budget risk contributes 5% weight. When disabled, the 5% is redistributed proportionally among core categories."
)

st.sidebar.markdown("---")
st.sidebar.markdown("""
**Quick Evaluation Guide**
1. Review or modify project metrics in the form.
2. Click **Calculate Risk Assessment**.
3. Inspect Overall Risk, Category Bars, Evidence Factors, and Mitigations.
""")

st.sidebar.info(
    "💡 **Model Notice:** This is an explainable rule-based system using deterministic software engineering heuristics. "
    "It provides decision support without black-box statistical assumptions."
)


# ---------------------------------------------------------------------------
# Header & Context
# ---------------------------------------------------------------------------
st.title("📊 Periculum — Software Project Risk Assessment")
st.write(
    "A transparent, explainable decision-support tool for engineering leaders and delivery managers. "
    "Evaluates project health across **Schedule**, **Resources**, **Quality**, and **Requirements**."
)

# ---------------------------------------------------------------------------
# Metric Input Form
# ---------------------------------------------------------------------------
with st.expander("📝 Project Metrics Input Form", expanded=True):
    # Determine default values from preset or fallback defaults
    p_name_default = preset_data.get("project_name", "Enterprise Cloud Portal") if preset_data else "Enterprise Cloud Portal"
    project_name = st.text_input("Project Name / Identifier", value=p_name_default)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📅 Schedule Metrics")
        s_data = preset_data.get("schedule", {}) if preset_data else {}
        total_duration = st.number_input(
            "Total Planned Duration (days)",
            min_value=1.0,
            value=float(s_data.get("total_duration_days", 120.0)),
            step=5.0,
            help="Total timeline agreed in project schedule baseline."
        )
        days_elapsed = st.number_input(
            "Days Elapsed (days)",
            min_value=0.0,
            value=float(s_data.get("days_elapsed", 60.0)),
            step=5.0,
            help="Calendar days elapsed since project kickoff. Can exceed planned duration for overdue projects."
        )
        total_tasks = st.number_input(
            "Total Tasks / Work Packages",
            min_value=0,
            value=int(s_data.get("total_tasks", 100)),
            step=5,
            help="Total distinct tasks or work packages planned in the WBS."
        )
        completed_tasks = st.number_input(
            "Completed Tasks",
            min_value=0,
            value=int(s_data.get("completed_tasks", 55)),
            step=5,
            help="Tasks fully closed and accepted."
        )
        delayed_tasks = st.number_input(
            "Delayed Tasks",
            min_value=0,
            value=int(s_data.get("delayed_tasks", 4)),
            step=1,
            help="Tasks currently slipping past their target baseline date."
        )

    with col2:
        st.subheader("👥 Resource & Team Metrics")
        r_data = preset_data.get("resource", {}) if preset_data else {}
        req_members = st.number_input(
            "Required Team Members (FTE)",
            min_value=0.5,
            value=float(r_data.get("required_team_members", 8.0)),
            step=0.5,
            help="Required full-time equivalent staffing for planned velocity."
        )
        avail_members = st.number_input(
            "Available Team Members (FTE)",
            min_value=0.0,
            value=float(r_data.get("available_team_members", 8.0)),
            step=0.5,
            help="Active staffing currently assigned and present."
        )
        team_workload = st.number_input(
            "Average Team Workload (%)",
            min_value=0.0,
            value=float(r_data.get("team_workload_pct", 95.0)),
            step=5.0,
            help="Average workload allocation across the team (100% = full sustainable capacity)."
        )
        highest_workload = st.number_input(
            "Highest Individual Workload (%)",
            min_value=0.0,
            value=float(r_data.get("highest_individual_workload_pct", 110.0)),
            step=5.0,
            help="Peak workload on the single most heavily allocated team member."
        )

    col3, col4 = st.columns(2)

    with col3:
        st.subheader("🐞 Quality & Defect Metrics")
        q_data = preset_data.get("quality", {}) if preset_data else {}
        open_bugs = st.number_input(
            "Total Open Defects",
            min_value=0,
            value=int(q_data.get("open_bugs", 6)),
            step=1,
            help="Total outstanding defects across all severity tiers."
        )
        critical_bugs = st.number_input(
            "Critical / Blocker Defects",
            min_value=0,
            value=int(q_data.get("critical_bugs", 1)),
            step=1,
            help="Severity-1 defects that halt core operations or block deployment."
        )
        prev_bugs = st.number_input(
            "Defects in Previous Period",
            min_value=0,
            value=int(q_data.get("previous_period_bugs", 5)),
            step=1,
            help="Defect count from preceding sprint/period (handles 0 cleanly)."
        )
        curr_bugs = st.number_input(
            "Defects in Current Period",
            min_value=0,
            value=int(q_data.get("current_period_bugs", 6)),
            step=1,
            help="Defect count discovered in the current sprint/reporting period."
        )

    with col4:
        st.subheader("📋 Requirement Stability Metrics")
        rq_data = preset_data.get("requirement", {}) if preset_data else {}
        total_reqs = st.number_input(
            "Total Requirements",
            min_value=0,
            value=int(rq_data.get("total_requirements", 45)),
            step=5,
            help="Baseline requirement count."
        )
        changed_reqs = st.number_input(
            "Changed Requirements (Total)",
            min_value=0,
            value=int(rq_data.get("changed_requirements", 5)),
            step=1,
            help="Cumulative requirements modified or added since kickoff."
        )
        curr_changes = st.number_input(
            "Changes in Current Period",
            min_value=0,
            value=int(rq_data.get("current_period_changes", 1)),
            step=1,
            help="Requirements modified in current reporting sprint."
        )
        major_changes = st.number_input(
            "Major / Architectural Changes",
            min_value=0,
            value=int(rq_data.get("major_changes", 0)),
            step=1,
            help="High-impact scope alterations requiring structural or database refactoring."
        )

    budget_obj: Optional[BudgetMetrics] = None
    if enable_budget_toggle:
        st.subheader("💰 Optional Budget Metrics")
        b_col1, b_col2, b_col3 = st.columns(3)
        b_data = preset_data.get("budget", {}) if preset_data else {}
        with b_col1:
            tot_b = st.number_input(
                "Total Budget ($)",
                min_value=1000.0,
                value=float(b_data.get("total_budget", 200000.0)),
                step=10000.0
            )
        with b_col2:
            spent_b = st.number_input(
                "Amount Spent ($)",
                min_value=0.0,
                value=float(b_data.get("amount_spent", 110000.0)),
                step=5000.0
            )
        with b_col3:
            comp_b = st.number_input(
                "Work Completed (%)",
                min_value=0.0,
                max_value=100.0,
                value=float(b_data.get("work_completed_pct", 55.0)),
                step=5.0
            )
        budget_obj = BudgetMetrics(
            total_budget=tot_b,
            amount_spent=spent_b,
            work_completed_pct=comp_b
        )

    submitted = st.button("🚀 Calculate Risk Assessment", type="primary", use_container_width=True)


# ---------------------------------------------------------------------------
# Construct Data Models & Run Assessment (Gated on Submission)
# ---------------------------------------------------------------------------
current_inputs_signature = (
    project_name,
    total_duration,
    days_elapsed,
    total_tasks,
    completed_tasks,
    delayed_tasks,
    req_members,
    avail_members,
    team_workload,
    highest_workload,
    open_bugs,
    critical_bugs,
    prev_bugs,
    curr_bugs,
    total_reqs,
    changed_reqs,
    curr_changes,
    major_changes,
    enable_budget_toggle,
    (tot_b, spent_b, comp_b) if enable_budget_toggle and budget_obj else None
)

# Invalidate stored assessment if any input metric has changed
if "assessment_data" in st.session_state and st.session_state["assessment_data"]:
    if st.session_state["assessment_data"].get("signature") != current_inputs_signature:
        st.session_state["assessment_data"] = None

# Require submission before calculating or displaying assessment
if not submitted and st.session_state.get("assessment_data") is None:
    st.info("👆 Review or adjust project metrics above and click **Calculate Risk Assessment** to run the evaluation.")
    st.stop()

if submitted:
    project_input = ProjectInput(
        project_name=project_name,
        schedule=ScheduleMetrics(
            total_duration_days=total_duration,
            days_elapsed=days_elapsed,
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            delayed_tasks=delayed_tasks
        ),
        resource=ResourceMetrics(
            required_team_members=req_members,
            available_team_members=avail_members,
            team_workload_pct=team_workload,
            highest_individual_workload_pct=highest_workload
        ),
        quality=QualityMetrics(
            open_bugs=open_bugs,
            critical_bugs=critical_bugs,
            previous_period_bugs=prev_bugs,
            current_period_bugs=curr_bugs
        ),
        requirement=RequirementMetrics(
            total_requirements=total_reqs,
            changed_requirements=changed_reqs,
            current_period_changes=curr_changes,
            major_changes=major_changes
        ),
        enable_budget=enable_budget_toggle,
        budget=budget_obj
    )

    # Validation Check
    val_result = validate_project_input(project_input)

    if not val_result.is_valid:
        st.session_state["assessment_data"] = None
        st.error("❌ **Validation Failed:** Please resolve the following input errors:")
        for err in val_result.errors:
            st.markdown(f"- ⚠️ {err}")
        st.stop()

    # Run Backend Scoring
    indicators = calculate_all_indicators(project_input)
    overall_result: OverallRiskResult = calculate_overall_risk(project_input, indicators)
    assessment: ProjectAssessment = generate_assessment(overall_result, project_input)
    warnings = val_result.warnings

    st.session_state["assessment_data"] = {
        "signature": current_inputs_signature,
        "overall_result": overall_result,
        "assessment": assessment,
        "indicators": indicators,
        "project_input": project_input,
        "warnings": warnings
    }
else:
    cached = st.session_state["assessment_data"]
    overall_result = cached["overall_result"]
    assessment = cached["assessment"]
    indicators = cached["indicators"]
    project_input = cached["project_input"]
    warnings = cached["warnings"]

if warnings:
    with st.expander("⚠️ Input Warnings & Non-Fatal Notices", expanded=False):
        for warn in warnings:
            st.warning(warn)


# ---------------------------------------------------------------------------
# Executive Dashboard Display
# ---------------------------------------------------------------------------
st.markdown("---")
st.subheader("🎯 Executive Risk Summary")

# Overall Status Banner
score = overall_result.overall_score
level = overall_result.overall_level

badge_class = {
    RiskLevel.LOW: "risk-badge-low",
    RiskLevel.MEDIUM: "risk-badge-med",
    RiskLevel.HIGH: "risk-badge-high"
}.get(level, "risk-badge-low")

col_ov1, col_ov2, col_ov3 = st.columns([1.5, 2, 2.5])

with col_ov1:
    st.markdown(f"""
    <div style="text-align: center; padding: 20px; background: #ffffff; border: 1px solid #dee2e6; border-radius: 10px;">
        <h4 style="margin: 0; color: #6c757d;">Overall Risk Score</h4>
        <h1 style="font-size: 3.5rem; margin: 10px 0; color: {'#198754' if level == RiskLevel.LOW else '#fd7e14' if level == RiskLevel.MEDIUM else '#dc3545'};">
            {score:.1f} <span style="font-size: 1.5rem; color: #adb5bd;">/ 100</span>
        </h1>
        <span class="{badge_class}">{level.value} RISK</span>
    </div>
    """, unsafe_allow_html=True)

with col_ov2:
    st.markdown("##### 📌 Key Assessment Takeaways")
    for takeaway in assessment.key_takeaways:
        st.markdown(f"- {takeaway}")

with col_ov3:
    st.markdown("##### ⚖️ Active Weight Distribution")
    weight_text = " | ".join([f"**{cat}**: {w:.1f}%" for cat, w in overall_result.category_weights.items()])
    st.caption(weight_text)
    if not overall_result.is_budget_enabled:
        st.caption("ℹ️ Budget risk disabled: 5% weight redistributed proportionally across core 4 categories.")
    else:
        st.caption("ℹ️ Budget risk active: 5% weight included.")


# Metric KPI Row
st.markdown("#### 📈 Key Operational Indicators")
kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)

sched_ind = indicators.schedule
res_ind = indicators.resource
qual_ind = indicators.quality
req_ind = indicators.requirement

kpi1.metric(
    "Task Progress",
    f"{sched_ind.task_progress_pct:.1f}%",
    delta=f"{sched_ind.schedule_variance:+.1f}% vs time",
    delta_color="normal"
)
kpi2.metric(
    "Time Elapsed",
    f"{sched_ind.time_elapsed_pct:.1f}%",
    delta="Overdue" if sched_ind.is_overdue else f"{sched_ind.remaining_time_pct:.1f}% left",
    delta_color="inverse" if sched_ind.is_overdue else "off"
)
kpi3.metric(
    "Delayed Tasks",
    f"{project_input.schedule.delayed_tasks}",
    delta=f"{sched_ind.delayed_task_ratio_pct:.1f}% of WBS",
    delta_color="inverse" if project_input.schedule.delayed_tasks > 0 else "off"
)
kpi4.metric(
    "Team Staffing",
    f"{res_ind.team_availability_pct:.0f}%",
    delta=f"-{res_ind.availability_shortfall_pct:.0f}% shortfall" if res_ind.availability_shortfall_pct > 0 else "Full",
    delta_color="inverse" if res_ind.availability_shortfall_pct > 0 else "normal"
)
kpi5.metric(
    "Open / Critical Bugs",
    f"{project_input.quality.open_bugs} / {project_input.quality.critical_bugs}",
    delta=f"{qual_ind.critical_bug_ratio_pct:.1f}% critical",
    delta_color="inverse" if project_input.quality.critical_bugs > 0 else "off"
)
kpi6.metric(
    "Requirement Churn",
    f"{req_ind.requirement_change_rate_pct:.1f}%",
    delta=f"{project_input.requirement.changed_requirements}/{project_input.requirement.total_requirements}",
    delta_color="inverse" if req_ind.requirement_change_rate_pct > 20.0 else "off"
)


# ---------------------------------------------------------------------------
# Visualizations
# ---------------------------------------------------------------------------
st.markdown("---")
st.subheader("📊 Category Risk Analysis & Benchmarks")

v_col1, v_col2 = st.columns([1.5, 1])

categories = list(overall_result.category_results.keys())
cat_scores = [overall_result.category_results[c].score for c in categories]
colors = [
    "#198754" if s < 40 else "#fd7e14" if s < 70 else "#dc3545"
    for s in cat_scores
]

with v_col1:
    fig_bar = go.Figure(data=[
        go.Bar(
            x=categories,
            y=cat_scores,
            text=[f"{s:.1f}" for s in cat_scores],
            textposition="auto",
            marker_color=colors,
            hoverinfo="x+y"
        )
    ])
    fig_bar.add_hline(y=40, line_dash="dash", line_color="#fd7e14", annotation_text="Medium Threshold (40)")
    fig_bar.add_hline(y=70, line_dash="dash", line_color="#dc3545", annotation_text="High Threshold (70)")
    fig_bar.update_layout(
        title="Category Risk Scores (0–100 Scale)",
        yaxis=dict(title="Score", range=[0, 105]),
        xaxis=dict(title="Risk Category"),
        height=360,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with v_col2:
    # Radar Chart for multi-dimensional profile
    radar_cats = categories + [categories[0]]
    radar_scores = cat_scores + [cat_scores[0]]
    fig_radar = go.Figure(data=[
        go.Scatterpolar(
            r=radar_scores,
            theta=radar_cats,
            fill='toself',
            fillcolor='rgba(13, 110, 253, 0.2)',
            line=dict(color='#0d6efd', width=2),
            name="Project Profile"
        )
    ])
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100])
        ),
        title="Multi-Dimensional Risk Profile",
        height=360,
        margin=dict(l=40, r=40, t=40, b=20),
        showlegend=False
    )
    st.plotly_chart(fig_radar, use_container_width=True)


# ---------------------------------------------------------------------------
# Explainability & Recommendations
# ---------------------------------------------------------------------------
st.markdown("---")
st.subheader("🔍 Explainable Risk Contributing Factors & Mitigations")
st.write(
    "Transparent decomposition showing why each score was assigned, "
    "backed by specific metrics and rule-based mitigation actions."
)

for cat_name, cat_assessment in assessment.categories.items():
    cat_res = overall_result.category_results[cat_name]
    level_badge = f"{cat_assessment.level.value} RISK ({cat_assessment.score:.1f}/100)"

    with st.expander(f"📁 {cat_name} Risk — {level_badge}", expanded=(cat_assessment.score >= 40.0)):
        exp_col1, exp_col2 = st.columns([1.2, 1.2])

        with exp_col1:
            st.markdown("##### 🔎 Evidence & Contributing Factors")
            for factor in cat_assessment.contributing_factors:
                st.markdown(f"- {factor}")

            st.markdown("##### ⚙️ Component Score Breakdown")
            comp_table = []
            for comp_key, comp in cat_res.components.items():
                comp_table.append({
                    "Component": comp.name,
                    "Raw Value": comp.raw_value,
                    "Component Risk (0-100)": f"{comp.score:.1f}",
                    "Weight": f"{comp.weight * 100:.0f}%"
                })
            st.dataframe(comp_table, use_container_width=True, hide_index=True)

        with exp_col2:
            st.markdown("##### 🛠️ Targeted SEPM Mitigation Recommendations")
            for mit in cat_assessment.mitigations:
                st.markdown(f"- 💡 {mit}")


# ---------------------------------------------------------------------------
# Export Assessment
# ---------------------------------------------------------------------------
st.markdown("---")
st.subheader("💾 Export Assessment")

export_data = {
    "project_name": overall_result.project_name,
    "overall_score": overall_result.overall_score,
    "overall_risk_level": overall_result.overall_level.value,
    "category_scores": {cat: res.score for cat, res in overall_result.category_results.items()},
    "category_weights": overall_result.category_weights,
    "key_takeaways": assessment.key_takeaways,
    "contributing_factors": {
        cat: a.contributing_factors for cat, a in assessment.categories.items()
    },
    "mitigations": {
        cat: a.mitigations for cat, a in assessment.categories.items()
    }
}

json_str = json.dumps(export_data, indent=2)
st.download_button(
    label="📥 Download Assessment Report (JSON)",
    data=json_str,
    file_name=f"{project_name.lower().replace(' ', '_')}_risk_assessment.json",
    mime="application/json"
)

st.markdown("""
<div class="disclaimer-box">
    <strong>⚠️ Model Transparency Notice:</strong><br>
    This application is an explainable, rule-based decision support system.
    Scoring weights, component functions, and risk classifications represent structured heuristics grounded in software engineering management principles.
    They provide actionable indicators without claiming uncalibrated statistical machine learning prediction.
</div>
""", unsafe_allow_html=True)

