import pytest
import httpx

import yaml

from shimbboleth.buildkite.pipeline_config import (
    BuildkitePipeline,
)
from shimbboleth.buildkite.pipeline_config._command_step import CommandStep


def test_key_aliasing():
    assert CommandStep.model_validate({"key": "mykey"}).key == "mykey"
    assert CommandStep.model_validate({"id": "myid"}).key == "myid"
    assert CommandStep.model_validate({"identifier": "myident"}).key == "myident"

    assert CommandStep.model_validate({"key": "mykey", "id": "myid"}).key == "mykey"
    assert (
        CommandStep.model_validate({"key": "mykey", "identifier": "myident"}).key
        == "mykey"
    )
    assert (
        CommandStep.model_validate({"id": "myid", "identifier": "myident"}).key
        == "myid"
    )

    assert (
        CommandStep.model_validate(
            {"key": "mykey", "id": "myid", "identifier": "myident"}
        ).key
        == "mykey"
    )
