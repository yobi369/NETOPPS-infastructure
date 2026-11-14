# Institutional Pilot Charter

> Template only. Complete and approve this document with the participating institution before any technical data is transferred or assessed.

## 1. Evaluation identity

- Pilot ID:
- Institution / business unit:
- Evaluation title:
- Proposed start and end dates:
- Document owner:
- Version / approval date:

## 2. Governance and authorization

| Responsibility | Name or role | Approval / date |
|---|---|---|
| Institutional sponsor | | |
| Technical owner | | |
| Data owner | | |
| Security / privacy contact | | |
| NETOPPS delivery contact | | |
| Independent technical reviewer | | |

**Written authorization reference:**

**Permitted assessment environment and location:**

**Approved data classification:**

**Applicable retention, deletion and access-control requirements:**

## 3. Objectives and questions

State the specific decision this pilot is intended to inform. Avoid broad goals such as “improve resilience” without measurable evaluation questions.

- Primary evaluation question:
- Secondary questions:
- Existing analysis process to compare against:
- Expected decision at pilot close:

## 4. Scope

- Sites / regions included:
- Network or infrastructure boundary:
- Critical services included:
- Assets and dependency types included:
- Failure scenarios to model:
- Candidate improvement(s) to compare:
- Explicit exclusions:

Only use a sanitized or institution-approved model. No production access is implied.

## 5. Inputs and evidence

List approved input files and evidence references in the evidence register. For each input record its owner, source, collection date, freshness, validation status and permitted use.

- Topology source and version:
- Service inventory source and version:
- Dependency source and version:
- Capacity evidence and measurement window:
- Failure-domain and physical-diversity evidence:
- Criticality and RTO/RPO approval source:

Unknown or unverified values must remain marked unknown; do not infer them to complete the model.

## 6. Method

1. Freeze and hash the approved baseline input set.
2. Validate schema and semantic consistency.
3. Run the baseline resilience report.
4. Review findings with institutional engineers and record dispositions.
5. Build a separate candidate model for each approved proposal.
6. Run candidate comparison using the same topology and agreed scenarios.
7. Produce an executive assessment with evidence references, limitations and decisions.

## 7. Acceptance measures

Agree thresholds before execution. Complete the scorecard in the evidence register / acceptance checklist.

| Measure | Definition / denominator | Target agreed by institution | Reviewer |
|---|---|---|---|
| Input completeness | Required fields present / required fields agreed | | |
| Dependency validity | Reviewer-validated dependencies / reference dependencies | | |
| Finding acceptance | Accepted findings / findings reviewed | | |
| Scenario coverage | Completed scenarios / scenarios agreed | | |
| Analysis effort | Analyst hours for equivalent scope | | |
| Actionability | Recommendations accepted for further review | | |

Do not report a percentage when the denominator or reference set is unknown.

## 8. Deliverables

- Approved scope and data boundary.
- Versioned input manifest and evidence register.
- Baseline engine report.
- Candidate model(s) and comparison report.
- Findings disposition and action register.
- Executive before/after assessment.
- Limitations, unresolved assumptions and pilot exit decision.

## 9. Stop / re-scope conditions

Pause the pilot if authorization is unclear, data classification is incompatible with the environment, sensitive data is received outside the approved boundary, inputs cannot be validated, or a proposed test could affect production operations. Resume only after the institution's designated owner approves a revised scope.

## 10. Approval

Institutional sponsor: ____________________  Date: __________

Institutional technical owner: ______________  Date: __________

NETOPPS representative: __________________  Date: __________

This charter does not grant network access, authorize production changes, create an SLA, or replace a separate commercial agreement, data-processing agreement or security review.
