# Contributing to NETOPPS

Thanks for helping improve NETOPPS. The current scope includes local inventory validation, topology simulation, and institutional resilience analysis. The community edition is licensed under AGPL-3.0-or-later; see [LICENSE](LICENSE), [LICENSE-AGPL-3.0.txt](LICENSE-AGPL-3.0.txt), and [COMMERCIAL-LICENSING.md](COMMERCIAL-LICENSING.md).

## Contribution rights and CLA

Contributors retain copyright in their own contributions. To preserve the project's ability to distribute the same eligible code under both the AGPL community licence and separately negotiated commercial licences, an external contribution intended for the dual-licensed codebase must be accompanied by a completed [Contributor License Agreement](CONTRIBUTOR-LICENSE-AGREEMENT.md) accepted by the project rights holder before merge.

The CLA is a licence grant, not a copyright assignment. It gives the project rights holder permission to use, modify, distribute, and sublicense the contribution under community, commercial, and other terms while the contributor keeps ownership and may continue using and licensing their work. A pull request by itself does not grant these additional rights.

Do not submit code, documentation, designs, or assets unless you have the right to license them. If an employer, client, university, contractor, or another party may own or control the material, obtain written authorization before submission. Identify third-party components and their licences. Never submit confidential information, trade secrets, credentials, private keys, customer topology, or personal data.

A contribution without an accepted CLA must not be merged into the dual-licensed codebase on the assumption that it can be commercially relicensed. The maintainer may decline it or assess a separately documented route with legal review.

## Before opening a change

1. Explain the operational problem and expected behavior.
2. Keep examples synthetic; never commit production topology, credentials, tokens, or private keys.
3. Add tests for success, invalid input, boundary cases, and failure behavior.
4. Update the README and relevant operations/security/architecture documentation.
5. Keep device I/O and configuration changes out of the core package unless the feature has a reviewed threat model and simulator-first design.
6. Confirm the contribution's origin, third-party notices, and CLA status with the maintainer.

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
- [ ] Contribution origin and third-party rights are identified.
- [ ] Required CLA is signed, accepted, and recorded privately before merge.

Do not mark a feature production-ready solely because its unit tests pass. The CLA template must receive qualified legal review before it is used as a binding agreement.
