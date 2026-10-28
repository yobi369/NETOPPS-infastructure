# Contributing to NETOPPS

Thanks for helping improve NETOPPS. The current scope is a local-only inventory validator and dry-run subnet planner.

## Before opening a change

1. Explain the operational problem and the expected behavior.
2. Keep all examples synthetic; never commit production topology, credentials, tokens, or private keys.
3. Add tests for success, invalid input, boundary cases, and failure behavior.
4. Update the README and relevant operations/security/architecture documentation.
5. Keep device I/O and configuration changes out of the core package unless the feature has a reviewed threat model and simulator-first design.

## Local checks

Use Python 3.11 or newer:

```bash
python -m pip install -e ".[test]"
ruff check netopps tests
bandit -q -r netopps
detect-secrets scan --all-files
pip-audit --skip-editable
coverage run --branch --source=netopps -m unittest discover -s tests -v
coverage report --fail-under=80
python -m json.tool schemas/inventory.schema.json > /dev/null
python -m netopps validate examples/inventory.json
```

## Pull request checklist

- [ ] Behavior and limitations are described.
- [ ] Tests cover normal and failure paths.
- [ ] CI checks pass on all supported Python versions.
- [ ] No secrets or sensitive inventory data are included.
- [ ] Documentation matches implemented behavior.
- [ ] Any network access is explicitly scoped, time-bounded, and opt-in.
- [ ] Any write-capable behavior has a separate approval path and rollback plan.

Do not mark a feature production-ready solely because its unit tests pass.
