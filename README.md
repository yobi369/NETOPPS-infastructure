# NETOPPS Infrastructure

**A safety-first network infrastructure and resilience analysis toolkit.**

NETOPPS is a practical NetOps engineering workspace for inventory validation, network-plan checks, operational runbooks, and carefully scoped connectivity checks. Its resilience-analysis workflow helps institutions model infrastructure dependencies, explore hypothetical disruption, and plan recovery. The first principle is simple: **inspect and validate before changing live infrastructure**.

> Status: production candidate for the documented local CLI scope. Authorized real-network lab acceptance remains required before relying on connectivity results operationally. NETOPPS is not a live network controller.

## Why this project

Network changes fail in expensive ways when inventory is inconsistent, addressing plans overlap, assumptions are undocumented, or automation has no safe rollback. NETOPPS aims to make those risks visible early, using small composable tools, machine-readable inputs, reproducible reports, and explicit operator approval.

## Design principles

- **Read-only by default:** no device configuration changes or network scans in the foundation tooling.
- **Fail closed:** malformed or ambiguous inventory is an error, not a guessed value.
- **Explainable checks:** every finding identifies the affected object and reason.
- **Portable and low-cost:** Python standard library for core validation; no paid services required.
- **Evidence over claims:** CI results and actual test coverage determine readiness statements.
- **Human-controlled change:** future write-capable actions require dry-run plans, explicit approval, timeouts, and rollback strategy.
- **Small composable tools:** useful CLI primitives before a sprawling dashboard.

## Current capabilities

- Validate JSON infrastructure inventory structure.
- Generate deterministic, read-only subnet allocation plans from a specified IPv4 or IPv6 pool.
- Perform opt-in TCP reachability checks only against management endpoints already listed in inventory, with bounded concurrency and per-connection timeouts.
- Check IPv4/IPv6 CIDR syntax and detect overlapping networks.
- Detect duplicate device identifiers, DNS hostname syntax and duplicates, duplicate management IP addresses, invalid roles, and invalid management ports.
- Reject ambiguous duplicate JSON keys, malformed UTF-8, excessively nested JSON, and input files larger than 5 MiB. Inventory sizes and overlap findings are also bounded.
- Produce deterministic machine-readable findings with documented exit codes.
- Exercise CLI and validator behavior with automated tests.

## Quick start

Requires Python 3.11 or newer. Install the CLI from the repository root:

```bash
python -m pip install .
# Local institutional pilot case/evidence workspace
netopps-pilot --help
```

Then run:

```bash
python -m netopps validate examples/inventory.json
netopps plan-subnets examples/inventory.json --pool 10.20.0.0/16 --prefix 24 --count 4
# Only run on networks you are authorized to check; this opens TCP connections.
netopps check-connectivity examples/inventory.json --allow-network --limit 20 --timeout 1.0
netopps topology-report examples/topology.json --path-from core-router --path-to app-server
netopps topology-report examples/topology.json --disable-link core-to-a
netopps topology-report examples/topology.json --traffic-file examples/traffic-demands.json
netopps topology-risk examples/topology.json
netopps topology-diff examples/topology.json examples/topology-candidate.json
netopps topology-scenarios examples/multi-site-topology.json examples/failure-scenarios.json
netopps topology-scenarios examples/multi-site-topology.json examples/failure-scenarios.json --dependency-file examples/service-dependencies.json
netopps resilience-report examples/multi-site-topology.json examples/service-dependencies.json
# Compare a proposed dependency design against the baseline
netopps resilience-report examples/multi-site-topology.json examples/service-dependencies.json --candidate-dependencies examples/service-dependencies-candidate.json
# Export a self-contained executive HTML briefing
netopps resilience-report examples/multi-site-topology.json examples/service-dependencies.json --format html --output resilience-briefing.html
```

Exit codes: `0` means the requested checks passed; `1` means inventory findings, an incomplete subnet plan, an unreachable endpoint, or a truncated connectivity scope; `2` means input/arguments could not be safely processed.

To validate your own inventory, copy `examples/inventory.json` and update it with non-sensitive lab data. Do not commit credentials, private keys, SNMP communities, or real production topology details.

## Institutional pilot workspace

