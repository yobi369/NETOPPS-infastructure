# Security Model

## Scope today

The tool validates local JSON and creates subnet plans without network I/O. An optional connectivity command can open TCP connections only to management endpoints explicitly listed in the inventory, and only when the operator supplies `--allow-network`. It sends no application payload and never scans or discovers targets.

## Assets and risks

- Inventory files may reveal topology, hostnames, management addresses, and operational structure.
- Malformed input may cause incorrect conclusions if errors are ignored.
- Oversized, deeply nested, or overlap-heavy input could consume excessive resources if limits are absent.
- Future integrations could turn a local validation tool into a privileged control plane if boundaries are not explicit.

## Required controls

1. Never commit credentials, tokens, private keys, SNMP communities, or unredacted customer inventory.
2. Use synthetic/documentation IP ranges in examples.
3. Treat invalid input as failure; do not silently coerce or guess.
4. Keep CI permissions read-only unless a workflow has a reviewed, narrowly scoped reason otherwise.
5. Pin GitHub Actions to immutable upstream commit SHAs; update pins through reviewed pull requests and rerun CI. The workflow currently uses official GitHub actions only.
6. Keep network checks scoped to inventory-listed targets, opt-in, read-only, timeout-bounded, and concurrency-limited. Future device integrations must enforce explicit allowlists.
7. Redact secrets from logs and error messages.
8. For write operations, require plan review, explicit operator approval, change-window awareness, timeout, post-change verification, and rollback instructions.

## Data handling

The CLI reads inventory files locally and prints reports to standard output. It does not persist inventory or reports, upload files, or send telemetry. The opt-in connectivity command sends only TCP connection attempts to inventory-listed IP/port pairs and sends no application payload. Inventory and report files may reveal sensitive topology; operators are responsible for access control, retention, secure storage, and deletion of those files and any redirected output.

## Responsible use

Only inventory and administer systems you own or are explicitly authorized to manage. Any future active checks must document scope, rate limits, and operational impact.

## Known limitations

This is not a security certification, a penetration test, or an independent audit. The repository currently has no authentication layer because it does not expose a service. Reassess this model before adding APIs, shared dashboards, secrets, or device write access.
