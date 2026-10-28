# Release Process

NETOPPS is currently an early `0.x` CLI. A release is scoped to the documented local inventory-validation and subnet-planning behavior unless a release note explicitly states otherwise.

## Before tagging

1. Confirm the release branch is clean and reviewed.
2. Run the full CI matrix on the exact candidate commit.
3. Confirm wheel build/install succeeds and the installed `netopps` command works in a clean environment.
4. Review the changelog and production-readiness gates.
5. Review dependency alerts, Bandit results, secret-scanning results, and outstanding security issues.
6. Confirm documentation matches executable behavior and no credentials or customer topology are included.
7. State limitations clearly; do not describe local validation as live monitoring or a network controller.

## Versioning

Use semantic-versioning conventions where practical:
- `0.x.y`: early development; interfaces may change.
- `1.0.0`: only after the supported CLI/schema contract and compatibility policy are established and the relevant production-readiness gates are evidenced.

## Release artifacts

Build a wheel from the reviewed tag and retain its checksum with release notes. Do not publish to a package index until the owner explicitly chooses the distribution target and confirms package naming and licensing.

## Rollback

For a CLI release, preserve the previous artifact and release notes. If a release is defective, mark it as superseded, publish a corrected version, and document migration or rollback instructions. Network configuration rollback is not applicable because this release has no device write capability.
