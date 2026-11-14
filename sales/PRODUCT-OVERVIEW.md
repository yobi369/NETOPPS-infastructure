# NETOPPS Infrastructure — Institutional Product Overview

**A safety-first toolkit for infrastructure validation, network planning, and institutional resilience analysis.**

NETOPPS helps infrastructure teams examine the quality of network inventories, model dependencies between critical services and supporting infrastructure, explore failure scenarios, and prepare evidence-led resilience discussions. It is designed around local execution, explicit operator inputs, deterministic reports, and human-controlled decisions.

## The institutional problem

Critical services often depend on infrastructure spread across sites, carriers, power domains, links, identity platforms, and internal teams. Planning becomes difficult when:

- asset inventories and addressing plans are inconsistent;
- dependencies are documented informally or not at all;
- a proposed redundant path may share the same upstream failure domain;
- service criticality and recovery objectives are not reflected in network planning;
- resilience proposals cannot be compared using a repeatable baseline;
- decision-makers receive technical diagrams but lack a concise, explainable impact summary.

NETOPPS provides a structured way to model these assumptions and examine their implications before a change is approved.

## What NETOPPS does today

### 1. Inventory quality and network planning
- Validates structured infrastructure inventory data.
- Checks identifiers, hostnames, management addresses, roles, ports, CIDR syntax, and overlapping networks.
- Produces deterministic subnet allocation plans from an operator-specified address pool.
- Supports opt-in TCP reachability checks only for management endpoints already listed in the inventory, with bounded concurrency and timeouts.

### 2. Topology and traffic simulation
- Models nodes, links, sites, and declared link attributes.
- Evaluates paths, connectivity components, isolated nodes, and structural fragility.
- Compares baseline and candidate topologies.
- Simulates node, link, and site failure scenarios.
- Models declared traffic demands and capacity constraints; these are scenario estimates, not measured traffic.

### 3. Institutional service dependency analysis
- Represents dependencies between services and supporting infrastructure.
- Models required and optional dependencies, cascading failures, and alternative members in explicitly declared redundancy groups.
- Applies operator-declared service criticality and dependency weights to prioritize impact.
- Traces direct and transitive failure paths and summarizes impacts by institution.
- Evaluates declared failover capacity and flags capacity gaps where sufficient input data exists.

### 4. Resilience and recovery planning
- Runs single and correlated failure scenarios using declared failure-domain labels.
- Identifies weak dependencies and conditional redundancy opportunities.
- Compares baseline and candidate dependency models.
- Surfaces institution-defined RTO/RPO objectives in recovery priority ordering.
- Produces JSON output and a self-contained offline HTML executive briefing.

## Institutional outcomes

NETOPPS can support teams to:

- create a more consistent, reviewable infrastructure inventory;
- expose hidden or poorly documented service dependencies;
- prioritize resilience work using declared criticality and dependency weights;
- test proposed redundancy arrangements against modeled failure scenarios;
- identify capacity assumptions that need validation;
- compare a baseline with a proposed design before procurement or implementation;
- communicate technical findings to risk, continuity, procurement, and executive stakeholders.

These are decision-support outcomes, not guarantees of avoided outages, financial savings, regulatory compliance, or service availability.

## Sector applications

### Government agencies and public institutions
Potential use: model dependencies behind citizen-facing or internal digital services, identify shared infrastructure risks across departments or sites, compare continuity options, and prepare an evidence-based resilience briefing.

A suitable initial engagement is a bounded assessment of one authorized service portfolio or a synthetic/lab topology. Government procurement, data classification, hosting, security accreditation, and records requirements must be assessed independently.

### Universities and education networks
Potential use: examine dependencies supporting learning platforms, student information systems, identity services, campus connectivity, research computing, library systems, and multi-campus links.

A pilot can model a small set of critical services and compare proposed campus or provider redundancy. Student or staff personal data is not required for the topology model; use asset identifiers and synthetic labels where possible.

### Telecom operators and internet service providers
Potential use: analyze modeled transport and service dependencies, examine declared carrier/site/power failure domains, prioritize services, and compare capacity assumptions for resilience planning.

NETOPPS is not a carrier-grade network management system, OSS/BSS, NMS, telemetry collector, routing controller, or live traffic engineering platform. Any operator deployment requires a validated data export, authorized lab evaluation, and integration engineering before operational reliance.

### Enterprise infrastructure teams
Potential use: model dependencies across data centres, offices, cloud/on-premises services, identity, WAN, internet circuits, and critical business applications; compare proposed redundancy and recovery priorities.

Start with an offline assessment using a sanitized inventory and explicitly declared service objectives.

## Deployment and data handling

The current product is a local Python CLI. The resilience model operates on files supplied by the operator and produces local JSON or offline HTML output. The tool does not upload topology files to a NETOPPS service, and the resilience simulation itself performs no network I/O.

The separate connectivity-check command is opt-in and opens bounded TCP connections only to management endpoints already listed in an inventory, when the operator supplies the explicit network permission flag. It does not perform broad discovery or configuration changes.

Customer data remains under the customer's control in the current local workflow. Customers should sanitize exports, restrict filesystem access, and avoid placing credentials, private keys, personal data, or sensitive production topology in public repositories or issue trackers.

## Deployment requirements

- Python 3.11 or newer.
- A supported operating environment capable of running Python.
- Customer-prepared inventory, topology, service-dependency, and scenario JSON files following the documented schemas/examples.
- An operator or analyst familiar with the environment and able to validate source data.
- Written authorization for any connectivity checks against real systems.

The current release does not include hosted multi-tenant access control, centralized identity, a web dashboard, centralized telemetry ingestion, a managed service, or a guaranteed SLA.

## Evaluation approach

A responsible evaluation should proceed through:

1. **Discovery:** identify services, sites, owners, data classification, and decision questions.
2. **Data preparation:** produce sanitized, operator-approved inventory and dependency inputs.
3. **Baseline:** run validation and resilience analysis; review assumptions and missing evidence.
4. **Candidate:** model one or more proposed changes without changing production systems.
5. **Review:** compare results with network diagrams, supplier evidence, lab tests, and recovery plans.
6. **Decision:** produce a documented set of recommendations, uncertainties, and next validation steps.

## Evidence and limitations

NETOPPS is deterministic given the same inputs, but deterministic output does not make input assumptions true. Capacity, traffic, criticality, failure domains, physical diversity, and RTO/RPO are supplied by operators. NETOPPS does not authenticate physical-diversity evidence or certify that separate providers, sites, conduits, power feeds, DNS, identity, or control planes are independent.

The product does not calculate outage probabilities, financial loss, regulatory compliance, measured restoration performance, or guaranteed service-level outcomes. Proposed redundancy only reduces modeled impact if the alternative is genuinely independent, compatible, adequately sized, and operationally tested.

## Licensing

The community edition is available under AGPL-3.0-or-later. A separate commercial licence may be negotiated for organizations that require different terms, subject to verification of rights and a signed agreement. See [Licensing Options](LICENSING-OPTIONS.md). No pricing or commercial rights are created by this overview.
