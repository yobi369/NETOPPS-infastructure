# Commercial Value Measurement Framework

## Purpose

This framework defines how an institutional or telecom evaluation should test whether NETOPPS creates measurable value. It deliberately avoids assumed savings, invented outage costs, unsupported return-on-investment claims and model scores presented as financial outcomes.

The evaluation compares an existing, operator-approved analysis workflow with a NETOPPS-assisted workflow on the same bounded scope and evidence set.

## Value hypotheses to test

| Value hypothesis | Measure | Evidence required |
|---|---|---|
| Faster resilience analysis | Elapsed analyst hours from accepted input to reviewed assessment | Time logs, task definitions, reviewer sign-off |
| Better dependency coverage | Relevant dependencies identified and validated / total dependencies in an agreed reference set | Operator-reviewed reference inventory and traceable findings |
| More useful failure prioritisation | Accepted high-priority findings surfaced, with rationale | Engineering review and disposition log |
| More consistent scenario review | Scenarios completed and documented / scenarios agreed for the evaluation | Scenario register and reproducible outputs |
| Better candidate-design comparison | Time and effort to compare baseline and candidate models | Versioned inputs, reports and analyst time logs |
| More actionable recovery planning | Findings converted into owned, approved actions | Action register, owner, due date and approval record |

These are hypotheses, not claims of achieved performance. NETOPPS output counts or weighted-impact values are not substitutes for independent validation.

## Baseline and comparison protocol

1. **Define the unit of work.** Select one bounded network segment, service group, site cluster or architecture review.
2. **Agree the reference set.** Have the operator define the known assets, service dependencies, failure scenarios and expected findings.
3. **Record the existing process.** Measure staff time, tools used, review steps, output format and known limitations without changing the process.
4. **Run NETOPPS on the same scope.** Use the same approved source data and documented assumptions.
5. **Review blind to the tool where practical.** Qualified operator reviewers assess relevance, correctness, omissions and false positives.
6. **Record dispositions.** Classify each finding as accepted, rejected, duplicate, incomplete or requiring further evidence.
7. **Repeat where possible.** A single scenario or one analyst is not enough to establish a stable productivity claim.
8. **Publish limitations.** Record sample size, exclusions, data quality, reviewer roles and any differences in scope.

## Core scorecard

Use the following fields for each evaluation run:

| Field | Description |
|---|---|
| Evaluation ID | Unique pilot identifier |
| Scope | Agreed topology, services and scenarios |
| Input version | Hash or controlled version of each input file |
| Baseline analyst hours | Measured time for the existing workflow |
| NETOPPS analyst hours | Measured time for the NETOPPS-assisted workflow |
| Reference dependencies | Operator-reviewed dependency count |
| Accepted dependencies | Dependencies validated by reviewers |
| Accepted findings | Findings accepted as relevant and correct |
| Rejected or duplicate findings | Findings requiring correction or exclusion |
| Scenario coverage | Completed scenarios / agreed scenarios |
| Actionable recommendations | Recommendations accepted for further engineering review |
| Data-quality exceptions | Missing, stale, contradictory or unverified inputs |
| Reviewer sign-off | Role and date of authorised reviewers |
| Limitations | Scope exclusions and unresolved assumptions |

Do not report percentages where the denominator is unknown or where the reference set has not been independently agreed.

## Financial value: only after operational evidence

A financial case may be developed only when the customer supplies and approves the relevant cost inputs. Potential categories include:

- Internal engineering hours spent on the measured analysis process.
- External consulting or assessment costs for the same scope.
- Cost of repeated manual model preparation.
- Approved costs associated with specific, documented resilience work.

Do not multiply NETOPPS weighted-impact scores by an assumed outage cost. Do not claim that a simulated avoided failure equals an avoided real outage. Do not attribute operational savings to NETOPPS unless the evaluation isolates its contribution and the customer validates the calculation.

A customer-approved financial model should show inputs, sources, calculation method, uncertainty range, exclusions and approval owner. Where these inputs are unavailable, report operational measurements only.

## Evidence required before external claims

A public case study, quantified productivity claim or financial ROI statement requires:

- Written customer permission to publish.
- An agreed baseline and repeatable measurement method.
- Reviewer-validated results and sample scope.
- Clear separation of measured results from projections.
- Disclosure of material limitations and confounding factors.
- Legal and commercial review of the proposed wording.

Until these gates are met, use language such as "evaluation hypothesis", "measured in this pilot" or "operator-reviewed finding". Avoid "reduces outages", "prevents downtime", "guarantees resilience" or quantified savings without evidence.

## Suggested pilot exit criteria

The customer and NETOPPS team should agree numeric thresholds before the pilot begins. Example categories include:

- Input completeness and schema acceptance.
- Percentage of reference dependencies correctly represented.
- Reviewer acceptance rate for high-priority findings.
- Completion of the agreed failure-scenario set.
- Time required to produce and review the assessment.
- Number of actionable recommendations accepted for further engineering review.
- No unresolved critical security, privacy or data-handling issue.

Threshold values must be agreed with the customer for the specific scope. This document does not prescribe or claim achieved results.
