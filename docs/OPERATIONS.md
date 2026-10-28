# Operations Guide

## Local validation

Use Python 3.11+.

```bash
python -m unittest discover -s tests -v
python -m netopps validate examples/inventory.json
python -m netopps plan-subnets examples/inventory.json --pool 10.20.0.0/16 --prefix 24 --count 4
# Requires explicit consent and only checks inventory-listed management endpoints.
python -m netopps check-connectivity examples/inventory.json --allow-network --limit 20 --timeout 1.0
```

See [CLI Output Contract](OUTPUT-SCHEMA.md) for the versioned JSON response shapes and compatibility rules.

## Exit codes

- `0`: inventory passed all implemented checks.
- `1`: inventory was parsed but failed validation.
- `2`: input file could not be read or was not valid JSON.

## Safe workflow

1. Make a copy of the sample inventory.
2. Use synthetic or appropriately protected data.
3. Run validation before proposing any network change.
4. Review every finding; a clean validation only means the implemented checks passed.
5. Store the output with a change ticket if it supports an operational decision.
6. Do not treat this tool as a reachability, configuration-compliance, or live-health monitor.

## Troubleshooting

- `inventory.schema_version`: set the supported schema version to integer `1`.
- `device.hostname`: use an ASCII DNS hostname with valid labels (letters/digits at the ends, letters/digits/hyphens inside); a single trailing root dot is accepted.
- `device.management_ip`: use a literal IPv4 or IPv6 address, not a hostname.
- `network.cidr`: use a canonical network address and prefix, for example `192.0.2.0/24`.
- `network.overlap`: review whether overlapping ranges are intentional; this validator reports overlap but cannot infer business intent.

## Incident/change discipline

Before future automation is allowed to change a device, require a reviewed plan, named approver, scope, pre-change snapshot where supported, timeout, post-change checks, and documented rollback. Do not apply generated configuration directly to production from an unreviewed CI job.

## Subnet allocation planning

`plan-subnets` is a dry-run planner. It reads the inventory, refuses to proceed when the inventory has validation findings, and returns the first available CIDRs in deterministic order. It does not reserve or apply addresses anywhere.

```bash
netopps plan-subnets examples/inventory.json --pool 10.20.0.0/16 --prefix 24 --count 4
```

- `--pool`: parent network in CIDR notation.
- `--prefix`: desired subnet prefix; it must be at least as specific as the parent pool.
- `--count`: requested number of subnets, from 1 to 256.
- Output includes `mode: plan-only` and `applied: false`.
- The planner refuses pools with more than one million candidate subnets to avoid unbounded work.
- A partial result returns exit code 1 and `complete: false`; invalid arguments return exit code 2.

Review every plan against organizational reservations, routing design, DHCP scopes, and change records before using it operationally.

## Read-only connectivity checks

`check-connectivity` opens a TCP connection to the management IP and port for each selected inventory device, sends no application payload, and closes the connection. It is not a port scanner and never discovers targets. The command refuses to run unless `--allow-network` is supplied explicitly.

- `--limit` is 1–100 devices (default 20); the report indicates if the inventory scope was truncated.
- `--timeout` is 0.1–3.0 seconds per connection (default 1.0).
- Concurrency is capped at eight connections.
- Only run it against infrastructure you own or are authorized to assess. A TCP handshake confirms reachability of that port at that moment; it does not establish application health, authentication success, or correct device configuration.
- Tests mock sockets and never connect to external infrastructure.
