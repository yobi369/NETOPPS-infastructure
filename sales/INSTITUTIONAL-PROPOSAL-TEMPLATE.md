# Commercial Proposal — NETOPPS Infrastructure

**CONFIDENTIAL — CUSTOMER-SPECIFIC DRAFT**

> This is a proposal template, not an offer capable of acceptance until all commercial, legal, and technical schedules are completed and approved by the authorized rights holder. All bracketed fields must be completed or removed. No price, licence, support commitment, SLA, warranty, or implementation capacity is implied by this template.

## 1. Proposal details

| Field | Details |
|---|---|
| Prepared for | [Customer legal name] |
| Department / business unit | [Department] |
| Prepared by | [Licensor legal name / authorized representative] |
| Proposal reference | [Reference] |
| Date | [Date] |
| Valid until | [Date] |
| Customer contact | [Name, title, business email] |
| Version | [Version] |

## 2. Executive summary

[Customer] is seeking to [describe the documented infrastructure, resilience, inventory, or planning problem]. NETOPPS Infrastructure is proposed as a local, safety-first toolkit to help the authorized team validate operator-supplied infrastructure inventories, model service dependencies, examine defined failure scenarios, compare a baseline with proposed alternatives, and prepare an explainable resilience briefing.

The proposed engagement is limited to the scope and deliverables in this document. NETOPPS is a decision-support tool; it does not control production infrastructure or guarantee availability, recovery, compliance, or avoided outages.

## 3. Customer context and objectives

**Current environment:** [Sites, services, platforms, network domains, and relevant constraints. Avoid including secrets or sensitive topology in this proposal.]

**Challenges confirmed during discovery:**
- [Challenge 1]
- [Challenge 2]
- [Challenge 3]

**Desired outcomes:**
- [Measurable outcome 1]
- [Measurable outcome 2]
- [Measurable outcome 3]

**Decision to be supported:** [What decision will the assessment inform?]

## 4. Proposed solution

NETOPPS can support the agreed use case through:

- structured inventory validation and addressing-plan checks;
- topology and service dependency modelling from customer-approved inputs;
- defined node, link, site, and correlated failure scenarios;
- criticality-weighted impact prioritization using customer-supplied metadata;
- candidate comparison for proposed dependency or redundancy changes;
- declared capacity gap review where input evidence is available;
- JSON and offline HTML resilience reporting.

Select only the capabilities included in the agreed scope. Do not imply live telemetry, automated configuration, hosted access, or vendor integration.

## 5. Scope of work

| Workstream | Included activity | Customer responsibility |
|---|---|---|
| Discovery | [Workshops, service scope, decision questions] | Provide authorized stakeholders and objectives |
| Data preparation | [Input templates, validation guidance, sanitization] | Supply approved, accurate, sanitized inputs |
| Baseline assessment | [Inventory and resilience analysis] | Validate assumptions and source data |
| Candidate scenarios | [Number and description of proposed alternatives] | Approve scenario assumptions |
| Review workshop | [Format, duration, participants] | Attend and provide feedback |
| Handover | [Reports, findings, limitations, next-step register] | Accept or document exceptions |

**In-scope sites:** [List]  
**In-scope services:** [List]  
**In-scope environments:** [List]  
**Excluded sites/services:** [List]  
**Authorized connectivity checks, if any:** [Explicit targets, authorization, window, limits; otherwise state “none”]

## 6. Deliverables and acceptance

| Deliverable | Format | Acceptance criteria | Due date |
|---|---|---|---|
| Input and assumptions register | [CSV/JSON/document] | Customer confirms scope and assumptions | [Date] |
| Baseline assessment | [JSON + HTML/PDF if separately prepared] | Agreed inputs processed; findings and limitations documented | [Date] |
| Candidate comparison | [JSON + HTML/document] | Agreed scenarios compared against baseline | [Date] |
| Executive briefing | [HTML/document/presentation] | Includes findings, evidence gaps, recommendations, caveats | [Date] |
| Handover session | [Remote/on-site] | Session completed and materials supplied | [Date] |

Acceptance period: [Number] business days after delivery. Customer must provide written acceptance or a consolidated list of material deviations from the agreed criteria. A deliverable is not rejected solely because model results reveal an unfavorable outcome or because the customer's underlying infrastructure has a risk.

## 7. Delivery approach and indicative schedule

| Phase | Activities | Indicative duration |
|---|---|---|
| 1. Initiation | Scope confirmation, stakeholders, authorization | [Duration] |
| 2. Data readiness | Sanitized inventory and dependency inputs | [Duration] |
| 3. Baseline | Validation, model review, initial report | [Duration] |
| 4. Candidate analysis | Agreed failure and resilience alternatives | [Duration] |
| 5. Executive review | Findings, limitations, recommendations | [Duration] |
| 6. Handover | Final deliverables and close-out | [Duration] |

Schedule begins only after the agreement is signed, required access/authorization is confirmed, and customer inputs are received. Delays in customer data or approvals may change the schedule by written agreement.

