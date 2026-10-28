# CLI Output Contract

Every successful or expected-error JSON response includes `output_schema_version: 1`. This versions the output format independently of the inventory input's `schema_version`.

## Validate response

A successful validation returns:

```json
{
  "output_schema_version": 1,
  "valid": true,
  "finding_count": 0,
  "findings": []
}
```

A validation failure returns the same top-level shape with `valid: false`, a positive `finding_count`, and deterministic `findings` entries containing `code`, `path`, and `message`.

## Subnet plan response

`plan-subnets` returns `output_schema_version`, `valid`, `mode: "plan-only"`, `pool`, `prefix`, `requested`, `allocated_count`, `allocated`, `complete`, and `applied: false`. A partial allocation is a validly formed response but returns exit code 1 and `complete: false`. The connectivity response includes `scope_truncated`; the CLI returns exit code 1 if the inventory was truncated, even when all checked endpoints were reachable.

Expected planner argument errors return `output_schema_version`, `valid: false`, `error`, and an empty `allocated` list, with exit code 2. File/JSON parsing errors are written to stderr and return exit code 2 because no reliable JSON result can be constructed.

## Compatibility policy

- Adding optional output fields is permitted within version 1.
- Renaming/removing fields, changing types, or changing exit-code semantics requires a version increment and release note.
- Consumers should ignore unknown output fields and check `output_schema_version` before interpreting a response.
- Tests assert the version field and core contract for validation and planning responses.
