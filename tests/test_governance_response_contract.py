import unittest
from unittest.mock import AsyncMock, patch

from montycat.core.engine import Engine
from montycat.core.utils import recursive_parse_orjson


class GovernanceResponseContractTests(unittest.TestCase):
    def test_preserves_governance_denial_details(self):
        error = (
            "Governance permission denied: capability 'manage-schema' "
            "on store 'orders', keyspace 'events'"
        )
        response = recursive_parse_orjson(
            {"status": False, "payload": None, "error": error}
        )
        self.assertEqual(response["error"], error)

    def test_preserves_creator_revocations_in_policy_views(self):
        response = recursive_parse_orjson(
            {
                "status": True,
                "payload": {
                    "owned_keyspaces": [
                        {"revoked_creator_capabilities": ["manage-schema"]}
                    ]
                },
                "error": None,
            }
        )
        self.assertEqual(
            response["payload"]["owned_keyspaces"][0][
                "revoked_creator_capabilities"
            ],
            ["manage-schema"],
        )


class PermissionNormalizationTests(unittest.IsolatedAsyncioTestCase):
    async def test_grant_and_revoke_normalize_permission_tokens(self):
        engine = Engine("localhost", 12777, "owner", "password", "orders")
        with patch.object(
            engine, "_execute_query_with_credentials", new=AsyncMock(return_value={"status": True})
        ) as execute:
            await engine.grant_to("delegate", " ALL ")
            await engine.revoke_from("delegate", "WrItE")

        self.assertEqual(execute.await_args_list[0].args[0][4], "all")
        self.assertEqual(execute.await_args_list[1].args[0][4], "write")


if __name__ == "__main__":
    unittest.main()
