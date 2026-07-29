# Changelog

All notable changes to the Montycat Python client are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.1] - 2026-07-29

Documentation, tests, and CI only — no library code changed, so upgrading from
1.1.0 is optional.

### Added

- README sections for behavior that was previously undocumented: response shape
  (`{"status", "payload", "error"}` and u128 keys arriving as strings),
  real-time subscriptions returning `(task, stop_event)` on the `port + 1`
  subscription port, TLS via `tls=True`, and owner/access management with
  `create_owner`, `grant_to`, `revoke_from`, and `Permission`.
- CI now installs the package and runs the test suite on Python 3.9 through
  3.13. The `test` job previously ran only a packaging dry run, so no test had
  ever executed in CI.
- Changelog link in the README.

### Changed

- The CI packaging dry run moved into its own `package` job, and the release job
  now depends on both `test` and `package`.

### Fixed

- The test suite annotated a schema field as `str | None`, which is PEP 604
  syntax evaluated at class-creation time and therefore requires Python 3.10,
  even though `setup.py` declares support from 3.9. Now `Optional[str]`, so the
  declared floor is real and testable.
- The README quick start used the same 3.10-only syntax, which would fail for
  any 3.9 reader copying it.
- The governance section omitted the storage-type and semantic-model constraint
  bullets and the `policy_explain` / `policy_history` paragraph that the Dart,
  Node, and Rust clients document.

## [1.1.0] - 2026-07-28

### Added

- **Data-mesh governance policy API** on `Engine`:
  - inspection — `policy_view`, `policy_history`, `policy_explain`, `policy_export`
  - mutation — `policy_grant`, `policy_revoke`, `policy_deny`, `policy_remove_denial`
  - dry runs — `policy_preview_grant`, `policy_preview_revoke`
  - manifests — `policy_validate`, `policy_plan`, `policy_apply` (JSON or YAML documents)
- New enums, exported from the package root: `PolicyCapability`, `PolicyKeyspaceType`,
  `SemanticModel`, `PolicyFormat`.
- `keyspace=` on `enable_semantic_search` / `disable_semantic_search`, for enrolling or
  dropping a single keyspace instead of the whole store. Raises `ValueError` when a
  keyspace is given without a store.

### Changed

- `grant_to` and `revoke_from` normalize the permission token (strip + lowercase), so
  `" ALL "` and `"WrItE"` are accepted and `Permission` enum members serialize correctly
  instead of reaching the wire as `Permission.ALL`.
- `policy_explain` and the policy mutations drop `keyspace` for
  `PolicyCapability.PROVISION_KEYSPACE`, which is a store-level capability.
- Policy qualifiers are capability-specific: `models`/`model` apply to
  `PROVISION_KEYSPACE` and `MANAGE_SEMANTIC`; storage-type qualifiers apply to
  keyspace-scoped capabilities except `MANAGE_SNAPSHOTS`, where in-memory storage is
  implicit. Invalid combinations raise `ValueError` before a command is sent.

### Breaking

- `enable_semantic_search(model=...)` now takes a `SemanticModel`, not a `str`. Passing a
  string raises `AttributeError`.

  ```python
  # before
  await engine.enable_semantic_search(model="bge-small")

  # now
  from montycat import SemanticModel
  await engine.enable_semantic_search(model=SemanticModel.BGE_SMALL)
  ```

### Internal

- Added `tests/test_governance_response_contract.py` — offline unit tests covering
  governance error/payload preservation through `recursive_parse_orjson` and permission
  token normalization. Not part of the distributed package.

## [1.0.7] - 2026-07-20

### Added

- Hybrid semantic search: `semantic_search_get_keys_where` and
  `semantic_search_get_values_where` take a `filters` dict applied as a hard metadata
  pre-filter, so only matching items are ranked and scores stay pure cosine. Empty
  `filters` raises `ValueError` — use the unfiltered methods instead.
- `min_score` threading through the shared semantic search path.

## [1.0.6] - 2026-07-19

### Changed

- Semantic search response structure: ranked hits are
  `{'__key__': ..., '__score__': ...}`, and the value-returning variants add
  `'__value__'`.

## [1.0.5] - 2026-07-16

### Added

- Semantic search — `enable_semantic_search` / `disable_semantic_search` plus the first
  `semantic_search_get_keys` / `semantic_search_get_values`.
- Engine controls — `enable_wait_for_index` / `disable_wait_for_index`,
  `enable_reports` / `disable_reports`, `allow_subscriptions` / `restrict_subscriptions`,
  `queue_depths`, `set_snapshot_rate`, `set_expiration_check_rate`.
- `wait_for_index` on the write paths: `insert_value`, `insert_custom_key`,
  `insert_custom_key_value`, `insert_bulk`, `update_value`, `update_bulk`, `delete_key`,
  `delete_bulk`.

## [1.0.4] - 2026-05-12

### Changed

- Input validation for key retrieval and keyspace creation, tighter `limit` validation in
  the generic and persistent KV classes.
- Bulk key handling uses explicit concatenation; query parameters are passed directly to
  `convert_to_binary_query` instead of via class attributes.
- `setup.py` became the single source of truth for package metadata; `build_and_push.sh`
  derives the version from it.

## [1.0.1] - 2026-02-04

### Added

- Nullable schema fields.

## [1.0.0] - 2025-10-17

### Added

- TLS support and a dedicated subscription port.
