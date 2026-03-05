# IFRS 9 ECL Automation & Visualization Platform

## System Requirements Specification

**Document Reference:** SBU-IFRS9-SRS-2025-001
**Version:** 1.0
**Classification:** CONFIDENTIAL
**Prepared for:** Chief Risk Officer / Chief Financial Officer
**Date:** March 2026

> *This document contains confidential and proprietary information. Unauthorized distribution is strictly prohibited.*

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Current State Assessment](#2-current-state-assessment)
3. [Scope & Objectives](#3-scope--objectives)
4. [Functional Requirements](#4-functional-requirements)
   - 4.1 Staging Engine
   - 4.2 Probability of Default (PD) Model
   - 4.3 Loss Given Default (LGD) Model
   - 4.4 Exposure at Default (EAD) Model
   - 4.5 ECL Calculation Engine
5. [Dashboard & Visualization Requirements](#5-dashboard--visualization-requirements)
6. [Regulatory & Audit Reporting](#6-regulatory--audit-reporting)
7. [Integration Architecture](#7-integration-architecture)
8. [User Access & Governance](#8-user-access--governance)
9. [Implementation Roadmap](#9-implementation-roadmap)
10. [Success Criteria](#10-success-criteria)
11. [Document Approval](#11-document-approval)

---

## 1. Executive Summary

Stanbic Bank Uganda currently manages IFRS 9 Expected Credit Loss (ECL) computations through a fragmented process relying on multiple Excel workbooks, manual staging decisions, and static reporting. This approach introduces significant operational risk, audit concerns, and an inability to respond to real-time credit risk developments across the loan book.

This document specifies the requirements for a **unified IFRS 9 ECL Automation and Visualization Platform** that will:

- Automate ECL computation across all portfolios
- Provide real-time visibility into credit risk through interactive dashboards
- Ensure full audit traceability for every staging decision and provision calculation
- Support forward-looking macroeconomic scenario analysis
- Meet all Bank of Uganda (BOU) regulatory reporting requirements

**Target outcome:** Reduce the end-to-end ECL computation cycle from 2–3 weeks to under 1 hour, with full auditability and regulatory compliance.

---

## 2. Current State Assessment

### 2.1 Existing Process

The current IFRS 9 process involves the following pain points:

- ECL calculations are spread across **15+ interconnected Excel workbooks** managed by the Credit Risk and Finance teams.
- Stage classification relies on **manual review** by credit analysts, with inconsistent application of Significant Increase in Credit Risk (SICR) triggers across portfolios.
- PD, LGD, and EAD parameters are updated quarterly through **offline calibration exercises**, with limited forward-looking macro integration.
- Collateral valuations are **manually extracted** from the collateral management system and pasted into spreadsheets, creating version control issues.
- Board and BOU reporting requires **3–5 days of manual report preparation** after ECL computation.
- There is **no centralized audit trail** for staging overrides, parameter changes, or model adjustments.

### 2.2 Key Risks

| Risk Category | Description | Impact |
|---|---|---|
| Operational Risk | Manual data entry and formula errors in Excel | Material misstatement of provisions |
| Model Risk | Inconsistent SICR criteria application | Inappropriate staging, regulatory findings |
| Regulatory Risk | Inability to produce timely BOU disclosures | Potential supervisory sanctions |
| Audit Risk | No traceability for staging overrides | Qualified audit opinion risk |
| Concentration Risk | No real-time sector/segment visibility | Delayed response to portfolio deterioration |

---

## 3. Scope & Objectives

### 3.1 In Scope

- Automated staging engine (Stage 1, 2, 3) with configurable SICR triggers
- PD model framework: transition matrices, behavioral scorecards, forward-looking macro overlay
- LGD model: facility-level computation with collateral, recovery, cure rate, and discounting components
- EAD model: on-balance sheet and off-balance sheet (CCF-based) exposures
- ECL calculation engine: facility-level, 12-month and lifetime, scenario-weighted
- Executive dashboards and visualization layer
- Regulatory reporting: BOU credit risk schedules, IFRS 7 disclosures
- Integration with core banking (T24/Temenos), collateral management, and general ledger
- User access governance with maker-checker workflows

### 3.2 Out of Scope (Phase 1)

- Market risk and operational risk capital models
- Treasury and trading book IFRS 9 (financial instruments at FVOCI/FVTPL)
- Stress testing beyond the ECL macro scenario framework

---

## 4. Functional Requirements

### 4.1 Staging Engine

The staging engine is the backbone of the IFRS 9 system. It must automatically classify every credit exposure into the appropriate IFRS 9 stage based on configurable business rules, with full audit traceability.

#### 4.1.1 Stage Definitions

| Stage | Definition | ECL Horizon | Key Triggers |
|---|---|---|---|
| Stage 1 | Performing. No significant increase in credit risk since origination. | 12-month PD | Current or <30 DPD; no SICR triggers activated |
| Stage 2 | Underperforming. SICR detected since origination. | Lifetime PD | Quantitative PD deterioration, watchlist, restructuring, sector downgrade |
| Stage 3 | Credit-impaired / Default. | Lifetime PD (100% default) | 90+ DPD, recovery initiated, judicial management, significant adverse event |

#### 4.1.2 SICR Trigger Framework

The system must evaluate SICR using both quantitative and qualitative criteria. All thresholds must be configurable by the risk team without developer intervention.

**Quantitative Triggers:**

- **Absolute PD increase:** If the current PD exceeds the origination PD by more than a defined basis point threshold (e.g., 100 bps)
- **Relative PD change:** If the ratio of current PD to origination PD exceeds a defined multiple (e.g., 2.0x)
- **Days Past Due:** Rebuttable presumption at 30+ DPD (configurable)
- **Credit rating downgrade:** Internal rating deterioration beyond a defined notch threshold

**Qualitative Triggers:**

- Loan placed on watchlist or special mention
- Restructured / rescheduled facilities
- Sector-level downgrade (e.g., agriculture sector stress event)
- Country risk downgrade for cross-border exposures
- Forbearance measures granted

#### 4.1.3 Stage Migration Audit Trail

Every stage transition must be logged with the following metadata:

- Facility ID, customer ID, portfolio segment
- Previous stage, new stage, date of migration
- Trigger that caused the migration (system-generated or manual override)
- If manual override: approver name, justification, approval timestamp
- ECL impact of the migration (before vs. after provision)

---

### 4.2 Probability of Default (PD) Model

#### 4.2.1 PD Estimation Methodology

The system must support multiple PD estimation approaches:

- **Transition Matrix Methodology:** Build migration matrices from internal historical ratings data (minimum 5-year history). Generate Point-in-Time (PIT) and Through-the-Cycle (TTC) PD estimates.
- **Behavioral Scorecard PD:** For retail portfolios without granular internal ratings, compute PD from behavioral scorecard outputs mapped to default probability bands.
- **Hybrid approach:** Combine transition matrix and scorecard outputs based on portfolio segment.

#### 4.2.2 Forward-Looking Macroeconomic Overlay

The PD model must incorporate macroeconomic scenarios to produce forward-looking estimates. The system must support:

- A minimum of **three scenarios**: Baseline, Optimistic, and Downturn
- **Probability weighting** of scenarios (e.g., 50% / 20% / 30%) configurable by the economics team
- **Macro variable integration** via regression or satellite model linking macro variables to PD

**Required Macro Variables for Uganda:**

| Variable | Source | Update Frequency | Typical Scenario Range |
|---|---|---|---|
| Real GDP growth rate | Bank of Uganda / UBOS | Quarterly | +2% to +7% |
| Inflation rate (CPI) | UBOS | Monthly | 3% to 12% |
| Central Bank Rate (CBR) | Bank of Uganda | Bi-monthly | 8% to 15% |
| Exchange rate (UGX/USD) | Bank of Uganda | Daily | 3,500 to 4,200 |
| Coffee export prices | Uganda Coffee Development Authority | Monthly | $1.50 to $3.50/lb |
| Oil import prices | International benchmarks | Daily | $60 to $120/bbl |
| Lending rates (commercial) | BOU Financial Stability Report | Quarterly | 16% to 24% |

#### 4.2.3 PD Term Structure

For Stage 2 exposures requiring lifetime ECL, the system must project PD curves over the remaining contractual maturity of each facility. This requires:

- Building cumulative PD curves from the transition matrices
- Applying the macro scenario overlay to shift the PD curve
- Capping lifetime PD at 100%

---

### 4.3 Loss Given Default (LGD) Model

LGD must be computed at the facility level incorporating collateral, recovery history, and time-value discounting.

#### 4.3.1 LGD Components

| Component | Description | Data Source |
|---|---|---|
| Collateral recovery | Forced-sale value of pledged collateral, net of disposal costs, with regulatory haircuts by collateral type | Collateral management system |
| Historical recovery rate | Actual recovery rates from the bank's workout portfolio, segmented by product and collateral type | Recovery / workout database |
| Time-to-recovery discounting | Discount future recoveries at the Effective Interest Rate (EIR) of the facility to reflect time value of money | Loan system (EIR) |
| Cure rate adjustment | For Stage 2 exposures, probability of reverting to performing status before default occurs | Internal transition data |
| Direct costs | Legal fees, collection costs, and administration expenses associated with the workout process | Finance / cost center data |

#### 4.3.2 Collateral Haircuts

The system must apply the following haircuts to collateral values (configurable):

| Collateral Type | Standard Haircut | Stressed Haircut | Revaluation Frequency |
|---|---|---|---|
| Residential property | 30% | 45% | Every 3 years (or on trigger) |
| Commercial property | 40% | 55% | Every 2 years |
| Motor vehicles | 50% | 65% | Annually |
| Government securities | 5% | 10% | Mark-to-market daily |
| Cash deposits | 0% | 0% | N/A |
| Listed equities | 30% | 50% | Mark-to-market daily |
| Agricultural land | 45% | 60% | Every 2 years |
| Unsecured | 100% (no recovery from collateral) | 100% | N/A |

---

### 4.4 Exposure at Default (EAD) Model

#### 4.4.1 On-Balance Sheet

For drawn facilities, EAD equals the outstanding principal balance plus accrued interest as at the reporting date.

#### 4.4.2 Off-Balance Sheet

For undrawn commitments and contingent liabilities, EAD is calculated as:

> **EAD = Drawn Amount + (Undrawn Commitment × Credit Conversion Factor)**

| Facility Type | Default CCF | Calibration Approach |
|---|---|---|
| Revolving credit facilities | 75% | Internal behavioral analysis of drawdown patterns pre-default |
| Undrawn term loan commitments | 50% | Historical utilization data |
| Letters of credit | 20% | Regulatory standard; validate against internal data |
| Performance guarantees | 50% | Regulatory standard; validate against claim history |
| Financial guarantees | 100% | Full conversion assumed |

---

### 4.5 ECL Calculation Engine

#### 4.5.1 Core Formula

> **ECL = ∑ [ PD(t) × LGD(t) × EAD(t) × DF(t) ]**

Where:
- **PD(t)** = marginal probability of default in period t
- **LGD(t)** = loss given default at time t
- **EAD(t)** = exposure at default at time t
- **DF(t)** = discount factor at the facility's effective interest rate

#### 4.5.2 ECL Horizon

- **Stage 1:** 12-month PD horizon (sum PD over months 1–12)
- **Stage 2:** Lifetime PD horizon (sum PD over remaining contractual maturity)
- **Stage 3:** PD = 100%; ECL = LGD × EAD, discounted at EIR

#### 4.5.3 Scenario Weighting

The system must compute ECL under each macroeconomic scenario independently and then produce a probability-weighted average:

> **Final ECL = (W_base × ECL_base) + (W_opt × ECL_opt) + (W_down × ECL_down)**

Scenario weights must be configurable and auditable, with approval workflow for changes.

#### 4.5.4 Granularity

- ECL must be computed at the **individual facility level**, not portfolio level.
- **Full drill-down capability:** from entity total → segment → portfolio → individual facility.
- Each facility's ECL must be fully decomposable into its PD, LGD, EAD, and discount factor components.

---

## 5. Dashboard & Visualization Requirements

The visualization layer is the primary interface for executive management, the Board Risk Committee, and the credit risk team. It must provide real-time insight into the ECL position across the entire portfolio.

### 5.1 Executive Summary Dashboard

- Total ECL by stage (absolute amount and as % of gross exposure)
- Coverage ratios: provision / gross exposure, by stage and portfolio
- Period-over-period ECL movement: opening balance, new originations, stage migrations, derecognitions, parameter changes, closing balance
- Key risk indicators (KRI): 30+ DPD rate, 90+ DPD rate, Stage 2 ratio, Stage 3 ratio

### 5.2 Stage Migration Waterfall

A visual waterfall chart showing the volume and value of exposures migrating between stages during the reporting period. This is the **single most important visual** for Board reporting. Must show:

- Count of facilities and UGX value
- Net ECL impact of each migration direction (1→2, 2→3, 2→1, 3→2, etc.)
- Top 10 facilities driving migration by ECL impact

### 5.3 Vintage Analysis

- ECL and default rates by loan origination cohort (vintage)
- Comparison of recent vintages vs. historical averages
- Early warning: identify vintages deteriorating faster than expected

### 5.4 Sector & Segment Heatmap

- Matrix visualization: rows = sectors (agriculture, trade, manufacturing, real estate, personal lending, etc.), columns = key metrics (gross exposure, ECL, coverage ratio, Stage 2 %, Stage 3 %)
- Color-coded: green (low risk), amber (watch), red (high risk)
- Drill-down to individual facilities within any sector/segment cell

### 5.5 Sensitivity Analysis Dashboard

- Interactive scenario selector: adjust macro variables and see real-time ECL impact
- Scenario comparison: side-by-side ECL under Baseline, Optimistic, and Downturn
- Custom stress test: allow ad-hoc scenarios (e.g., "What if GDP drops 2% and UGX depreciates 15%?")
- Parameter sensitivity: marginal impact of 1% change in PD, LGD, or EAD on total ECL

### 5.6 Model Performance Monitoring

- PD backtesting: predicted vs. actual default rates by rating grade and portfolio
- LGD backtesting: predicted vs. realized loss rates
- Staging accuracy: percentage of loans correctly staged vs. ex-post outcomes
- Model stability metrics: Population Stability Index (PSI), Gini coefficient trend

---

## 6. Regulatory & Audit Reporting

### 6.1 Bank of Uganda (BOU) Reports

- Credit risk schedules as required under the Financial Institutions Act (FIA) 2004 and BOU regulations
- Quarterly credit risk returns: classified assets by stage, sector, and product
- Provisioning adequacy report: comparison of IFRS 9 ECL vs. BOU minimum provisioning requirements

### 6.2 IFRS 7 Financial Instrument Disclosures

- Credit quality tables: gross carrying amount and ECL by stage and internal rating grade
- Reconciliation of loss allowances: opening balance, charges, releases, write-offs, recoveries, closing balance
- Sensitivity disclosures: impact of changes in key assumptions on ECL
- Significant increase in credit risk: criteria used, quantitative triggers, qualitative overlays
- Collateral disclosure: carrying amounts of collateral held, by type

### 6.3 Audit Trail & Traceability

For any individual facility, an auditor must be able to query the system and retrieve:

1. The facility's current stage and the specific trigger that determined it
2. The PD used (point-in-time, scenario-weighted), with the source model and calibration date
3. The LGD computation: collateral value, haircut applied, recovery rate, time-to-recovery, cure rate
4. The EAD computation: drawn balance, undrawn commitment, CCF applied
5. The discount rate (EIR) and discounting methodology
6. The macro scenario weights and individual scenario ECLs
7. The final ECL amount and its contribution to the portfolio/entity total

---

## 7. Integration Architecture

### 7.1 Source Systems

| System | Data | Integration Method | Frequency |
|---|---|---|---|
| Core Banking (T24/Temenos) | Loan book, balances, DPD, payments, interest rates, maturity | API / Batch ETL | Daily (monitoring), month-end (reporting) |
| Collateral Management System | Collateral type, valuation, forced-sale value, revaluation dates | API / Database link | Daily sync |
| Internal Rating System | Customer ratings, rating history, rating migration | API / Batch | Daily |
| General Ledger | Account codes for provisioning entries | API (push) | Month-end |
| External Data Providers | Macro variables (GDP, CPI, exchange rates) | API / Manual upload | Quarterly (or as updated) |

### 7.2 Output Integrations

- **General Ledger:** Automated provisioning journal entries (debit provision expense, credit provision account) at month-end close
- **Regulatory Reporting Tool:** Automated population of BOU return templates
- **Data Warehouse:** ECL data mart for historical trend analysis
- **External Audit Portal:** Read-only access for external auditors during year-end audit

---

## 8. User Access & Governance

### 8.1 Role-Based Access Control

| Role | Access Level | Capabilities |
|---|---|---|
| Credit Risk Team | Full model access | Run ECL computations, adjust parameters, configure SICR triggers, approve staging overrides |
| Finance Team | Report access | View ECL outputs, run regulatory reports, generate journal entries |
| Model Validation | Read-only + backtesting | Access all model documentation, backtesting results, parameter history |
| Executive Management | Dashboard only | View executive dashboards, download Board reports |
| External Audit | Read-only (time-limited) | Query facility-level ECL calculations, view audit trail |
| System Administrator | Full system access | User management, system configuration, data refresh scheduling |

### 8.2 Maker-Checker Workflow

All of the following actions require maker-checker approval before taking effect:

- Changes to PD model parameters or calibration
- Changes to LGD assumptions (haircuts, recovery rates)
- Changes to CCF values
- Changes to macroeconomic scenario weights
- Manual staging overrides (Stage 1 → 2, or preventing migration)
- Changes to SICR trigger thresholds

---

## 9. Implementation Roadmap

| Phase | Timeline | Deliverables | Key Milestones |
|---|---|---|---|
| **Phase 1: Foundation** | Months 1–4 | Staging engine, ECL calculation core, data integration (T24), basic reporting | First automated ECL run; parallel run with existing spreadsheets |
| **Phase 2: Visualization** | Months 5–7 | Executive dashboards, stage migration waterfall, sensitivity analysis, IFRS 7 disclosures | Board-ready dashboard; BOU report automation |
| **Phase 3: Advanced Models** | Months 8–10 | Forward-looking macro overlay, PD term structure, model performance monitoring | Macro scenario integration; backtesting framework live |
| **Phase 4: Optimization** | Months 11–12 | Performance tuning, full audit trail, external audit portal, user training, documentation | Go-live; decommission spreadsheet process |

---

## 10. Success Criteria

The platform will be deemed successful when the following criteria are met:

| Criterion | Target | Measurement |
|---|---|---|
| ECL computation time | < 1 hour (full book) | Timed execution from data refresh to final ECL output |
| Staging accuracy | > 95% agreement with expert review | Quarterly sample review by model validation |
| Audit traceability | 100% facility-level drill-down | Every ECL can be decomposed to PD, LGD, EAD, DF, scenario |
| Regulatory reporting | Same-day BOU report generation | Time from month-end close to report submission |
| Model backtesting | PD deviation < 20% from actuals | Annual backtesting exercise |
| User adoption | > 90% of ECL workflow on platform | Decommission of legacy spreadsheets within 3 months of go-live |
| Board stress testing | Real-time scenario response | Custom stress test results available within 5 minutes |

---

## 11. Document Approval

| Role | Name | Signature | Date |
|---|---|---|---|
| Chief Risk Officer | | | |
| Chief Financial Officer | | | |
| Head of Credit Risk | | | |
| Head of Model Validation | | | |
| Chief Information Officer | | | |
| External Systems Vendor | | | |

---

*— End of Document —*

*STANBIC BANK UGANDA | IFRS 9 ECL Automation Platform | SBU-IFRS9-SRS-2025-001 | CONFIDENTIAL*