## 8. Licensing option

Select and complete one:

- [ ] Community edition under AGPL-3.0-or-later; customer is responsible for reviewing and complying with the licence.
- [ ] Separate commercial licence under a signed agreement.

For a commercial licence, identify:
- licensed components and release: [Details]
- customer legal entity: [Entity]
- permitted affiliates: [List / none]
- sites / installations / environments: [Scope]
- users / operators: [Scope]
- source access and modification rights: [Details]
- embedding / redistribution / service provider rights: [Details]
- term and renewal: [Details]

The commercial licence agreement, not this proposal alone, defines the rights granted. Third-party components remain under their own licences.

## 9. Fees and payment schedule

| Line item | Quantity / basis | Fee (currency) |
|---|---|---:|
| Software licence | [Metric / term] | [Amount] |
| Assessment / implementation | [Days / fixed scope] | [Amount] |
| Data preparation support | [Scope] | [Amount] |
| Training / workshop | [Sessions] | [Amount] |
| Support / maintenance | [Term / scope] | [Amount] |
| Other | [Description] | [Amount] |
| **Subtotal** | | **[Amount]** |
| Taxes | [Applicable taxes] | [Amount] |
| **Total** | | **[Amount]** |

Payment milestones: [e.g. deposit / delivery / acceptance — specify amounts and dates].  
Currency: [KES / USD / other].  
Quote validity: [Date].  
Purchase order requirements: [Details].

No pricing is established until completed and approved by the rights holder. Tax treatment must be confirmed for the relevant parties and jurisdiction.

## 10. Support, maintenance, and service levels

Select only if expressly included in a signed agreement:

- Support period: [Dates]
- Support hours and timezone: [Details]
- Support channel: [Details]
- Severity definitions: [Details]
- Response targets: [Targets; distinguish response from resolution]
- Included updates: [Versions / period]
- Maintenance window: [Details]
- Exclusions and customer dependencies: [Details]

If not completed and signed, support, maintenance, uptime, response targets, and SLA commitments are excluded.

## 11. Security, data, and deployment

Proposed deployment: [Customer-controlled local environment / other explicitly reviewed model].

Customer responsibilities:
- authorize the assessment and all connectivity checks in writing;
- provide sanitized, accurate, minimum-necessary input data;
- remove credentials, private keys, personal data, and unrelated sensitive information;
- control access to source files and generated reports;
- determine data classification, retention, backups, and secure deletion;
- validate outputs before making operational changes.

The current NETOPPS resilience workflow is local and simulation-only. It does not upload topology files to a NETOPPS hosted service, collect central telemetry, provide hosted multi-tenant accounts, or apply network configuration changes. Any future processing of personal data, hosted deployment, or access to production systems requires a separate security and legal review.

## 12. Assumptions, dependencies, and exclusions

**Assumptions:** [Accurate data, stakeholder availability, environment constraints, Python runtime, customer approvals.]

**Dependencies:** [Input delivery dates, customer reviewers, procurement, security approvals.]

**Exclusions unless separately agreed:** network redesign implementation; live monitoring; device discovery; configuration changes; automated failover; carrier/cloud integrations; security penetration testing; certification; regulatory audit; disaster recovery execution; guaranteed business outcomes.

## 13. Risks and limitations

Assessment quality depends on the completeness and accuracy of operator-supplied inputs. Declared capacities, failure domains, physical diversity evidence, criticality, traffic, RTO, and RPO are not independently verified by the software. Modelled failure scenarios are not outage probabilities. Recommendations must be reviewed against physical diagrams, supplier evidence, authorized lab tests, operational constraints, and approved continuity plans.

## 14. Contractual terms and approvals

This proposal is subject to:
- a completed and signed commercial licence agreement, where applicable;
- any statement of work, data-processing, security, or support schedule required for the engagement;
- procurement, budget, and legal approvals by both parties.

The definitive agreement must specify governing law, liability, warranties, indemnities, confidentiality, dispute resolution, taxes, termination, and other legal terms. This proposal does not override the definitive signed agreement.

## 15. Sign-off

**For the supplier / rights holder**

Name: [Name]  
Title: [Title]  
Signature: [Signature]  
Date: [Date]

**For the customer**

Name: [Name]  
Title: [Title]  
Signature: [Signature]  
Date: [Date]

---

## Appendix A — Customer-specific success measures

Select measures that can actually be observed in the engagement:

- [ ] Percentage of in-scope inventory records passing validation.
- [ ] Number of critical services with documented infrastructure dependencies.
- [ ] Number of modeled failure scenarios reviewed by service owners.
- [ ] Number of capacity assumptions identified as unknown or insufficient.
- [ ] Number of proposed resilience alternatives compared with a baseline.
- [ ] Number of recovery objectives confirmed by accountable service owners.
- [ ] Executive acceptance of the assessment and limitations register.

Do not use these measures to imply guaranteed outage reduction or operational certification.
