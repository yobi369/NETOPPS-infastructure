# Telecom Infrastructure Resilience Evaluation — Demonstration

## Purpose

This walkthrough presents NETOPPS against a synthetic telecommunications environment. It is designed for a technical evaluation conversation with a telecom operator. It is not a representation of Safaricom's architecture, live network data, or a claim that NETOPPS has been tested inside a carrier network.

The demonstration answers four questions:

1. Which modeled services depend on each infrastructure component?
2. What happens to those services when a selected site or core component fails?
3. Does a proposed alternate dependency change the modeled service impact?
4. Are the declared capacity and failure-domain assumptions sufficient to support the proposed resilience claim?

## Guided browser walkthrough

A separate, static browser demonstration is published at [https://netopps.vercel.app/demo/](https://netopps.vercel.app/demo/). It lets a visitor select one of four synthetic failure scenarios and compare the illustrative baseline and candidate dependency designs. The browser page uses its own small, explicit example model; it is not wired to the Python engine, does not load the JSON files below, and must not be presented as a live NETOPPS calculation. Its purpose is to make the product's resilience questions understandable in a first meeting.

## Files

- `examples/telecom-evaluation-topology.json` — synthetic two-site network topology.
- `examples/telecom-evaluation-services.json` — baseline services with a single declared dependency path.
- `examples/telecom-evaluation-services-candidate.json` — candidate service model with an alternate dependency at a second synthetic site.

All names, sites, capacities, service priorities, recovery objectives and failure-domain labels are illustrative inputs. They are not operator measurements or Safaricom facts.

## Run the demonstration

Install NETOPPS from the repository root:

```bash
python -m pip install .
```

Generate the baseline assessment:

```bash
netopps resilience-report examples/telecom-evaluation-topology.json examples/telecom-evaluation-services.json --format html --output telecom-baseline-briefing.html
```

Generate the candidate assessment and compare it with the baseline dependency design:

```bash
netopps resilience-report examples/telecom-evaluation-topology.json examples/telecom-evaluation-services.json --candidate-dependencies examples/telecom-evaluation-services-candidate.json --format html --output telecom-candidate-comparison.html
```

Run a structural topology report for a selected path:

```bash
netopps topology-report examples/telecom-evaluation-topology.json --path-from mobile-core-east --path-to mobile-money-api
```

The HTML briefings are self-contained and offline. Review the executive assessment, weakest dependencies, conditional redundancy recommendations, correlated failure scenarios, capacity assessment and recovery priorities.

## Suggested evaluation session

### 1. Agree the service boundary

Select a small set of representative service classes with the operator. For example, a packet-data service, voice/signalling service and a digital transaction API can be used as abstract categories. Do not request sensitive production topology or credentials for an initial demonstration.

### 2. Review the baseline model

Explain how each service is linked to the infrastructure assets it requires. Confirm the declared criticality, dependency weights, required capacity and RTO/RPO objectives with the operator's subject-matter experts.

### 3. Run failure scenarios

Review the model's single-asset and shared-failure-domain analysis. Ask the operator to challenge missing dependencies, shared power or transport assumptions, and unrealistic capacity declarations.

### 4. Compare a candidate design

Review the candidate dependency file. The second-site dependency is a hypothesis, not proof of physical independence or a validated failover route. A real evaluation must establish that the alternate is technically reachable, independently powered and routed, appropriately secured, and has sufficient tested capacity.

### 5. Capture evidence and decisions

Record which findings the operator accepts, rejects or needs to validate. Identify data gaps, proposed engineering actions, responsible owners and the evidence required before any change is approved.

## What this demonstration proves — and does not prove

The local CLI workflow demonstrates that the current NETOPPS engine can process an operator-supplied topology and service model, simulate selected failures, rank modeled service impacts, inspect declared redundancy and capacity, and compare baseline and candidate dependency documents. The browser walkthrough is a separate illustrative experience and does not execute the engine.

It does not demonstrate live telemetry, real-time network visibility, subscriber-level impact, packet-level simulation, routing-protocol convergence, automated failover, device configuration, carrier-grade scale, integration with OSS/BSS, or performance on a production operator network.

All outputs are deterministic planning analysis from supplied inputs. They are not outage probabilities, financial loss estimates, SLA measurements, security certification or guarantees of restoration performance.

## Acceptance gates for a real telecom pilot

Before relying on results, the operator and NETOPPS team should agree on:

- A bounded, authorised and non-sensitive data extract or operator-reviewed model.
- Asset and service identity mapping, including ownership of source data.
- Explicit topology, power, transport, provider and facility failure domains.
- Capacity units, measurement windows, busy-hour assumptions and evidence sources.
- Service criticality, dependency semantics and approved recovery objectives.
- A representative set of failure scenarios and expected outcomes.
- Independent review by operator engineers.
- A documented comparison against the operator's existing analysis process.
- Security, privacy, data residency, retention and deletion requirements.
- A rollback and exit plan for any later integration work.

No production access or live network connection is required for this offline demonstration.
