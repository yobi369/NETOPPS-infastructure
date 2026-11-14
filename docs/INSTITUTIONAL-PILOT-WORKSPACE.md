# Institutional Pilot Workspace

The workspace is a local-first pilot case and evidence manifest, not a hosted customer portal. It records pilot identity, written authorization, approved environment, artifact references, evidence provenance, assessment history and SHA-256 integrity.

## Create and validate

```bash
netopps-pilot init --directory ./pilot-cases/telecom-evaluation --pilot-id telecom-eval-001 --institution "Example Institution" --title "Critical service resilience evaluation"
netopps-pilot validate --directory ./pilot-cases/telecom-evaluation
netopps-pilot package --directory ./pilot-cases/telecom-evaluation --output ./deliverables/telecom-evaluation.zip
```

Add institution-approved inputs and reports to the workspace. Declare each artifact in pilot-manifest.json with a unique ID, role, relative path and SHA-256 digest. Required baseline roles are baseline_topology and baseline_dependencies. Assessment records reference an assessment_report artifact and evidence IDs. The manifest is authoritative; the CSV evidence register is a reviewer-friendly companion.

## Supported artifact roles

- baseline_topology and baseline_dependencies: frozen reference inputs.
- candidate_topology and candidate_dependencies: proposed alternatives.
- assessment_report: output from the existing NETOPPS resilience engine.
- supporting_evidence: approved supporting material.

A hash mismatch is a stop condition. Do not silently refresh a baseline hash; preserve the original and create a separately versioned baseline or pilot revision. Packaging validates first and includes only the manifest, CSV register and explicitly declared artifacts. The ZIP must be written outside the workspace.

## Governance extension\n\nUse the separate [Pilot Governance and Trust](PILOT-GOVERNANCE-AND-TRUST.md) guide to register reviewer public keys, sign approvals, verify the audit chain, create baseline/candidate provenance and export a reproducible governance package. The trust registry is an institution-managed trust anchor; identity and delegated authority must be checked by the institution.\n\n## Security boundary

Keep the workspace on institution-approved access-controlled storage. Do not put credentials, subscriber data, personal data or unredacted production topology in public repositories or public forms. The workspace itself does not encrypt pilot files or provide user authentication, hosted role enforcement or immutable audit storage. The governance CLI encrypts private signing keys and supports Ed25519 signatures; signatures establish key possession and integrity, not real-world identity or authority. Hashes alone do not prove origin or time. Apply institutional encryption, transfer, retention and access controls. No hosted storage, tenant isolation, network integration, live monitoring or device configuration is provided.

The existing local engine remains responsible for analysis:
```bash
netopps resilience-report topology.json baseline-services.json --format json --output reports/baseline.json
netopps resilience-report topology.json baseline-services.json --candidate-dependencies candidate-services.json --format json --output reports/comparison.json
```
