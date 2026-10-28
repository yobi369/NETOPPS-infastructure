# Changelog

All notable changes to NETOPPS are documented here. This project currently uses an early `0.x` version; interfaces may change before a stable release.

## Unreleased

### Added
- Local JSON inventory validation with deterministic findings and explicit exit codes.
- Duplicate device/network identifiers, duplicate hostnames and management IP checks.
- IPv4/IPv6 CIDR validation and bounded overlap reporting.
- Read-only IPv4/IPv6 subnet allocation planning.
- Input-size, UTF-8, duplicate JSON-key, and excessive-nesting safeguards.
- Versioned inventory JSON Schema, schema validation tests, and a versioned CLI output contract.
- Python package metadata and `netopps` console entry point.
- CI across Python 3.11, 3.12, and 3.13 with linting, static security analysis, coverage, schema checks, and wheel installation verification.
- Security, contributor, operations, architecture, roadmap, and production-readiness documentation.

### Limitations
- No live device adapters, active discovery, monitoring service, authentication service, persistent storage, or configuration write operations.
- No production deployment or external network lab validation has been completed.
- No license has been selected.
