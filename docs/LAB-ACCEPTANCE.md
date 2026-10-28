# Authorized Network Lab Acceptance

Use this checklist before relying on NETOPPS connectivity results for operational decisions. This is an operator-run acceptance procedure; CI does not contact external or production devices.

## Safety preconditions

- [ ] Obtain written authorization for the target devices and test window.
- [ ] Use a non-production lab where possible.
- [ ] Select only devices already listed in the inventory file.
- [ ] Confirm the management IPs and ports are correct and the test will not trigger rate-limit or alerting policies.
- [ ] Keep inventory and reports in approved storage; do not commit real topology or credentials.

## Acceptance steps

1. Record NETOPPS commit SHA, Python version, OS, lab topology, and test date.
2. Run inventory validation and resolve all findings:
   ```bash
   netopps validate lab-inventory.json
   ```
3. Review the planned subnet allocation without applying it:
   ```bash
   netopps plan-subnets lab-inventory.json --pool <approved-pool-cidr> --prefix <prefix> --count <count>
   ```
   Confirm that every proposed range respects reserved addresses, DHCP scopes, routing, and existing allocations.
4. Choose one explicitly authorized device and verify a known-open management port:
   ```bash
   netopps check-connectivity lab-inventory.json --allow-network --limit 1 --timeout 1.0
   ```
5. Verify the report identifies the intended device/IP/port, returns a plausible status, and sets `configuration_changed: false`.
6. In the lab only, test a known-closed port and a controlled timeout. Confirm the command reports `connection_refused` or `timeout` without crashing.
7. Test a truncated inventory by using a limit smaller than the device count. Confirm `scope_truncated: true`, `valid: false`, and exit code 1.
8. Confirm that no configuration, credentials, or application payloads were sent; only TCP connection attempts were made.
9. Review CI status, secret scan, dependency audit, and security findings for the exact commit under test.

## Acceptance record

Record the following outside the public repository if it contains sensitive topology:

- Commit SHA and release version
- Test date and operator
- Lab environment and authorization/change reference
- Device count and types (avoid sensitive hostnames in public records)
- Known-open/known-closed/timeout outcomes
- Unexpected alerts, errors, or operational side effects
- Pass/fail decision and any limitations

## Pass criteria

- Inventory validation passes.
- Subnet plan has been manually reviewed and not applied by NETOPPS.
- Known-open and known-closed TCP tests produce expected results.
- Timeout and partial-scope cases behave as documented.
- No unexpected operational side effects occur.
- All findings and limitations are recorded.

Do not run these steps against systems without authorization. A passing TCP handshake is not a device configuration audit or an application health check.
