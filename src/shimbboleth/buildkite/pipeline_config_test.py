from functools import partial

from shimbboleth.buildkite.pipeline_config._command_step import CommandStep
from shimbboleth.buildkite.pipeline_config._group_step import GroupStep
from shimbboleth.buildkite.pipeline_config._input_step import InputStep
from shimbboleth.buildkite.pipeline_config._wait_step import WaitStep
from shimbboleth.buildkite.pipeline_config._trigger_step import TriggerStep
from shimbboleth.buildkite.pipeline_config._block_step import BlockStep

import pytest

STEP_VALIDATE_FUNCS = [
    pytest.param(BlockStep.model_validate, id="BlockStep"),
    pytest.param(CommandStep.model_validate, id="CommandStep"),
    pytest.param(InputStep.model_validate, id="InputStep"),
    pytest.param(CommandStep.model_validate, id="CommandStep"),
    pytest.param(WaitStep.model_validate, id="WaitStep"),
    pytest.param(
        lambda d: TriggerStep.model_validate({**d, "trigger": "value"}),
        id="TriggerStep",
    ),
    pytest.param(
        lambda d: GroupStep.model_validate({**d, "steps": [{"command": "hi"}]}),
        id="GroupStep",
    ),
]

# @TODO: test "is wrong type"

def kkdict(*keys: str) -> dict[str, str]:
    return dict((key, key) for key in keys)


@pytest.mark.parametrize("func", STEP_VALIDATE_FUNCS)
@pytest.mark.parametrize(
    "payload, expected",
    [
        (kkdict("key"), "key"),
        (kkdict("id"), "id"),
        (kkdict("identifier"), "identifier"),
        (kkdict("key", "id"), "key"),
        (dict(key=None, id="id"), "id"),
        (kkdict("key", "identifier"), "key"),
        (dict(key=None, identifier="identifier"), "identifier"),
        (kkdict("id", "identifier"), "id"),
        (dict(id=None, identifier="identifier"), "identifier"),
        (kkdict("key", "id", "identifier"), "key"),
        (dict(key=None, id=None, identifier="identifier"), "identifier"),
    ],
)
def test_key_aliasing(func, payload, expected):
    assert func(payload).key == expected


@pytest.mark.parametrize("func", STEP_VALIDATE_FUNCS)
@pytest.mark.parametrize(
    "payload, expected",
    [
        (kkdict("label"), "label"),
        (kkdict("name"), "name"),
        (kkdict("label", "name"), "name"),
        (dict(name=None, label="label"), "label"),
    ],
)
def test_label_aliasing(func, payload, expected):
    assert func(payload).label == expected


@pytest.mark.parametrize(
    "payload, expected",
    [
        (kkdict(), "stepname"),
        (kkdict("label"), "label"),
        (kkdict("name"), "name"),
        (kkdict("label", "name"), "name"),
        (dict(label=None, name=None), "stepname"),
    ],
)
def test_stepname_aliasing(payload, expected):
    assert BlockStep.model_validate({**payload, "block": "stepname"}).label == expected
    assert InputStep.model_validate({**payload, "input": "stepname"}).label == expected
    # assert WaitStep.model_validate({**payload, "wait": "stepname"}).label == expected
    # assert WaitStep.model_validate({**payload, "waiter": "stepname"}).label == expected
    # @TODO: GroupStep as well
