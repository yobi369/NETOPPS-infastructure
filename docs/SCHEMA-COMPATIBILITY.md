# Inventory Schema Compatibility Policy

## Current contract

- The root inventory must use the integer `schema_version: 1`.
- The root object accepts only `schema_version`, `devices`, and `networks`.
- Device and network records validate the documented core fields. Optional `site` values must be non-empty strings.
- Additional device/network metadata is allowed for forward-compatible local annotations, but unknown root properties are rejected to prevent misspelled top-level sections.
- The JSON Schema in `schemas/inventory.schema.json` is the structural contract; `netopps validate` adds semantic checks such as duplicate addresses and overlapping CIDRs.

## Compatibility rules

1. A new optional device/network metadata field may be added in version 1 if older validators safely ignore it and it does not change the meaning of an existing field.
2. Changing a field's type, meaning, requiredness, or validation semantics is a breaking change and requires a schema-version increment.
3. New root-level sections require a schema-version increment because unknown root properties fail closed.
4. Every schema change must update the schema, example inventory, CLI validator, and tests in the same pull request.
5. A version bump must include an explicit migration plan and before/after fixtures. Never silently rewrite an inventory file.
6. Migration tooling, when introduced, must support a dry-run diff, preserve the original input, report each conversion, and validate both source and output.
7. The CLI must reject unsupported schema versions rather than guessing or automatically upgrading data.

## Current limitations

Only schema version 1 is implemented. No migration engine or compatibility adapter exists yet. The policy defines how future versions should be introduced; it does not claim that migration tooling has been built.
