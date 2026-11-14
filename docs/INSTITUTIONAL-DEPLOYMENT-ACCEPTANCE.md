# Institutional Deployment and Security Acceptance

## Deployment model

NETOPPS pilot execution is local-first. Install the reviewed Python package in an institution-managed workstation, isolated VM or approved analysis environment. The public showcase is informational and must not receive confidential topology, service inventories, subscriber data, credentials, private keys or evidence packages.

## Minimum environment controls

- Institution-owned endpoint and approved OS/Python 3.11+ runtime.
- Named operator accounts, least privilege and MFA at the host/identity layer where available.
- Encrypted storage and institution-managed backup/retention.
- Private signing keys encrypted at rest, stored outside the pilot workspace and Git, with documented custody and recovery.
- Trust registry, approval policy and signed audit checkpoints stored under separate controlled access.
- Approved transfer channel for evidence packages; verify package digest at handoff and receipt.
- Egress restricted to approved update sources; no live network checks unless separately authorized and scoped.
- Dependency installation from reviewed, pinned release artifacts with vulnerability review.
- Documented incident contact, stop-work authority and rollback owner.

## Acceptance gates

| Gate | Evidence required | Pass condition |
|---|---|---|
| Authorization | Signed pilot charter and scope | Named sponsor and technical/data owners approve environment, data classes and scope |
| Platform | Host build record and package version/hash | Approved host, Python runtime and reviewed artifact |
| Identity and keys | Reviewer roster, key fingerprints, custody record | Identity and delegated authority independently verified; private keys protected |
| Governance | Policy file, test approvals and signed receipts | Rotation/revocation and distinct role-qualified approval checks pass |
| Audit | Signed checkpoint retained outside workspace | Independent verification succeeds after a controlled log-copy test |
| Evidence | Evidence register and package verification output | All declared artifact hashes and included signatures verify |
| Operations | Runbook, backup/restore and incident contacts | Operator can stop, preserve evidence and restore approved workspace |
| Closeout | Acceptance record and residual-risk register | Sponsor accepts findings, limitations and remediation ownership |

## Deployment sequence

1. Approve the pilot charter, data classification, environment and authorized operators.
2. Provision the analysis host and install the reviewed package in a virtual environment.
3. Generate reviewer keys; register public keys only after institutional identity and authority checks.
4. Create and approve a role policy; perform a rotation/revocation tabletop test.
5. Initialize the local pilot workspace and validate synthetic or authorized input artifacts.
6. Run baseline and candidate assessments; record evidence and assumptions.
7. Collect required signed approvals and verify the approval policy.
8. Verify the activity log, create a signed checkpoint and transfer it to independent controlled storage.
9. Build the evidence package; verify it locally and independently at the receiving endpoint.
10. Record acceptance, residual risks, retention schedule and rollback/closeout decision.

## Stop-work conditions

Stop analysis and preserve the current workspace if authorization is withdrawn, an artifact hash changes unexpectedly, a reviewer key is suspected compromised, trust registry integrity is uncertain, the audit checkpoint fails, evidence classification is exceeded, or the approved scope/environment changes. Do not silently regenerate baselines or replace a failed checkpoint.

## Rollback and recovery

Retain the last approved package, manifest, trust-registry snapshot, policy version and signed audit checkpoint. For a compromised key, revoke it through an authorized trust administrator, preserve the signed revocation receipt, register a replacement key after identity revalidation, and assess affected approvals from the compromise window. Restore only from institution-approved backups and re-verify hashes and signatures. Rollback applies to the pilot workspace and governance state; NETOPPS does not configure or roll back live network infrastructure.

## Formal sign-off

- Institutional sponsor: ____________________ Date: __________
- Technical owner: _________________________ Date: __________
- Information security reviewer: ____________ Date: __________
- Data owner: _____________________________ Date: __________
- NETOPPS pilot lead: ______________________ Date: __________

Acceptance is specific to the named environment, scope, package version and evidence set. It is not a carrier certification, security certification, service guarantee or proof of production-network resilience.
