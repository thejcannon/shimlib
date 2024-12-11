"""
These tests test the Python-side of the pipeline config classes.
"""

from collections import defaultdict
import itertools

from pydantic import ValidationError

from shimbboleth.buildkite.pipeline_config import (
    ALL_STEP_TYPES,
    BuildkitePipeline,
    CommandStep,
    GroupStep,
    InputStep,
    WaitStep,
    TriggerStep,
    BlockStep,
)
from shimbboleth.buildkite.pipeline_config._types import LooseBoolT

import pytest

from shimbboleth.buildkite.pipeline_config.command_step import NestedCommandStep


STEP_EXTRA_DATA = defaultdict(
    lambda: {},
    {
        TriggerStep: {"trigger": "trigger"},
        GroupStep: {"group": None, "steps": [{"command": "hi"}]},
    },
)


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
    step = step_cls.model_validate({**payload, **STEP_EXTRA_DATA[step_cls]})
    assert step.key == (
        "key"
        if payload.get("key", None) is not None
        else "id"
        if payload.get("id", None) is not None
        else "identifier"
        if payload.get("identifier", None) is not None
        else None
    )
    assert step.id == step.key
    assert step.identifier == step.key


@pytest.mark.parametrize("step_cls", ALL_STEP_TYPES)
def test_key_aliasing__wrong_type_on_ignored_field(step_cls):
    step_cls.model_validate(
        {"key": "key", "id": {}, "identifier": {}, **STEP_EXTRA_DATA[step_cls]}
    )
    step_cls.model_validate({"id": "", "identifier": {}, **STEP_EXTRA_DATA[step_cls]})


@pytest.mark.parametrize("step_cls", ALL_STEP_TYPES)
@pytest.mark.parametrize(
    "payload",
    [
        {"key": {}},
        {"id": {}},
        {"identifier": {}},
        {"key": None, "id": {}},
        {"key": None, "id": None, "identifier": {}},
    ],
)
def test_key_aliasing__wrong_type_on_field(step_cls, payload):
    with pytest.raises(ValidationError):
        step_cls.model_validate({**payload, **STEP_EXTRA_DATA[step_cls]})


