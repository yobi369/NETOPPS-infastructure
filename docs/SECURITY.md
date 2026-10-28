# Security Model

## Scope today

The current tool validates a local JSON file. It does not connect to devices, scan hosts, invoke shell commands, or modify infrastructure.

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
5. Pin and review third-party GitHub Actions before using them in sensitive release workflows.
6. Keep future device integrations read-only by default and enforce explicit allowlists.
7. Redact secrets from logs and error messages.
8. For write operations, require plan review, explicit operator approval, change-window awareness, timeout, post-change verification, and rollback instructions.

## Responsible use

Only inventory and administer systems you own or are explicitly authorized to manage. Any future active checks must document scope, rate limits, and operational impact.

## Known limitations

This is not a security certification, a penetration test, or an independent audit. The repository currently has no authentication layer because it does not expose a service. Reassess this model before adding APIs, shared dashboards, secrets, or device write access.