Create a local evidence-linked pilot case with `netopps-pilot init`, validate artifact hashes and evidence references with `netopps-pilot validate`, and create a reproducibility package with `netopps-pilot package`. See [Institutional Pilot Workspace](docs/INSTITUTIONAL-PILOT-WORKSPACE.md). The workspace is local-only and does not provide hosted storage, encryption, authentication, role enforcement or tamper-proof audit logging.

## Telecom evaluation demonstration

A guided, browser-based telecom scenario is available at the [NETOPPS interactive demo](https://netopps.vercel.app/demo/). It lets visitors select synthetic failures and compare baseline versus candidate redundancy. This is an explanatory front-end illustration, separate from the local analysis engine; it is not a live calculation from operator data. The reproducible CLI workflow and synthetic input files are documented in the [Telecom Evaluation Demo](docs/TELECOM-EVALUATION-DEMO.md). Neither the browser scenario nor the example files represent Safaricom or any other operator's actual network.

## Inspect actual engine output\n\nGenerate a machine-readable resilience report with `netopps resilience-report … --format json --output report.json`, then open the [NETOPPS Engine Report Viewer](https://netopps.vercel.app/analysis/) and select the file. The viewer reads it locally; it does not upload report data. See [Engine Report Viewer](docs/ENGINE-REPORT-VIEWER.md). This is separate from the illustrative [guided browser demo](https://netopps.vercel.app/demo/).\n\n## Inventory contract

The versioned interchange schema is in [schemas/inventory.schema.json](schemas/inventory.schema.json). The schema defines the data shape; the Python validator additionally checks semantic conditions such as overlapping networks and duplicate management addresses.

## Repository map

- `netopps/` — inventory validation, subnet planning, opt-in connectivity checks, topology simulation, institutional resilience planning, and CLI.
- `tests/` — validator and CLI regression tests.
- `examples/` — safe, synthetic inventory, topology, service dependency, and telecom evaluation data.
- `schemas/` — versioned inventory schema.
- `docs/ARCHITECTURE.md` — boundaries and extension points.
- `docs/NETWORK-DIGITAL-TWIN.md` — simulation model, examples, limitations, and research path.
- `docs/TRAFFIC-SIMULATION.md` — traffic demand assumptions and congestion estimates.
- `docs/TOPOLOGY-RISK.md` — topology diff semantics and explainable risk scoring.
- `docs/SCENARIO-PACKS.md` — repeatable node, link, and site outage scenarios.
- `docs/RESILIENCE-PLANNING.md` — ranked institutional resilience options, capacity assessment, and recovery priorities.
- `docs/TELECOM-EVALUATION-DEMO.md` — synthetic telecom demonstration, evaluation workflow, and pilot acceptance gates.
- `docs/COMMERCIAL-VALUE-MEASUREMENT.md` — evidence-led pilot scorecard and commercial-value measurement method.
- `docs/SECURITY.md` — threat model and safe-use rules.
- `docs/OPERATIONS.md` — repeatable local workflow and incident discipline.
- `docs/ROADMAP.md` — staged delivery with verifiable acceptance criteria.
- `docs/PRODUCTION-READINESS.md` — release gates and current gaps.
- `docs/RELEASE.md` — controlled release and rollback process.
- `docs/SCHEMA-COMPATIBILITY.md` — schema versioning and migration rules.
- `docs/OUTPUT-SCHEMA.md` — versioned CLI JSON response contract.
- `docs/LAB-ACCEPTANCE.md` — authorized lab acceptance checklist before operational reliance.
- `CHANGELOG.md` — implemented changes and limitations.
- `docs/DECISIONS.md` — engineering decision records.
- `COMMERCIAL-LICENSING.md` — community and commercial licensing paths.
- `CONTRIBUTOR-LICENSE-AGREEMENT.md` — draft contributor rights agreement.
- `docs/COMMERCIAL-LICENSE-AGREEMENT-TEMPLATE.md` — draft institutional commercial agreement.
- `docs/COMMERCIAL-READINESS-CHECKLIST.md` — ownership, release, and customer-contract readiness gates.
- `sales/` — institutional product overview, licensing options, proposal template, and discovery/pilot guide.

## Network digital twin (simulation-only)

NETOPPS includes a deterministic graph model for operator-supplied topology scenarios. It can summarize connectivity components, identify isolated nodes, calculate lowest-latency paths, simulate hypothetical node or link failures, estimate traffic demand against declared link capacity, compare baseline and candidate topologies, and produce explainable structural-fragility scores. Optional service dependency graphs add recursive failure paths, service-state classification, and institution-level impact ranking from operator-supplied metadata. The `resilience-report` command ranks single-dependency failure domains, proposes conditional redundancy improvements, reports capacity shortfalls under modeled failures, and orders recovery priorities by declared service criticality and optional RTO/RPO objectives. It also simulates correlated failures from shared failure-domain labels and audits operator-supplied physical-diversity evidence metadata. It flags shared failure domains but does not authenticate evidence or certify physical independence. The CLI can export a self-contained, offline HTML executive briefing. The model is local-only and does not discover devices, collect telemetry, open sockets, or change infrastructure. Declared latency and capacity are scenario inputs, not live measurements. See [Network Digital Twin](docs/NETWORK-DIGITAL-TWIN.md), [Traffic Simulation](docs/TRAFFIC-SIMULATION.md), [Resilience Planning](docs/RESILIENCE-PLANNING.md), and the [Telecom Evaluation Demo](docs/TELECOM-EVALUATION-DEMO.md).

## Safety boundaries

Inventory validation and subnet planning parse local JSON and do not open network connections. The optional `check-connectivity` command opens TCP connections only to management endpoints listed in the supplied inventory and only when `--allow-network` is present; it sends no application payload and performs no discovery or configuration changes. Do not use it on networks you do not own or have explicit permission to assess. Any future discovery or configuration feature must be opt-in, scoped, rate-limited, auditable, and documented before implementation.

## Development and CI

```bash
python -m pip install -e ".[test]"
python -m compileall -q netopps tests
ruff check netopps tests
bandit -q -r netopps
detect-secrets scan --all-files --exclude-files '(^|/)(\.git|\.ruff_cache|htmlcov|dist|build)/'
pip-audit --skip-editable
coverage run --branch --source=netopps -m unittest discover -s tests -v
coverage report --fail-under=80
python -m json.tool schemas/inventory.schema.json > /dev/null
python -m netopps validate examples/inventory.json
```

GitHub Actions runs these checks on Python 3.11, 3.12, and 3.13. A successful run verifies the CLI, mocked connectivity cases, and local loopback TCP behavior; it does not verify customer devices, a production network, or a hosted deployment.

## Contribution quality bar

Every feature should include tests, a clear failure mode, updated documentation, and an explicit statement of whether it is simulated, local-only, or verified against real infrastructure. Avoid committing secrets or claiming operational readiness without evidence.

## Licensing

NETOPPS uses a dual-licensing model for the current codebase:

- **Community edition:** GNU Affero General Public License v3.0 or later ([full text](LICENSE-AGPL-3.0.txt)). If you modify and operate a covered version for users over a network, AGPL section 13 generally requires offering those users the corresponding source code.
- **Commercial edition:** A separate commercial license is available from the copyright holder under a written agreement. See [Commercial Licensing](COMMERCIAL-LICENSING.md) for the scope and enquiry route. No commercial license is granted by this repository itself.

**Historical MIT grants:** Earlier versions and copies already distributed under MIT remain governed by that license; this change does not revoke permissions already granted. The original MIT text is preserved in [LICENSE-MIT-LEGACY](LICENSE-MIT-LEGACY).

The dual-licensing offer applies only to material for which the copyright holder has the necessary rights. External contributions require an accepted Contributor License Agreement before merge into the dual-licensed codebase; contributors retain ownership while granting the rights described in that agreement. Third-party components remain subject to their own rights and license terms. Commercial agreement templates are drafts only and do not grant rights until completed and signed. Operators remain responsible for authorization and safe use of any network or device.


## Institutional Pilot Edition

The `pilot/` directory contains the controlled evaluation package: a pilot charter, evidence register, acceptance checklist and local execution guide. It defines a six-stage workflow from authorization and onboarding through structured inventory, evidence review, baseline analysis, candidate improvement and executive comparison. The pilot uses the existing local Python engine and keeps customer data under the institution's approved control. It does not introduce hosted workspaces, data uploads, authentication, multi-tenant storage or live network integration. Start with [pilot/README.md](pilot/README.md), complete the [pilot charter](pilot/PILOT-CHARTER.md), and maintain the [evidence register](pilot/EVIDENCE-REGISTER.csv) before running an assessment.
