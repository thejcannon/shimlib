"""
Tests for the JSON Schema itself.
"""

from shimbboleth.buildkite.pipeline_config import get_schema
from pathlib import Path
import os
import json


def test_gen_schema_matches_disk():
    """Test that the schema on disk is up-to-date"""
    schema = get_schema()
    json_schema = json.dumps(schema, indent=2, sort_keys=True)
    disk_schema_path = Path(__file__).parent.parent / "schema.json"
    disk_schema = disk_schema_path.read_text()
    if json_schema != disk_schema:
        if os.getenv("SHIMBBOLETH_UPDATE_SCHEMAS", "0") == "1":
            disk_schema_path.write_text(json_schema)
        else:
            print(
                "Run the test again with SHIMBBOLETH_UPDATE_SCHEMAS=1 to update the schema"
            )
        assert False, "Schema mismatch"
