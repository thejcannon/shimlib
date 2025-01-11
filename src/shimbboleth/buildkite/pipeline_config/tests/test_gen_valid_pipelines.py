"""
@TODO: ...
"""

from itertools import chain
from pathlib import Path

from shimbboleth.buildkite.pipeline_config import BuildkitePipeline

from shimbboleth.buildkite.pipeline_config.tests.conftest import STEP_TYPE_PARAMS

import pytest
from pytest import param

GENERATION_PATH = Path(__file__).parent / "valid-pipelines" / "generated"

BASECAMP_CAMPFIRE_URL = "https://3.basecamp.com/1234567/integrations/qwertyuiop/buckets/1234567/chats/1234567/lines"

BOOLVALS = ("true", "false", True, False)


@pytest.mark.parametrize(
    "pipeline_step",
    [
        # Nones
        {"block": None},
        {"input": None},
        {"wait": None},
        # Strings
        *("block", "manual", "input", "wait", "waiter"),
        # Tests against all step types
        *(
            param(
                {
                    **step_param.values[0],  # type: ignore
                    **step_type_param.dumped_default,
                },
                id=f"{step_type_param.stepname}-{step_param.id}",
            )
            for step_type_param in STEP_TYPE_PARAMS.values()
            for step_param in (
                # allow_dependency_failure
                *(
                    param(
                        {"allow_dependency_failure": value},
                        id="all-allow_dependency_failure",
                    )
                    for value in BOOLVALS
                ),
                # depends_on
                param({"depends_on": "scalar"}, id="depends_on"),
                param({"depends_on": ["string"]}, id="depends_on"),
                param({"depends_on": [{"step": "step_id"}]}, id="depends_on"),
                *(
                    param(
                        {"depends_on": [{"step": "step_id", "allow_failure": value}]},
                        id="depends_on-allow_failure",
                    )
                    for value in BOOLVALS
                ),
                param(
                    {
                        "depends_on": [
                            "string",
                            {"step": "step_id", "allow_failure": True},
                        ]
                    },
                    id="depends_on-mixed",
                ),
                # if
                param({"if": "string"}, id="if"),
                # key-id-identifier
                param({"key": "key1"}, id="key"),
                param({"id": "id1"}, id="id"),
                param({"identifier": "identifier1"}, id="identifier"),
                param({"key": "key2", "id": "id2"}, id="key-id"),
                param(
                    {"key": "key3", "identifier": "identifier2"}, id="key-identifier"
                ),
                param({"id": "id3", "identifier": "identifier3"}, id="id-identifier"),
                param(
                    {"key": "key4", "id": "id4", "identifier": "identifier4"},
                    id="key-id-identifier",
                ),
                # @TODO: Also the cases where the value is null (techincally, but also bleh)
                param(
                    {step_type_param.stepname: step_type_param.stepname}, id="stepname"
                ),
                param(
                    {
                        step_type_param.stepname: step_type_param.stepname,
                        "label": "label",
                    },
                    id="stepname-label",
                ),
                param(
                    {
                        step_type_param.stepname: step_type_param.stepname,
                        "name": "name",
                    },
                    id="stepname-name",
                ),
                param(
                    {
                        step_type_param.stepname: step_type_param.stepname,
                        "label": "label",
                        "name": "name",
                    },
                    id="stepname-label-name",
                ),
            )
        ),
        # All but group
        *(
            param(
                {
                    **step_param.values[0],  # type: ignore
                    **step_type_param.dumped_default,
                },
                id=f"{step_type_param.stepname}-{step_param.id}",
            )
            for steptype, step_type_param in STEP_TYPE_PARAMS.items()
            if steptype != "group"
            for step_param in (
                # type-label-name
                param({"type": step_type_param.type}, id="type"),
                param(
                    {"type": step_type_param.type, "label": "label"}, id="type-label"
                ),
                param(
                    {"type": step_type_param.type, "label": "label", "name": "name"},
                    id="type-label-name",
                ),
                # branches
                param({"branches": "master"}, id="branches-string"),
                param({"branches": ["master"]}, id="branches-list"),
            )
        ),
        # nested
        # @TODO: test the aliases too (manueal, waiter)
        *(
            param(
                {step_type_param.stepname: step_type_param.ctor_defaults},
                id=f"{step_type_param.stepname}-nested",
            )
            for steptype, step_type_param in STEP_TYPE_PARAMS.items()
            if steptype != "group"
        ),
        # BlockStep
        *(
            param({"type": "block", "blocked_state": state}, id="blocked-state")
            for state in ("passed", "failed", "running")
        ),
        # Command Step
        param(
            {
                "type": "command",
                "agents": ["noequal", "key1=value", "key2=value=value"],
            },
            id="command-agents-list",
        ),
        param(
            {
                "type": "command",
                "agents": {
                    "str": "string",
                    "int": 0,
                    "bool": True,
                    "list": ["one", "two"],
                    "obj": {"key": "value"},
                    "none": None,
                    "has-an-equal": "key=value",
                },
            },
            id="command-agents-object",
        ),
        param(
            {
                "type": "command",
                "agents": {"noequal": "true", "key1": "value", "key2": "value=value"},
            },
            id="command-agents-object-simple",
        ),
        param(
            {
                "type": "command",
                "agents": {
                    "str": "string",
                    "int": "0",
                    "bool": "true",
                    "list": '["one", "two"]',
                    "obj": '{"key"=>"value"}',
                    "has-an-equal": "key=value",
                },
            },
            id="command-agents-object-strings",
        ),
        # Group Step
        param(
            {
                "group": "group",
                "steps": [{"type": "wait"}],
                "notify": [
                    "github_check",
                    "github_commit_status",
                    {"basecamp_campfire": BASECAMP_CAMPFIRE_URL},
                    {"slack": "#general"},
                    {"slack": {"channels": ["#general"]}},
                    {"slack": {"channels": ["#general"], "message": "message"}},
                    {"github_commit_status": {"context": "context"}},
                    {"github_check": {"name": "name"}},
                ],
            },
            id="group-notify",
        ),
        *(
            param(
                {
                    "group": "group",
                    "steps": [{"type": "wait"}],
                    "skip": value,
                },
                id="group-skip",
            )
            for value in (True, False, "", "reason")
        ),
        # "Manual" Steps (Block and Input)
        *(
            chain.from_iterable(
                [
                    # @TODO: Split this into multiple
                    param(
                        {
                            "type": manual_step_type,
                            "fields": [
                                # Text fields
                                {"text": "text", "key": "text-bare"},
                                {
                                    "text": "text",
                                    "key": "text-with-hint",
                                    "hint": "hint",
                                },
                                {
                                    "text": "text",
                                    "key": "text-with-required",
                                    "required": False,
                                },
                                {
                                    "text": "text",
                                    "key": "text-with-default",
                                    "default": "default",
                                },
                                {
                                    "text": "text",
                                    "key": "text-with-format",
                                    "format": "^$",
                                },
                                # Select fields
                                {
                                    "select": "select",
                                    "key": "select-bare",
                                    "options": [{"label": "label", "value": "value"}],
                                },
                                {
                                    "select": "select",
                                    "key": "select-with-hint",
                                    "hint": "hint",
                                    "options": [{"label": "label", "value": "value"}],
                                },
                                {
                                    "select": "select",
                                    "key": "select-with-required",
                                    "required": False,
                                    "options": [{"label": "label", "value": "value"}],
                                },
                                {
                                    "select": "select",
                                    "key": "select-with-multiple",
                                    "multiple": True,
                                    "options": [{"label": "label", "value": "value"}],
                                },
                                {
                                    "select": "select",
                                    "key": "select-with-default",
                                    "default": "value",
                                    "options": [{"label": "label", "value": "value"}],
                                },
                                {
                                    "select": "select",
                                    "key": "select-with-multiple-and-scalar-default",
                                    "multiple": True,
                                    "default": "value",
                                    "options": [{"label": "label", "value": "value"}],
                                },
                                {
                                    "select": "select",
                                    "key": "select-with-multiple-and-list-default",
                                    "multiple": True,
                                    "default": ["value"],
                                    "options": [{"label": "label", "value": "value"}],
                                },
                                {
                                    "select": "select",
                                    "key": "select-with-option-with-hint",
                                    "options": [
                                        {
                                            "label": "label",
                                            "value": "value",
                                            "hint": "hint",
                                        }
                                    ],
                                },
                                {
                                    "select": "select",
                                    "key": "select-with-option-with-required",
                                    "options": [
                                        {
                                            "label": "label",
                                            "value": "value",
                                            "required": False,
                                        }
                                    ],
                                },
                            ],
                        },
                        id=f"{manual_step_type}-fields",
                    ),
                    param(
                        {"type": manual_step_type, "prompt": "prompt"},
                        id=f"{manual_step_type}-prompt",
                    ),
                    *(
                        param(
                            {
                                "type": manual_step_type,
                                "fields": [
                                    {
                                        "select": "select",
                                        "key": "key",
                                        "options": [
                                            {"label": "label", "value": "value"}
                                        ],
                                        "multiple": value,
                                    }
                                ],
                            },
                            id=f"{manual_step_type}-select-field-multiple",
                        )
                        for value in BOOLVALS
                    ),
                    *(
                        param(
                            {
                                "type": manual_step_type,
                                "fields": [
                                    {
                                        "select": "select",
                                        "key": "key",
                                        "options": [
                                            {
                                                "label": "label",
                                                "value": "value",
                                                "required": value,
                                            }
                                        ],
                                    }
                                ],
                            },
                            id=f"{manual_step_type}-select-field-option-required",
                        )
                        for value in BOOLVALS
                    ),
                    *(
                        param(
                            {
                                "type": manual_step_type,
                                "fields": [
                                    {
                                        "select": "select",
                                        "key": "key",
                                        "options": [
                                            {"label": "label", "value": "value"}
                                        ],
                                        "required": value,
                                    }
                                ],
                            },
                            id=f"{manual_step_type}-select-field-required",
                        )
                        for value in BOOLVALS
                    ),
                    *(
                        param(
                            {
                                "type": manual_step_type,
                                "fields": [
                                    {"text": "text", "key": "key", "required": value}
                                ],
                            },
                            id=f"{manual_step_type}-text-field-required",
                        )
                        for value in BOOLVALS
                    ),
                ]
                for manual_step_type in ("block", "input")
            )
        ),
        # Trigger Step
        *(
            param(
                {"type": "trigger", "trigger": "trigger", "async": value},
                id="trigger-async",
            )
            for value in BOOLVALS
        ),
        param(
            {
                "type": "trigger",
                "trigger": "trigger",
                "build": {"branch": "branch"},
            },
            id="trigger-build-branch",
        ),
        param(
            {
                "type": "trigger",
                "trigger": "trigger",
                "build": {"commit": "commit"},
            },
            id="trigger-build-commit",
        ),
        param(
            {
                "type": "trigger",
                "trigger": "trigger",
                "build": {
                    "env": {
                        "str": "string",
                        "int": 0,
                        "bool": True,
                    }
                },
            },
            id="trigger-build-env",
        ),
        param(
            {
                "type": "trigger",
                "trigger": "trigger",
                "build": {"message": "message"},
            },
            id="trigger-build-message",
        ),
        param(
            {
                "type": "trigger",
                "trigger": "trigger",
                "build": {
                    "meta_data": {
                        "str": "string",
                        "int": 0,
                        "bool": True,
                    }
                },
            },
            id="trigger-build-meta_data",
        ),
        *(
            param(
                {"type": "trigger", "trigger": "trigger", "skip": value},
                id="trigger-skip",
            )
            for value in (True, False, "", "reason")
        ),
        *(
            param(
                {"type": "trigger", "trigger": "trigger", "soft_fail": value},
                id="trigger-soft_fail",
            )
            for value in BOOLVALS
        ),
        # Wait Step
        *(
            param(
                {"type": "wait", "continue_on_failure": value},
                id="wait-continue_on_failure",
            )
            for value in BOOLVALS
        ),
    ],
)
def test_valid_pipeline_steps(pipeline_step: dict, request: pytest.FixtureRequest):
    """
    This test tests that the pipelines we're generating are valid, type-wise.

    They don't necessarily test default values, or that we loaded the correct thing (although ideally they would).

    Eventually, we'll expand this to have these pipelines validated against the schema we generate
    (to test the schema) and against the upstream schema (as a 3-way test).
    """
    # param_id = request.node.name.removeprefix(request.node.originalname)[1:-1]
    # @TODO: make sure the directory has the same set of files as the param
    # (GENERATION_PATH / f"{param_id}.yaml").write_text(yaml.safe_dump({"steps": [pipeline_step]}))
    pipeline = BuildkitePipeline.model_load([pipeline_step])
    pipeline.model_dump()
