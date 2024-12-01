from collections import defaultdict
from collections.abc import Container
import itertools

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


def kkdict(*keys: str, **kwargs: str | None) -> dict[str, str | None]:
    kwargs.update((key, key) for key in keys)
    return kwargs


def all_combos(possibilities: list | tuple):
    return [
        combo
        for length in range(len(possibilities) + 1)
        for combo in itertools.combinations(possibilities, length)
    ]


def kaboom(*aliases):
    return [
        {**{key: key for key in keys}, **{key: None for key in nulld_keys}}
        for keys in all_combos(aliases)
        for nulld_keys in all_combos([alias for alias in aliases if alias not in keys])
    ]


@pytest.mark.parametrize("step_cls", ALL_STEP_TYPES)
@pytest.mark.parametrize("payload", kaboom("key", "id", "identifier"))
def test_key_aliasing(step_cls, payload):
    assert step_cls.model_validate({**payload, **STEP_EXTRA_DATA[step_cls]}).key == (
        "key"
        if payload.get("key", None) is not None
        else "id"
        if payload.get("id", None) is not None
        else "identifier"
        if payload.get("identifier", None) is not None
        else None
    )


@pytest.mark.parametrize("step_cls", [CommandStep, TriggerStep])
@pytest.mark.parametrize("payload", kaboom("name", "label"))
def test_label_aliasing__just_name_label(step_cls, payload):
    step = step_cls.model_validate({**payload, **STEP_EXTRA_DATA[step_cls]})
    assert step.name == (
        "name"
        if payload.get("name", None)
        else "label"
        if payload.get("label", None)
        else None
    )
    assert step.label == step.name

@pytest.mark.parametrize("step_cls", [BlockStep, InputStep, WaitStep])
@pytest.mark.parametrize("payload", kaboom("name", "label", "stepname"))
def test_label_aliasing__with_stepname(step_cls, payload):
    payload = payload.copy()
    stepname = step_cls.__name__.removesuffix("Step").lower()
    if "stepname" in payload:
        payload[stepname] = payload.pop("stepname")
    step = step_cls.model_validate({**payload, **STEP_EXTRA_DATA[step_cls]})
    assert step.name == (
        "name"
        if payload.get("name", None)
        else "label"
        if payload.get("label", None)
        else "stepname"
        if payload.get(stepname, None)
        else None
    )
    assert step.label == step.name
    assert getattr(step, stepname) == step.name

@pytest.mark.parametrize(
    "payload",
    # NB: `group` is a required property, so filter out payloads without it
    [payload for payload in kaboom("name", "label", "group") if "group" in payload],
)
def test_label_aliasing__stepname__groupstep(payload):
    group_step = GroupStep.model_validate(
        {**payload, "steps": [{"command": "command"}]}
    )
    assert group_step.group == (
        "group"
        if payload.get("group", None)
        else "name"
        if payload.get("name", None)
        else "label"
        if payload.get("label", None)
        else None
    )
    assert group_step.label == group_step.group
    assert group_step.name == group_step.group




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
