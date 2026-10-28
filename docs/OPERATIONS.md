# Operations Guide

## Local validation

Use Python 3.11+.

```bash
python -m unittest discover -s tests -v
python -m netopps validate examples/inventory.json
```

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
- `device.management_ip`: use a literal IPv4 or IPv6 address, not a hostname.
- `network.cidr`: use a canonical network address and prefix, for example `192.0.2.0/24`.
- `network.overlap`: review whether overlapping ranges are intentional; this validator reports overlap but cannot infer business intent.

## Incident/change discipline

Before future automation is allowed to change a device, require a reviewed plan, named approver, scope, pre-change snapshot where supported, timeout, post-change checks, and documented rollback. Do not apply generated configuration directly to production from an unreviewed CI job.
