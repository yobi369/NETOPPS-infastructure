# NETOPPS Commercial Licensing Readiness

This checklist separates what the repository can document today from what must be completed before a customer is promised commercial rights or operational service levels.

## Rights and ownership

- [ ] Confirm the legal identity of the rights holder and the complete ownership chain for all current code, documentation, examples, logos, and other assets.
- [ ] Identify any employer, client, university, contractor, or third-party ownership claims.
- [ ] Review every dependency and bundled asset; maintain a third-party notices and licence inventory.
- [ ] Have counsel review the dual-licensing model, the AGPL notice, historical MIT grants, and the proposed CLA.
- [ ] Execute a CLA with each external contributor before merging contributions intended for commercial relicensing.
- [ ] Store signed CLAs and approvals privately with contribution references; do not commit personal signatures or identity documents.
- [ ] Record explicit written rights for any contribution that is not covered by an executed CLA.

## Product and release definition

- [ ] Define the commercial product boundary and exact components included.
- [ ] Select a versioned release or commit SHA for each customer agreement.
- [ ] Build and retain reproducible release artifacts and checksums.
- [ ] Publish a software bill of materials (SBOM) and dependency licence report for each release.
- [ ] Define supported Python versions, operating environments, installation procedure, backup, and upgrade path.
- [ ] Complete authorized lab acceptance for the customer deployment profile; do not imply the local CLI is a hosted platform or live network controller.
- [ ] Document known limitations and customer prerequisites.

## Commercial terms

- [ ] Define licence metric: organization, site, installation, operator, or another measurable unit.
- [ ] Define internal use, affiliate use, service-provider access, embedding, redistribution, and source-code rights.
- [ ] Set pricing, payment milestones, taxes, renewal, and any optional implementation fees.
- [ ] Decide whether updates, maintenance, training, and support are included or separately priced.
- [ ] Define support hours, contact path, response targets, severity levels, and exclusions before offering an SLA.
- [ ] Complete warranty, liability, indemnity, confidentiality, audit, governing-law, and dispute provisions with counsel.
- [ ] Use a separate data-processing/security schedule if a future service processes personal or customer data.

## Customer acceptance and records

- [ ] Record the customer legal entity, authorized signatories, deployment scope, release, and executed agreement.
- [ ] Record any customer-specific deviations and approvals.
- [ ] Provide installation, security, operations, backup, and limitations documentation.
- [ ] Keep a renewal and support-contact register.
- [ ] Reassess the agreement when product scope, ownership, dependencies, or deployment model changes.

## Current product boundary

The repository currently documents a local Python CLI and local, simulation-only resilience analysis. It does not currently provide hosted multi-tenant access control, central telemetry collection, a managed service, guaranteed support, or an SLA. Do not sell or promise those capabilities until they are implemented, tested, and contractually defined.
