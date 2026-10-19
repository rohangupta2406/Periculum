# Scoring Formulas, Weights, and Design Assumptions

## 1. System Design Principles & Heuristics

**Periculum** is an explainable, rule-based decision support system. The formulas and weights defined herein represent structured heuristics grounded in software engineering management literature (e.g., Earned Value Management, COCOMO principles, Agile velocity, and defect density patterns).

> [!NOTE]
> **Heuristic Model Notice**: These scoring algorithms are transparent, deterministic heuristics designed to make project risks visible and actionable. They provide decision support without claiming uncalibrated statistical machine learning predictions.


---

## 2. Classification Thresholds

All risk scores (component, category, and overall) operate on a normalized scale from **0.0 to 100.0**:

| Score Range | Classification | Interpretive Action |
| :--- | :--- | :--- |
| **0.0 – 39.9** | **LOW RISK** | Project operations within expected tolerances; continue standard monitoring. |
| **40.0 – 69.9** | **MEDIUM RISK** | Emerging vulnerabilities detected; proactive corrective intervention advised. |
| **70.0 – 100.0** | **HIGH RISK** | Severe project threats present; immediate executive escalation required. |

---

## 3. Weighting Hierarchy

### Overall Project Risk Weights

| Risk Category | Base Weight (Budget Active) | Redistributed Weight (Budget Inactive) | Rationale |
| :--- | :---: | :---: | :--- |
| **Schedule Risk** | 35% | $\frac{35}{95} \approx 36.84\%$ | Timeline slippage is the primary direct driver of stakeholder dissatisfaction and contractual breach. |
| **Resource Risk** | 20% | $\frac{20}{95} \approx 21.05\%$ | Staffing deficits and engineer burnout drive downstream schedule and quality failures. |
| **Quality Risk** | 20% | $\frac{20}{95} \approx 21.05\%$ | Unresolved defects create release-blocking instability and post-deployment failure. |
| **Requirement Risk** | 20% | $\frac{20}{95} \approx 21.05\%$ | Scope volatility ("churn") creates compounding rework across design and code. |
| **Budget Risk (Optional)** | 5% | 0.0% (Disabled) | Optional secondary indicator; disabled by default to maintain focus on technical delivery. |
| **Total** | **100.0%** | **100.0%** | When budget is disabled, its 5% weight is distributed proportionally. |

---

## 4. Category Scoring Formulations

### 4.1 Schedule Risk (Category Weight: 35% / 36.84%)
Schedule risk balances historical variance, forward-looking pace pressure, task delays, and deadline proximity.

$$\text{Schedule Risk} = 0.40 \cdot S_{\text{var}} + 0.30 \cdot S_{\text{pressure}} + 0.20 \cdot S_{\text{delayed}} + 0.10 \cdot S_{\text{deadline}}$$

1. **Schedule Variance Risk ($S_{\text{var}}$, Weight: 40%)**:
   - Schedule Variance $SV = \text{Task Progress \%} - \text{Time Elapsed \%}$.
   - If $SV \ge 0$: Score $= 0.0$ (on or ahead of schedule).
   - If $SV < 0$ and not overdue: Score $= \text{clamp}(|SV| \cdot 2.0, 0, 100)$. (e.g., $-25\%$ variance maps to $50$ risk).
   - If project is overdue ($DaysElapsed > PlannedDuration$ and work remains): Score $= \text{clamp}(70.0 + \text{DaysOverdue} \cdot 2.0, 70, 100)$.
2. **Remaining Work Pressure ($S_{\text{pressure}}$, Weight: 30%)**:
   - Compares remaining work $\%$ against remaining timeline $\%$.
   - Ratio $R = \frac{\text{Remaining Work \%}}{\text{Remaining Time \%}}$.
   - If work remaining $= 0\%$: Score $= 0.0$.
   - If overdue with work remaining: Score $= 100.0$.
   - If $R \le 1.0$: Score $= \text{clamp}(R \cdot 20.0, 0, 20)$.
   - If $R > 1.0$: Score $= \text{clamp}(20.0 + (R - 1.0) \cdot 53.33, 20, 100)$.
3. **Delayed Tasks Risk ($S_{\text{delayed}}$, Weight: 20%)**:
   - Delayed task ratio $D = \frac{\text{Delayed Tasks}}{\text{Total Tasks}} \cdot 100$.
   - Score $= \text{clamp}(D \cdot 2.5, 0, 100)$.
4. **Deadline Proximity Risk ($S_{\text{deadline}}$, Weight: 10%)**:
   - Captures compression of contingency buffers as delivery deadline approaches:
   - If work remaining $= 0\%$: Score $= 0.0$.
   - If time elapsed $\le 50\%$: Score $= 10.0$ (broad flexibility).
   - If $50\% < \text{time elapsed} \le 85\%$: Score $= 10.0 + (\text{elapsed} - 50.0) \cdot 1.4$.
   - If $\text{time elapsed} > 85\%$: Score $= 60.0 + (\text{elapsed} - 85.0) \cdot 2.67$.

---

### 4.2 Resource Risk (Category Weight: 20% / 21.05%)
Resource risk assesses team availability, allocation imbalance, and overall exhaustion.

