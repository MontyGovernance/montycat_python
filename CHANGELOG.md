# Changelog

All notable changes to the Montycat Python client are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0]

Opt-in connection pooling, plus two framing fixes that pooling depends on, and
the semantic-configuration commands from the previous release line.

Additive — upgrading needs no code changes, with one behavior change: a
subscription callback now fires once per frame (see Fixed).

### Added

- **Opt-in connection pooling.** Every request previously opened a TCP
  connection, sent one request, read one response, and closed. Reuse removes the
  handshake from every call after the first:

  ```python
  from montycat import Engine, PoolConfig, close_all_pools

  connection = Engine(
      host="127.0.0.1", port=21210, username="USER", password="12345",
      store="Departments",
      pool=PoolConfig(),        # the only new argument; omit for today's behavior
  )

  Sales.connect_engine(connection)
  await Sales.insert_value(sale)     # unchanged

  await close_all_pools()            # before exit
  ```

  Pools live in a module-level registry keyed by `(host, port, tls)`, so every
  keyspace class pointing at one server shares a single pool. `connect_engine`
  copies scalars off the engine and discards it, so a pool attached to the
  engine object could never have been reached. `tls` is part of the key because
  a plaintext and a TLS connection to one address are not interchangeable.

  Disabled by default: an idle pooled connection still holds one of the engine's
  connection permits, so the bound is deliberately conservative (`max_idle=8`,
  `idle_timeout=30.0`). Subscriptions are never pooled, and a connection is held
  exclusively for one request/response — two coroutines interleaving writes on
  one socket would deliver a response to the wrong caller. A cancelled request
  closes its connection rather than returning it, since a cancelled task may
  have left an unread response in the socket.

  Exported `PoolConfig` and `close_all_pools` from the package root.

### Fixed

- **A subscription frame could be delivered concatenated with the next one, or
  dropped entirely.** The reader appended raw socket chunks and invoked the
  callback with whatever had accumulated, then cleared the buffer. Two frames
  arriving in one chunk were delivered as a single event, and a chunk ending
  mid-frame after a complete one had that partial frame discarded by the clear.
  Frames are now read one at a time and the callback fires once per frame.

- **A response kept the bytes that followed its newline.** The read loop stopped
  once a chunk contained `\n` but appended the whole chunk, so anything the
  server had already sent toward the *next* response was parsed as part of this
  one. Harmless while every connection was discarded immediately; fatal on a
  pooled connection. Responses now use `StreamReader.readline()`, which leaves
  the remainder in the reader's own buffer, travelling with the connection.

- **EOF before any response byte returned an empty success.** Callers received
  something they would then try to parse. It now surfaces as an error.

## [1.1.3]

Adds a way to read the server's real semantic configuration, and a safe way to
change an enrolled keyspace's embedding model. Additive — upgrading from 1.1.2
requires no code changes.

### Added

- `Engine.get_semantic_status(store, keyspace)` returns the server's actual
  semantic settings rather than what the caller assumed: the DB-wide switch and
  default model, plus each enrolled keyspace's model, dimensions, field,
  storage type, and whether a backfill is still pending.
- `Engine.reembed_semantic_search(model, store, keyspace, field)` atomically
  drops one keyspace's vectors, records the new configuration, and starts a
  complete backfill. It reports the previous model alongside the new one, so a
  caller can confirm what it replaced.
- **`Keyspace.InMemory.do_snapshots_for_keyspace()`** — the method was spelled
  `do_snaphots_for_keyspace` (missing `s`), the only client of the four to
  misspell it. The correct spelling now exists; the old name is kept as a
  deprecated alias so existing callers keep working.

### Changed

- Documented that `enable_semantic_search` leaves an already-enrolled keyspace
  alone. It was never a way to switch models; `reembed_semantic_search` is.
  Behavior is unchanged — only the documentation was misleading.
- Corrected the `disable_semantic_search` docs: `drop_vectors` is not "required
  before switching to a different embedding model". Use
  `reembed_semantic_search`, which does not leave the keyspace unsearchable in
  between.

### Deprecated

