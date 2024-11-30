from collections import defaultdict

from shimbboleth.buildkite.pipeline_config.command_step import CommandStep
from shimbboleth.buildkite.pipeline_config.group_step import GroupStep
from shimbboleth.buildkite.pipeline_config.input_step import InputStep
from shimbboleth.buildkite.pipeline_config.wait_step import WaitStep
from shimbboleth.buildkite.pipeline_config.trigger_step import TriggerStep
from shimbboleth.buildkite.pipeline_config.block_step import BlockStep
from shimbboleth.buildkite.pipeline_config import ALL_STEP_TYPES

import pytest


STEP_EXTRA_DATA = defaultdict(
    lambda: {},
    {
        TriggerStep: {"trigger": "trigger"},
        GroupStep: {"group": None, "steps": [{"command": "hi"}]},
    },
)

# @TODO: test "is wrong type"


def kkdict(*keys: str) -> dict[str, str]:
    return dict((key, key) for key in keys)


@pytest.mark.parametrize("step_cls", ALL_STEP_TYPES)
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
def test_key_aliasing(step_cls, payload, expected):
    assert step_cls.model_validate({**payload, **STEP_EXTRA_DATA[step_cls]}).key == expected


@pytest.mark.parametrize("step_cls", ALL_STEP_TYPES)
@pytest.mark.parametrize(
    "payload, expected",
    [
        (kkdict("label"), "label"),
        (kkdict("name"), "name"),
        (kkdict("label", "name"), "name"),
        (dict(name=None, label="label"), "label"),
    ],
)
def test_label_aliasing(step_cls, payload, expected):
    assert step_cls.model_validate({**payload, **STEP_EXTRA_DATA[step_cls]}).label == expected

@pytest.mark.parametrize("step_cls", [BlockStep, InputStep, WaitStep])
def test_label_aliasing__stepname__simple(step_cls):
    stepname = step_cls.__name__.removesuffix("Step").lower()
    assert step_cls.model_validate(kkdict(stepname)).label == stepname
    assert step_cls.model_validate(kkdict(stepname, "label")).label == "label"



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


# @pytest.mark.integration
def test_bk_aliasing():
    # group
    config = [
        {
            "name": "name",
            "label": "label",
            "group": "group",
            "steps": [{"command": "hi"}],
        }
    ]  # -> group
    config = [
        {"name": "name", "label": "label", "group": None, "steps": [{"command": "hi"}]}
    ]  # -> name
    # block (and input)
    config = [{"block": "block", "name": "name", "label": "label"}]  # -> name
    config = [{"block": "block", "label": "label"}]  # -> label
    config = [{"block": "block"}]  # -> block
    # (wait step has no label so meh...)
    # command
    config = [{"command": "command", "name": "name", "label": "label"}]  # -> name
    config = [{"command": "command"}]  # -> None (empty string)
