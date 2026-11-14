# Pilot Governance, Signatures and Evidence Integrity

NETOPPS governance commands operate locally. Pilot data and private keys are not uploaded.

## 1. Cryptographic reviewer approvals

NETOPPS uses Ed25519 signatures over canonical UTF-8 JSON. Generate a reviewer keypair; the private key is encrypted with a passphrase and written with owner-only permissions on supported POSIX filesystems.

```bash
netopps-governance keygen --private-key ./trust/reviewer.private.pem --public-key ./pilot-cases/example/trust/reviewer.public.pem
netopps-governance register-reviewer --registry ./pilot-cases/example/trust/reviewers.json --public-key ./pilot-cases/example/trust/reviewer.public.pem --reviewer-id reviewer-001 --display-name "Authorized Reviewer" --organization "Example Institution" --role "Resilience Reviewer"
netopps-governance approve --directory ./pilot-cases/example --registry ./pilot-cases/example/trust/reviewers.json --private-key ./trust/reviewer.private.pem --assessment-id comparison-01 --decision approved --output ./pilot-cases/example/approvals/comparison-01.json
netopps-governance verify-approval --approval ./pilot-cases/example/approvals/comparison-01.json --registry ./pilot-cases/example/trust/reviewers.json --directory ./pilot-cases/example
```

An approval binds the pilot manifest digest, assessment ID and kind, decision, report artifact ID and digest, reviewer identity claims, key fingerprint and UTC signing time. Verification checks the signature against an active key in the supplied trust registry and optionally confirms the current manifest and report still match.

## 2. Reviewer identity and authority

The reviewer registry is a local trust anchor maintained by an institution-designated administrator. It binds a reviewer ID and declared name, organization and role to an Ed25519 public-key fingerprint and active/revoked status. The institution must verify identity and delegated authority before registering a key. Revocation is performed by controlled changes to the registry. Protect the registry and public keys with institutional access controls and backups.

A signature proves possession of the registered private key and integrity of signed bytes. It does not independently prove employment, legal identity, delegated authority or that the decision is correct. The registration command is not an identity-proofing service. Never commit private keys, passphrases or production trust material to Git.

## 3. Tamper-evident activity history

```bash
netopps-governance audit-append --directory ./pilot-cases/example --registry ./pilot-cases/example/trust/reviewers.json --private-key ./trust/reviewer.private.pem --event-type assessment.reviewed --details '{"assessment_id":"comparison-01","decision":"approved"}'
netopps-governance audit-verify --directory ./pilot-cases/example --registry ./pilot-cases/example/trust/reviewers.json
```

Each event includes a sequence number, previous-entry hash, actor identity, UTC timestamp, details, entry hash and Ed25519 signature. Verification detects altered, reordered or removed middle entries. A local chain alone cannot detect truncation of its final entries or replacement of the entire log. Independently retain each verified head hash or signed package in institution-controlled immutable/WORM storage and periodically compare against that external anchor. NETOPPS does not provide remote notarization or immutable storage.

## 4. Baseline-to-candidate provenance

```bash
netopps-governance provenance --directory ./pilot-cases/example --assessment-id comparison-01 --output ./pilot-cases/example/provenance/comparison-01.json
```

The provenance record links baseline and candidate topology/dependency artifact IDs, roles, paths and content hashes to the report hash, manifest digest and evidence IDs. Comparison assessments require both baseline and candidate topology and dependency artifacts. This records declared lineage; it does not independently validate source authenticity or input truth.

## 5. Reproducible evidence packages

```bash
netopps-governance package --directory ./pilot-cases/example --output ./deliverables/example-pilot.zip
sha256sum ./deliverables/example-pilot.zip
```

Packages include the manifest, evidence register, declared artifacts, approvals, provenance records, signed activity history and (when present in the pilot workspace) the explicit reviewer registry and its public keys. Private keys are never swept into packages. ZIP entry ordering, timestamps and permissions are normalized. Identical files under the same Python/zlib environment produce the same package digest. Different compression-library versions may produce different bytes.

## Security boundaries

- No hosted identity provider, SSO, MFA, certificate authority validation, identity proofing or automated authority delegation.
- The trust registry is an institution-managed trust anchor; protect it against unauthorized changes.
- The audit log is append-only by CLI convention, not filesystem-enforced immutable storage.
- Keep workspaces, private keys, registries and exported packages in institution-approved storage and transfer channels.
- Do not include confidential topology, subscriber/personal data or credentials unless explicitly approved for that destination.
