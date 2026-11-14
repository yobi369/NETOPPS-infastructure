# NETOPPS Institutional Pilot Edition

The pilot package defines a controlled, evidence-led evaluation using the existing local NETOPPS CLI. It does not create a hosted customer workspace or connect to an institution's network.

## Start here

1. Copy [PILOT-CHARTER.md](PILOT-CHARTER.md) and agree the evaluation scope before receiving technical data.
2. Assign an institutional sponsor, technical owner, data owner and reviewer.
3. Use [EVIDENCE-REGISTER.csv](EVIDENCE-REGISTER.csv) to record each input, its source, owner, date, validation status and permitted use. Keep sensitive source material in the institution's approved repository; record only an approved reference or hash here.
4. Prepare sanitized, versioned topology and service dependency JSON using the current input contracts and examples.
5. Run the baseline and candidate assessments locally, in the institution-approved environment.
6. Complete [PILOT-ACCEPTANCE-CHECKLIST.md](PILOT-ACCEPTANCE-CHECKLIST.md) and the before/after scorecard before presenting conclusions.

## Local analysis workflow

From the NETOPPS repository root:

```bash
python -m pip install .
netopps resilience-report <topology.json> <baseline-services.json> --format json --output baseline-report.json
netopps resilience-report <topology.json> <baseline-services.json> --candidate-dependencies <candidate-services.json> --format json --output comparison-report.json
```

Use the [Engine Report Viewer](https://netopps.vercel.app/analysis/) to inspect generated reports. The viewer processes selected files locally in the browser. For sensitive institutional work, prefer the institution's approved offline workstation and keep inputs and outputs within its approved storage boundary.

## Six-stage pilot lifecycle

1. **Controlled onboarding:** signed scope, named owners, authorization, data-handling rules and stop conditions.
2. **Structured inventory:** versioned assets, sites, links, services and dependencies with stable identifiers.
3. **Evidence validation:** provenance, freshness, ownership, review state and unresolved assumptions recorded explicitly.
4. **Baseline assessment:** run the existing NETOPPS engine against the approved baseline input set.
5. **Improvement design:** create a separate candidate dependency model; never overwrite the baseline.
6. **Executive comparison:** report measured input quality, modeled changes, accepted findings, unresolved risks and decisions.

## Data and safety boundaries

- Do not submit credentials, private keys, subscriber data, personal data or unredacted production topology to public repositories or public web forms.
- The public showcase is not a secure tenant workspace. Do not enter confidential information there.
- No data upload, central storage, authentication, multi-tenant isolation, live telemetry, device discovery or network configuration is introduced by this package.
- The engine models operator-supplied data. It does not authenticate evidence or independently verify physical diversity, live capacity, failover or recovery performance.
- No production change is part of this pilot workflow. Any later operational test requires a separate written authorization and change-control process.

A pilot is not considered successful merely because NETOPPS generated a report. The institution must review the inputs, challenge the assumptions, disposition findings and approve the acceptance criteria.
