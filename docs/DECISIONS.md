# Engineering Decision Records

## ADR-001: Start with a local, read-only validator

**Status:** Accepted

**Context:** Network automation can cause outages when inventory assumptions are wrong. The repository needs a useful, testable base before connecting to live systems.

**Decision:** Begin with a standard-library Python CLI that parses local JSON and checks inventory structure, management endpoints, and overlapping CIDRs. It does not perform network I/O.

**Consequences:** Easy to run on a laptop and in CI with no external services or credentials. It cannot report device reachability or live configuration state.

## ADR-002: Treat documentation as an operational contract

**Status:** Accepted

**Decision:** Every feature must document current behavior, safety boundaries, failure modes, and what has not been verified. Future roadmap items must not be described as implemented.

**Consequences:** The README and readiness claims stay aligned with executable behavior and test evidence.
