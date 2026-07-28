import unittest
from unittest.mock import AsyncMock, patch

import orjson

from montycat.core.engine import Engine
from montycat.core.tools import (
    Permission,
    PolicyCapability,
    PolicyFormat,
    PolicyKeyspaceType,
    SemanticModel,
)


class EngineUriTests(unittest.TestCase):
    def test_parses_uri_with_optional_store(self):
        engine = Engine.from_uri("montycat://alice:secret@db.example:12777/orders")
        self.assertEqual(
            (engine.host, engine.port, engine.username, engine.password, engine.store),
            ("db.example", 12777, "alice", "secret", "orders"),
        )
        self.assertIsNone(
            Engine.from_uri("montycat://alice:secret@db.example:12777").store
        )

    def test_rejects_invalid_uris(self):
        invalid = (
            "https://alice:secret@db.example:12777",
            "montycat://db.example:12777",
            "montycat://alice:secret@db.example",
        )
        for uri in invalid:
            with self.subTest(uri=uri), self.assertRaises(ValueError):
                Engine.from_uri(uri)


class EngineCommandTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.engine = Engine(
            "localhost", 12777, "owner", "password", "orders", tls=True
        )
        self.execute = AsyncMock(return_value={"status": True})
        self.patcher = patch.object(
            self.engine, "_execute_query_with_credentials", new=self.execute
        )
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    async def assert_command(self, awaitable, expected):
        self.execute.reset_mock()
        result = await awaitable
        self.assertEqual(result, {"status": True})
        self.execute.assert_awaited_once_with(expected)

    async def test_store_owner_and_access_commands(self):
        cases = (
            (self.engine.create_store(), ["create-store", "store", "orders"]),
            (self.engine.remove_store(), ["remove-store", "store", "orders"]),
            (
                self.engine.create_owner("alice", "secret"),
                ["create-owner", "username", "alice", "password", "secret"],
            ),
            (self.engine.remove_owner("alice"), ["remove-owner", "username", "alice"]),
            (self.engine.list_owners(), ["list-owners"]),
            (
                self.engine.grant_to("alice", Permission.READ, ["events", "users"]),
                [
                    "grant-to",
                    "owner",
                    "alice",
                    "permission",
                    "read",
                    "store",
                    "orders",
                    "keyspaces",
                    "events",
                    "users",
                ],
            ),
            (
                self.engine.revoke_from("alice", " WRITE ", "events"),
                [
                    "revoke-from",
                    "owner",
                    "alice",
                    "permission",
                    "write",
                    "store",
                    "orders",
                    "keyspaces",
                    "events",
                ],
            ),
        )
        for awaitable, expected in cases:
            await self.assert_command(awaitable, expected)

        with self.assertRaisesRegex(ValueError, "Invalid permission"):
            await self.engine.grant_to("alice", "admin")

    async def test_semantic_commands_and_scope_validation(self):
        await self.assert_command(
            self.engine.enable_semantic_search(
                SemanticModel.BGE_SMALL,
                field="body",
                store="catalog",
                keyspace="products",
            ),
            [
                "enable-semantic-search",
                "model",
                "bge-small",
                "field",
                "body",
                "store",
                "catalog",
                "keyspace",
                "products",
            ],
        )
        await self.assert_command(
            self.engine.disable_semantic_search(
                drop_vectors=True, store="catalog", keyspace="products"
            ),
            [
                "disable-semantic-search",
                "drop-vectors",
                "store",
                "catalog",
                "keyspace",
                "products",
            ],
        )
        with self.assertRaisesRegex(ValueError, "store is required"):
            await self.engine.enable_semantic_search(keyspace="products")
        with self.assertRaisesRegex(ValueError, "store is required"):
            await self.engine.disable_semantic_search(keyspace="products")

    async def test_policy_read_commands(self):
        await self.assert_command(
            self.engine.policy_view(owner="alice", store="catalog"),
            ["policy-view", "owner", "alice", "store", "catalog"],
        )
        await self.assert_command(
            self.engine.policy_history("alice", "catalog", "products"),
            [
                "policy-history",
                "owner",
                "alice",
                "store",
                "catalog",
                "keyspace",
                "products",
            ],
        )
        await self.assert_command(
            self.engine.policy_explain(
                PolicyCapability.MANAGE_SEMANTIC,
                "catalog",
                owner="alice",
                keyspace="products",
                keyspace_type=PolicyKeyspaceType.PERSISTENT,
                model=SemanticModel.BGE_SMALL,
            ),
            [
                "policy-explain",
                "capability",
                "manage-semantic",
                "store",
                "catalog",
                "owner",
                "alice",
                "keyspace",
                "products",
                "type",
                "persistent",
                "model",
                "bge-small",
            ],
        )

    async def test_all_policy_mutations_and_provision_scope(self):
        methods = (
            ("policy_grant", "policy-grant"),
            ("policy_revoke", "policy-revoke"),
            ("policy_deny", "policy-deny"),
            ("policy_remove_denial", "policy-remove-denial"),
            ("policy_preview_grant", "policy-preview-grant"),
            ("policy_preview_revoke", "policy-preview-revoke"),
        )
        for method_name, operation in methods:
            with self.subTest(operation=operation):
                await self.assert_command(
                    getattr(self.engine, method_name)(
                        "alice",
                        PolicyCapability.PROVISION_KEYSPACE,
                        "catalog",
                        keyspace="ignored-for-provision",
                        types=[PolicyKeyspaceType.PERSISTENT],
                        models=[SemanticModel.BGE_SMALL],
                    ),
                    [
                        operation,
                        "owner",
                        "alice",
                        "capability",
                        "provision-keyspace",
                        "store",
                        "catalog",
                        "types",
                        "persistent",
                        "models",
                        "bge-small",
                    ],
                )

    async def test_policy_manifest_commands(self):
        for method_name, operation in (
            ("policy_validate", "policy-validate"),
            ("policy_plan", "policy-plan"),
            ("policy_apply", "policy-apply"),
        ):
            await self.assert_command(
                getattr(self.engine, method_name)("rules: []", PolicyFormat.YAML),
                [operation, "format", "yaml", "document", "rules: []"],
            )
        await self.assert_command(
            self.engine.policy_export(PolicyFormat.YML),
            ["policy-export", "format", "yml"],
        )

    async def test_operator_commands(self):
        cases = (
            (
                self.engine.get_structure_available(),
                ["get-structure-available", "store", "orders"],
            ),
            (self.engine.enable_wait_for_index(), ["enable-wait-for-index"]),
            (self.engine.disable_wait_for_index(), ["disable-wait-for-index"]),
            (self.engine.enable_reports(), ["enable-reports"]),
            (self.engine.disable_reports(), ["disable-reports"]),
            (self.engine.allow_subscriptions(), ["allow-subscriptions"]),
            (self.engine.restrict_subscriptions(), ["restrict-subscriptions"]),
            (self.engine.queue_depths(), ["queue-depths"]),
            (self.engine.set_snapshot_rate(5), ["snapshot-rate", "5"]),
            (self.engine.set_expiration_check_rate(10), ["expiration-check", "10"]),
        )
        for awaitable, expected in cases:
            await self.assert_command(awaitable, expected)

        no_store = Engine("localhost", 12777, "owner", "password")
        with patch.object(
            no_store,
            "_execute_query_with_credentials",
            new=AsyncMock(return_value=True),
        ) as execute:
            await no_store.get_structure_available()
        execute.assert_awaited_once_with(["get-structure-available"])

    async def test_execute_serializes_credentials_and_tls(self):
        self.patcher.stop()
        with patch(
            "montycat.core.engine.send_data",
            new=AsyncMock(return_value={"status": True}),
        ) as send:
            result = await self.engine._execute_query_with_credentials(["list-owners"])

        self.assertEqual(result, {"status": True})
        args = send.await_args.args
        self.assertEqual(args[:2], ("localhost", 12777))
        self.assertEqual(
            orjson.loads(args[2]),
            {
                "raw": ["list-owners"],
                "credentials": ["owner", "password"],
            },
        )
        self.assertTrue(send.await_args.kwargs["tls"])


if __name__ == "__main__":
    unittest.main()