$$\text{Resource Risk} = 0.40 \cdot R_{\text{avail}} + 0.40 \cdot R_{\text{imbalance}} + 0.20 \cdot R_{\text{shortage}}$$

1. **Team Availability Risk ($R_{\text{avail}}$, Weight: 40%)**:
   - Availability $\% = \frac{\text{Available Members}}{\text{Required Members}} \cdot 100$.
   - Shortfall $\%$ $S = \max(0, 100 - \text{Availability \%})$.
   - Score $= \text{clamp}(S \cdot 2.0, 0, 100)$.
2. **Workload Imbalance Risk ($R_{\text{imbalance}}$, Weight: 40%)**:
   - Imbalance Spread $\Delta W = \max(0, \text{Highest Workload} - \text{Average Workload})$.
   - Peak Overload $P = \max(0, \text{Highest Workload} - 100\%)$.
   - Score $= \text{clamp}(\Delta W \cdot 1.2 + P \cdot 0.8, 0, 100)$.
3. **Resource Shortage Risk ($R_{\text{shortage}}$, Weight: 20%)**:
   - Team Overload $\Omega = \max(0, \text{Average Workload} - 100\%)$.
   - Score $= \text{clamp}(S \cdot 0.5 + \Omega \cdot 1.5, 0, 100)$.

---

### 4.3 Quality Risk (Category Weight: 20% / 21.05%)
Quality risk evaluates backlog volume, critical severity concentration, and defect growth trajectory.

$$\text{Quality Risk} = 0.30 \cdot Q_{\text{open}} + 0.35 \cdot Q_{\text{critical}} + 0.35 \cdot Q_{\text{growth}}$$

1. **Open Defects Volume ($Q_{\text{open}}$, Weight: 30%)**:
   - Score $= \text{clamp}(\text{Open Bugs} \cdot 5.0, 0, 100)$ (20 open bugs saturates at 100).
2. **Critical Defect Severity ($Q_{\text{critical}}$, Weight: 35%)**:
   - Ratio $CR = \frac{\text{Critical Bugs}}{\text{Open Bugs}} \cdot 100$ (if open bugs $> 0$).
   - Score $= \text{clamp}(CR \cdot 0.6 + \text{Critical Bugs} \cdot 15.0, 0, 100)$.
3. **Defect Growth Trend ($Q_{\text{growth}}$, Weight: 35%)**:
   - **Zero Baseline Protection**:
     - When previous period bugs $= 0$ and current bugs $= 0$: Score $= 0.0$.
     - When previous period bugs $= 0$ and current bugs $> 0$: Score $= \text{clamp}(\text{Current Bugs} \cdot 15.0, 15, 85)$.
   - **Standard Growth**:
     - When previous period bugs $> 0$:
       $$\text{Growth \%} = \frac{\text{Current Bugs} - \text{Previous Bugs}}{\text{Previous Bugs}} \cdot 100$$
     - If $\text{Growth \%} \le 0$: Score $= 0.0$ (flat or improving defect trend).
     - If $\text{Growth \%} > 0$: Score $= \text{clamp}(\text{Growth \%} \cdot 1.0, 0, 100)$.

---

### 4.4 Requirement Risk (Category Weight: 20% / 21.05%)
Requirement risk reflects scope creep, change velocity, and structural architectural instability.

$$\text{Requirement Risk} = 0.50 \cdot REQ_{\text{rate}} + 0.30 \cdot REQ_{\text{freq}} + 0.20 \cdot REQ_{\text{major}}$$

1. **Requirement Change Rate ($REQ_{\text{rate}}$, Weight: 50%)**:
   - Rate $CR = \frac{\text{Changed Requirements}}{\text{Total Requirements}} \cdot 100$.
   - Score $= \text{clamp}(CR \cdot 2.5, 0, 100)$ ($40\%$ change rate saturates at 100).
2. **Current Change Velocity ($REQ_{\text{freq}}$, Weight: 30%)**:
   - Frequency $CF = \frac{\text{Current Period Changes}}{\text{Total Requirements}} \cdot 100$.
   - Score $= \text{clamp}(CF \cdot 3.5, 0, 100)$.
3. **Major / Architectural Scope Changes ($REQ_{\text{major}}$, Weight: 20%)**:
   - Major Ratio $MR = \frac{\text{Major Changes}}{\text{Changed Requirements}} \cdot 100$ (if changed $> 0$).
   - Score $= \text{clamp}(MR \cdot 0.6 + \text{Major Changes} \cdot 15.0, 0, 100)$.

---

### 4.5 Optional Budget Risk (Category Weight: 5% when enabled)
Budget risk evaluates cost variance against delivered progress:

$$\text{Budget Risk} = 0.70 \cdot B_{\text{variance}} + 0.30 \cdot B_{\text{burn}}$$

- Cost Variance Proxy: $\text{Work Completed \%} - \text{Budget Spent \%}$.
- If work completed $\ge$ budget spent: Risk $= 0.0$.
- If budget spent $>$ work completed: $B_{\text{variance}} = \text{clamp}(|\text{Variance}| \cdot 2.5, 0, 100)$.
- Burn Ratio: $\frac{\text{Budget Spent \%}}{\text{Work Completed \%}}$. If $> 1.0$: $B_{\text{burn}} = \text{clamp}((\text{Ratio} - 1.0) \cdot 100, 0, 100)$.
