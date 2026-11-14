# Institutional Security and Deployment Readiness

This milestone adds local trust administration and independent verification primitives. It does not turn NETOPPS into a hosted identity or customer-management platform.

## Reviewer key lifecycle

Generate replacement keys with `netopps-governance keygen`, store the encrypted private key outside the pilot workspace, and place the public key under the institution-controlled `trust/` directory. Trust changes require an active reviewer whose registered role is `Trust Administrator` or `Security Administrator`.

Rotation example (the replacement public key must already exist beneath the trust directory):

```bash
netopps-security rotate-reviewer \
  --registry ./pilot-cases/example/trust/reviewers.json \
  --old-fingerprint OLD_SHA256_FINGERPRINT \
  --new-public-key ./pilot-cases/example/trust/reviewer-next.public.pem \
  --reviewer-id reviewer-002 --display-name "Reviewer Two" \
  --organization "Example Institution" --role "Resilience Reviewer" \
  --admin-private-key ./secure/trust-admin.private.pem \
  --receipt ./pilot-cases/example/trust/changes/rotation.json
```

Revocation marks the key inactive in the local trust registry and writes an administrator-signed receipt. Preserve the prior registry and receipts in institution-controlled versioned storage. Historical signatures remain cryptographically verifiable after revocation while the corresponding public key and trust record are retained. Revocation prevents new approvals because signing requires an active key; it does not invalidate earlier signed bytes. The local trust registry is not an online certificate authority. Reviewers and auditors must separately establish whether the key was valid at the historical signing time from retained trust-change records.

## Signed audit-head checkpoints

After verifying the activity chain, create a signed checkpoint and store it separately from the pilot workspace (ideally in institution-controlled immutable/WORM storage):

```bash
netopps-security checkpoint --directory ./pilot-cases/example \
  --registry ./pilot-cases/example/trust/reviewers.json \
  --private-key ./secure/audit-reviewer.private.pem \
  --output /institutional-archive/netopps/pilot-audit-head.json
netopps-security verify-checkpoint --directory ./pilot-cases/example \
  --registry ./pilot-cases/example/trust/reviewers.json \
  --checkpoint /institutional-archive/netopps/pilot-audit-head.json
```

A checkpoint binds pilot ID, event count and chain head to an Ed25519 signer. A separately retained checkpoint detects later truncation or replacement relative to that anchor. It does not prevent an attacker from changing both the log and the checkpoint if they control both storage locations.

## Role-based, multi-reviewer approval

Create a policy JSON file, maintained through institutional change control:

```json
{
  "required_approvals": 2,
  "allowed_roles": ["Resilience Reviewer", "Security Reviewer"]
}
```

Then verify distinct, active, role-qualified approvals:

```bash
netopps-security verify-policy --directory ./pilot-cases/example \
  --registry ./pilot-cases/example/trust/reviewers.json \
  --policy ./pilot-cases/example/policies/assessment-approval.json \
  --approvals ./pilot-cases/example/approvals/reviewer-a.json \
              ./pilot-cases/example/approvals/reviewer-b.json
```

Each approval is individually signed and bound to the manifest and report digest. Policy verification enforces the configured count, allowed roles and distinct reviewer IDs. It is a verification command, not a hosted authorization gateway: institutions must enforce policy before accepting a decision or releasing a report.

## External evidence-package verification

An external auditor can verify a ZIP without extracting it:

```bash
netopps-security verify-package --package ./deliverables/example-pilot.zip
```

The verifier checks archive path safety and duplicate names, declared artifact hashes, packaged reviewer public-key fingerprints, approval signatures, manifest digests and assessment report digests. It does not certify the truth or completeness of source evidence, independently validate reviewer identity, prove a signing time, or replace institutional audit procedures.

## Deployment and security acceptance

See [INSTITUTIONAL-DEPLOYMENT-ACCEPTANCE.md](INSTITUTIONAL-DEPLOYMENT-ACCEPTANCE.md) for environment controls, acceptance gates, responsibilities, rollback, and sign-off.

## Security boundaries

- No hosted tenants, SSO, MFA, identity proofing, remote key escrow, online revocation service or central audit service.
- Trust registry updates and policy files require institution-controlled access control, change approval, backup and retention.
- Keep encrypted private keys outside Git and evidence packages; restrict access and maintain offline recovery procedures.
- Signatures prove possession of a registered key and integrity of signed bytes, not legal identity, authority, correctness or trusted time.
- A checkpoint is useful only when its signed copy is retained independently of the workspace.
- Use only institution-approved systems and synthetic or explicitly authorized data. The public showcase is not an intake portal.
