from shimbboleth.buildkite.pipeline_config._command_step import CommandStep
from shimbboleth.buildkite.pipeline_config._group_step import GroupStep
from shimbboleth.buildkite.pipeline_config._input_step import InputStep
from shimbboleth.buildkite.pipeline_config._wait_step import WaitStep
from shimbboleth.buildkite.pipeline_config._trigger_step import TriggerStep
from shimbboleth.buildkite.pipeline_config._block_step import BlockStep

import pytest


@pytest.mark.parametrize(
    ["step_cls", "extra"],
    [
        [BlockStep, {}],
        [CommandStep, {}],
        [InputStep, {}],
        [CommandStep, {}],
        [WaitStep, {}],
        [TriggerStep, {"trigger": "value"}],
        [GroupStep, {"steps": [{"command": "hi"}]}],
    ],
)
def test_key_aliasing(step_cls, extra):
    assert step_cls.model_validate({"key": "mykey", **extra}).key == "mykey"
    assert step_cls.model_validate({"id": "myid", **extra}).key == "myid"
    assert step_cls.model_validate({"identifier": "myident", **extra}).key == "myident"

    assert (
        step_cls.model_validate({"key": "mykey", "id": "myid", **extra}).key == "mykey"
    )
    assert (
        step_cls.model_validate({"key": "mykey", "identifier": "myident", **extra}).key
        == "mykey"
    )
    assert (
        step_cls.model_validate({"id": "myid", "identifier": "myident", **extra}).key
        == "myid"
    )

    assert (
        step_cls.model_validate(
            {"key": "mykey", "id": "myid", "identifier": "myident", **extra}
        ).key
        == "mykey"
    )
