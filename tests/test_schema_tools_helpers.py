import unittest
from typing import Optional

import orjson

from montycat.core.schema import Schema
from montycat.core.tools import Limit, Permission, Pointer, Timestamp
from montycat.core.utils import is_u128, recursive_parse_orjson
from montycat.store_functions.store_generic_functions import (
    convert_custom_key,
    convert_custom_keys,
    convert_custom_keys_values,
    convert_to_binary_query,
    handle_limit,
    handle_pointers_for_update,
    handle_timestamps_and_pointers,
    modify_pointers,
    normalize_bools,
)


class ToolsTests(unittest.TestCase):
    def test_timestamp_variants_and_invalid_configuration(self):
        self.assertEqual(
            Timestamp(start=10, end=20).serialize(), {"range_timestamp": [10, 20]}
        )
        self.assertEqual(Timestamp(after=10).serialize(), {"after_timestamp": 10})
        self.assertEqual(Timestamp(before=20).serialize(), {"before_timestamp": 20})
        self.assertEqual(Timestamp(timestamp=15).serialize(), 15)
        with self.assertRaisesRegex(ValueError, "Invalid timestamp"):
            Timestamp().serialize()

    def test_pointer_limit_and_permission(self):
        class Keyspace:
            keyspace = "events"

        self.assertEqual(Pointer(Keyspace(), "abc").serialize(), ["events", "abc"])
        self.assertEqual(Limit(2, 5).serialize(), {"start": 2, "stop": 5})
        self.assertEqual(str(Permission.ALL), "all")


class SchemaTests(unittest.TestCase):
    class Event(Schema):
        name: str
        count: int
        # Optional[...] rather than PEP 604 `str | None`: annotations are
        # evaluated at class-creation time and `|` on types needs Python 3.10,
        # while setup.py declares support from 3.9.
        note: Optional[str]

    class LinkedEvent(Schema):
        parent: Pointer
        created_at: Timestamp

    def test_validates_required_optional_extra_and_types(self):
        event = self.Event(name="launch", count=2)
        self.assertEqual(
            event.serialize(),
            {
                "name": "launch",
                "count": 2,
                "note": None,
                "schema": "Event",
            },
        )
        self.assertEqual(str(self.Event), "Event")
        self.assertEqual(repr(self.Event), "Event")

        with self.assertRaisesRegex(ValueError, "Missing required field"):
            self.Event(name="launch")
        with self.assertRaisesRegex(ValueError, "Unexpected field"):
            self.Event(name="launch", count=2, surprise=True)
        with self.assertRaisesRegex(TypeError, "should be of type 'int'"):
            self.Event(name="launch", count="two")

    def test_extracts_pointer_and_timestamp_metadata(self):
        linked = self.LinkedEvent(
            parent=Pointer("events", "root"),
            created_at=Timestamp(timestamp=123),
        )
        self.assertEqual(linked.pointers, {"parent": ["events", "root"]})
        self.assertEqual(linked.timestamps, {"created_at": 123})
        self.assertEqual(linked.schema, "LinkedEvent")


class UtilityTests(unittest.TestCase):
    def test_recursively_parses_nested_json_and_preserves_u128(self):
        huge = "340282366920938463463374607431768211455"
        parsed = recursive_parse_orjson(
            {"nested": '[1, "{\\"ok\\": true}"]', "tuple": ("2",), "id": huge}
        )
        self.assertEqual(parsed["nested"], [1, {"ok": True}])
        self.assertEqual(parsed["tuple"], (2,))
        self.assertEqual(parsed["id"], huge)
        self.assertTrue(is_u128(huge))
        self.assertFalse(is_u128("123"))

    def test_key_pointer_boolean_and_limit_helpers(self):
        self.assertEqual(convert_custom_keys(["a", 2]), [
            convert_custom_key("a"),
            convert_custom_key(2),
        ])
        self.assertEqual(
            convert_custom_keys_values({"a": 1}),
            {convert_custom_key("a"): 1},
        )
        value = {"parent": Pointer("events", "abc")}
        self.assertEqual(
            handle_pointers_for_update(value), {"parent": ["events", "abc"]}
        )
        self.assertEqual(
            modify_pointers({"pointers": {"parent": ["events", "abc"]}}),
            {"pointers": {"parent": ["events", convert_custom_key("abc")]}},
        )
        self.assertEqual(orjson.loads(normalize_bools({"ok": True})), {"ok": True})
        self.assertEqual(handle_limit([2, 5]), {"start": 2, "stop": 5})
        self.assertEqual(handle_limit(5), {"start": 0, "stop": 5})
        self.assertEqual(handle_limit([]), {"start": 0, "stop": 0})
        for invalid in ([2], [5, 2], -1, "5"):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                handle_limit(invalid)

    def test_timestamp_and_pointer_search_criteria(self):
        result = handle_timestamps_and_pointers(
            {
                "created": Timestamp(after=10),
                "parent": Pointer("events", "abc"),
                "active": True,
            }
        )
        self.assertEqual(
            result,
            {
                "created": {"after_timestamp": 10},
                "active": True,
                "pointers": {"parent": ["events", "abc"]},
            },
        )

    def test_binary_query_serialization_and_optional_semantic_fields(self):
        class Query:
            username = "owner"
            password = "secret"
            keyspace = "events"
            store = "orders"
            persistent = True
            distributed = False

        query = orjson.loads(
            convert_to_binary_query(
                Query,
                command="semantic-search",
                key=7,
                value={"schema": "Event", "parent": Pointer("events", "abc")},
                search_criteria={"active": True},
                bulk_keys=[1, "two"],
                semantic_query="launch",
                min_score=0.7,
                semantic_filter={"created": Timestamp(after=10)},
                wait_for_index=True,
            )
        )
        self.assertEqual(query["key"], "7")
        self.assertEqual(query["schema"], "Event")
        self.assertEqual(query["bulk_keys"], ["1", "two"])
        self.assertEqual(query["search_criteria"], "launch")
        self.assertEqual(query["min_score"], 0.7)
        self.assertTrue(query["wait_for_index"])
        self.assertEqual(orjson.loads(query["value"])["parent"], ["events", "abc"])
        self.assertEqual(
            orjson.loads(query["semantic_filter"]),
            {"created": {"after_timestamp": 10}},
        )

    def test_bulk_values_must_share_one_schema(self):
        class Query:
            username = password = keyspace = store = ""
            persistent = distributed = False

        with self.assertRaisesRegex(ValueError, "only one schema"):
            convert_to_binary_query(
                Query,
                bulk_values=[
                    {"schema": "First", "value": 1},
                    {"schema": "Second", "value": 2},
                ],
            )


if __name__ == "__main__":
    unittest.main()