- `Keyspace.InMemory.do_snaphots_for_keyspace()`. It forwards to
  `do_snapshots_for_keyspace()` and will be removed in a future major release.

## [1.1.2]

Fixes a hang that affects any request whose payload contains the word
`subscribe`. **Upgrade from 1.1.1 is recommended.**

### Fixed

- **A request whose value contained the substring `subscribe` never returned.**
  Subscription mode was detected with `b"subscribe" in query`, so a call like
  `insert_value({"note": "please subscribe"})` was routed into the streaming
  branch — which has no read timeout and loops forever. Any record mentioning
  the word was affected, `unsubscribe` included.

  A request is now a subscription because the caller supplied a `callback`. That
  was always the real distinction — `_run_query` already chose the subscription
  port on exactly that basis — so the two signals can no longer disagree.
  Intent is no longer inferred from user data.

  Present in every release before this one. The Rust and Dart clients carry the
  same defect and are fixed in their matching releases; the Node client was
  already correct.

## [1.1.1]

Documentation, tests, and CI only — no library code changed, so upgrading from
1.1.0 is optional.

### Added

- README sections for behavior that was previously undocumented: response shape
  (`{"status", "payload", "error"}` and u128 keys arriving as strings),
  real-time subscriptions returning `(task, stop_event)` on the `port + 1`
  subscription port, TLS via `tls=True`, and owner/access management with
  `create_owner`, `grant_to`, `revoke_from`, and `Permission`.
- CI now installs the package and runs the test suite on Python 3.10 through
  3.13. The `test` job previously ran only a packaging dry run, so no test had
  ever executed in CI.
- Changelog link in the README.

### Changed

- **Declared Python support is now 3.10+, corrected from 3.9+.** The package has
  never been importable on 3.9: `core/schema.py` and `store_classes/kv.py` both
  import `types.UnionType` at module scope, which was added in 3.10, so any 3.9
  install failed with `ImportError` on the first `import montycat`. The metadata
  and the README FAQ advertised a version that never worked. Nothing that
  currently runs is affected, and 3.9 reached end of life in October 2025.
- The CI packaging dry run moved into its own `package` job, and the release job
  now depends on both `test` and `package`.

### Fixed

- The governance section omitted the storage-type and semantic-model constraint
  bullets and the `policy_explain` / `policy_history` paragraph that the Dart,
  Node, and Rust clients document.

## [1.1.0]

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

## [1.0.7]

### Added

- Hybrid semantic search: `semantic_search_get_keys_where` and
  `semantic_search_get_values_where` take a `filters` dict applied as a hard metadata
  pre-filter, so only matching items are ranked and scores stay pure cosine. Empty
  `filters` raises `ValueError` — use the unfiltered methods instead.
- `min_score` threading through the shared semantic search path.

## [1.0.6]

### Changed

- Semantic search response structure: ranked hits are
  `{'__key__': ..., '__score__': ...}`, and the value-returning variants add
  `'__value__'`.

## [1.0.5]

### Added

- Semantic search — `enable_semantic_search` / `disable_semantic_search` plus the first
  `semantic_search_get_keys` / `semantic_search_get_values`.
- Engine controls — `enable_wait_for_index` / `disable_wait_for_index`,
  `enable_reports` / `disable_reports`, `allow_subscriptions` / `restrict_subscriptions`,
  `queue_depths`, `set_snapshot_rate`, `set_expiration_check_rate`.
- `wait_for_index` on the write paths: `insert_value`, `insert_custom_key`,
  `insert_custom_key_value`, `insert_bulk`, `update_value`, `update_bulk`, `delete_key`,
  `delete_bulk`.

## [1.0.4]

### Changed

- Input validation for key retrieval and keyspace creation, tighter `limit` validation in
  the generic and persistent KV classes.
- Bulk key handling uses explicit concatenation; query parameters are passed directly to
  `convert_to_binary_query` instead of via class attributes.
- `setup.py` became the single source of truth for package metadata; `build_and_push.sh`
  derives the version from it.

## [1.0.1]

### Added

- Nullable schema fields.

## [1.0.0]

### Added

- TLS support and a dedicated subscription port.
