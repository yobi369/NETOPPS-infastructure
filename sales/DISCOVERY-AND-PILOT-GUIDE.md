# NETOPPS Institutional Discovery and Pilot Guide

Use this guide to qualify an opportunity before promising a deployment, integration, timeline, or price.

## 1. Qualification questions

### Business and service context
- Which services are considered critical, and who owns each one?
- What operational or continuity decision should this assessment support?
- What incidents, audit findings, planned changes, or procurement decisions prompted the enquiry?
- Which sites, departments, campuses, data centres, or service groups are in scope?

### Infrastructure and dependencies
- Is there an existing asset inventory, topology diagram, service catalogue, or dependency register?
- Are carrier, power, site, route, identity, DNS, cloud, and third-party dependencies recorded?
- Which capacity values are measured, contracted, estimated, or unknown?
- Are alternative providers and paths physically and logically independent? What evidence supports that claim?

### Recovery and governance
- Are service criticality levels approved by accountable owners?
- Are RTO and RPO targets documented and current?
- Who approves the model assumptions and final recommendations?
- What data classification, hosting, procurement, security, records, and audit requirements apply?

### Technical fit
- Can the customer run a local Python 3.11+ CLI in an approved environment?
- Can the customer provide sanitized JSON inputs or map existing exports into the documented schema?
- Is an offline HTML briefing sufficient for the initial decision?
- Does the customer expect live telemetry, centralized accounts, a dashboard, device configuration, or automated failover? If yes, these are not current capabilities and must be treated as separate future product requirements, not implied deliverables.

### Commercial fit
- Does the customer prefer AGPL-3.0-or-later or require a separately negotiated commercial agreement?
- Is source access, modification, embedding, redistribution, or affiliate access required?
- What is the procurement route, budget owner, approval timeline, and contract review process?
- Are implementation, training, support, and maintenance required?

## 2. Recommended first pilot

Start with a bounded, offline pilot:

- one business unit, campus, agency service group, or enterprise domain;
- a customer-approved set of critical services and supporting infrastructure;
- sanitized inventory and topology inputs;
- a small agreed set of node, link, site, and correlated failure scenarios;
- one baseline and one candidate dependency model;
- a review of declared capacity, redundancy, criticality, and recovery objectives;
- a final offline executive briefing and assumptions register.

The pilot should not require production credentials, broad scanning, live telemetry, or configuration changes.

## 3. Pilot success criteria

Agree criteria before data preparation. Possible measures:

- agreed in-scope assets and services represented in the model;
- input validation findings reviewed and dispositioned;
- critical dependencies and missing evidence recorded;
- selected failure scenarios reproducibly evaluated;
- baseline and candidate model differences explained;
- unknown or unsupported assumptions clearly identified;
- service owners and infrastructure reviewers accept the report as a planning input.

A pilot is successful when it produces a useful, reviewable decision artifact—not when it reports a favorable resilience score.

## 4. Evidence to request

Request only what is necessary and approved:

- sanitized inventory export;
- high-level topology or logical connectivity diagram;
- service-to-infrastructure dependency register;
- declared site, power, carrier, and route failure-domain labels;
- capacity values with source and confidence;
- approved service criticality, RTO, and RPO values;
- customer data classification and handling instructions.

Do not request passwords, private keys, SNMP communities, customer personal data, or raw production secrets.

## 5. Stop / re-scope conditions

Pause and re-scope if the customer requires:
- live network discovery or broad scanning;
- direct production configuration changes;
- automated failover or routing control;
- a hosted multi-tenant portal, SSO, or organization account management;
- real-time monitoring or central telemetry ingestion;
- a certification, guaranteed resilience score, or compliance attestation;
- a guaranteed SLA or support coverage not separately implemented and approved.

These capabilities are outside the current product boundary. Do not imply they are available.