@pytest.mark.parametrize("step_cls", ALL_STEP_TYPES)
def test_key_not_uuid(step_cls):
    with pytest.raises(ValidationError, match=r"must not be a valid UUID"):
        step_cls.model_validate(
            {"key": "e03c95ff-7a98-4a32-8a0c-fd37f36a06f7", **STEP_EXTRA_DATA[step_cls]}
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


@pytest.mark.parametrize("step_cls", ALL_STEP_TYPES)
def test_label_aliasing__wrong_type_on_ignored_field(step_cls):
    step_cls.model_validate({"name": "", "label": {}, **STEP_EXTRA_DATA[step_cls]})


@pytest.mark.parametrize("step_cls", ALL_STEP_TYPES)
@pytest.mark.parametrize(
    "payload",
    [
        {"name": {}},
        {"label": {}},
        {"name": None, "label": {}},
    ],
)
def test_label_aliasing__wrong_type_on_field(step_cls, payload):
    with pytest.raises(ValidationError):
        step_cls.model_validate({**payload, **STEP_EXTRA_DATA[step_cls]})


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


@pytest.mark.parametrize("step_cls", [BlockStep, InputStep, WaitStep])
@pytest.mark.parametrize(
    "payload",
    [
        {"stepname": {}},
        {"name": None, "label": None, "stepname": {}},
    ],
)
def test_label_aliasing__wrong_type_with_stepname(step_cls, payload):
    with pytest.raises(ValidationError):
        step_cls.model_validate({**payload, **STEP_EXTRA_DATA[step_cls]})


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


@pytest.mark.parametrize(
    "data, expected",
    [
        ({"commands": "commands"}, ["commands"]),
        ({"commands": ["commands"]}, ["commands"]),
        ({"command": None}, []),
    ],
)
def test_command_step_command_alias(data, expected):
    step = CommandStep.model_validate(data)
    assert step.command == expected
    assert step.commands == expected

@pytest.mark.parametrize(
    "data, expected",
    [
        ({"command": {"command": "command"}}, CommandStep(command=["command"])),
        ({"commands": {"command": "command"}}, CommandStep(command=["command"])),
        ({"script": {"command": "command"}}, CommandStep(command=["command"])),
        ({"command": None}, None),
    ],
)
def test_nested_command_step_command_alias(data, expected):
    step = NestedCommandStep.model_validate(data)
    assert step.command == expected
    assert step.commands == expected
    assert step.script == expected



# @TODO: NestedWaitStep aliases
# @TODO: Test pipeline discriminator

def test_agents_parsing():
    assert (
        BuildkitePipeline.model_validate({"agents": {}, "steps": ["wait"]}).agents == {}
    )
    assert (
        BuildkitePipeline.model_validate({"agents": [], "steps": ["wait"]}).agents == {}
    )
    assert BuildkitePipeline.model_validate(
        {"agents": {"a": "b"}, "steps": ["wait"]}
    ).agents == {"a": "b"}
    assert BuildkitePipeline.model_validate(
        {"agents": ["a=b"], "steps": ["wait"]}
    ).agents == {"a": "b"}


def test_loose_bool():
    from pydantic import BaseModel

    class Model(BaseModel, strict=True):
        field: LooseBoolT

    assert Model.model_validate({"field": True}).field is True
    assert Model.model_validate({"field": "true"}).field is True
    assert Model.model_validate({"field": "false"}).field is False
    assert Model.model_validate({"field": False}).field is False


@pytest.mark.parametrize(
    "step_cls", [BlockStep, CommandStep, InputStep, TriggerStep, WaitStep]
)
def test_branches_canonicalization(step_cls):
    assert step_cls.model_validate(
        {"branches": "main", **STEP_EXTRA_DATA[step_cls]}
    ).branches == ["main"]
    assert step_cls.model_validate(
        {"branches": ["main"], **STEP_EXTRA_DATA[step_cls]}
    ).branches == ["main"]
    assert (
        step_cls.model_validate(
            {"branches": None, **STEP_EXTRA_DATA[step_cls]}
        ).branches
        is None
    )


# @TODO: Each of these can be run against upstream BK API
@pytest.mark.parametrize(
    "config, error",
    [
        pytest.param(
            {
                "steps": [
                    {
                        "input": "input",
                        "fields": [{"select": "select", "key": "key", "options": []}],
                    }
                ]
            },
            "`options` can't be empty",
            marks=pytest.mark.xfail,  # Wrong error mesage
        ),
        (
            {"steps": [{"command": "command", "commands": "commands"}]},
            "Step type is ambiguous: use only one of `command` or `commands`",
        ),
        (
            {"steps": [{"command": None, "commands": "commands"}]},
            "Step type is ambiguous: use only one of `command` or `commands`",
        ),
        (
            {"steps": [{"command": "command", "commands": None}]},
            "Step type is ambiguous: use only one of `command` or `commands`",
        ),
        (
            {"steps": [{"command": None, "commands": None}]},
            "Step type is ambiguous: use only one of `command` or `commands`",
        ),
        (
            {"steps": [{"command": {"command": "command"}, "commands": {"command": "command"}}]},
            "Step type is ambiguous: use only one of `command` or `commands`",
        ),
        (
            {"steps": [{"command": {"command": "command"}, "script": {"command": "command"}}]},
            "Step type is ambiguous: use only one of `command` or `script`",
        ),
    ],
)
def test_error_from_definition(config, error):
    with pytest.raises(ValidationError) as e:
        BuildkitePipeline.model_validate(config)
    assert e.value.errors()[0]["ctx"]["error"].args[0] == error
