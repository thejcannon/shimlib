"""
Tests using valid pipelines (according to the schema).

This module is respionsible for as much testing as possible
using schema-valid pipelines. As its jsut for schema-valid pipelines,
there isn't any tests that test what happens _after_ the pipeline is loaded.
Just that it is loadable.

For logic-centric tests, see `test_json_loading_logic.py`.

This module itself tries to make it easy to define new test cases, and have
those case be tested against:
    - Model loading in Python
    - generated JSON Schema
    - Upstream JSON Schema (TODO: link)
    - Upstream Buildkite API

(I aim to to be at least as correct (if not more correct) than upstream)

NOTE: Because of the "multiple ways to test a valid pipeline" this module is a bit wonky.
    This is mostly a conflict with how I want to express the code and pytest's ability to
    declare parameterized tests. Eventually I hope to make this even easier to express
    (likely involving pytest hooks for test collection/generation).
"""

# @TODOs:
#   - Test actual nulls in the pipeline
from typing import cast

import jsonschema
from shimbboleth.buildkite.pipeline_config import (
    BuildkitePipeline,
    get_schema,
)

from shimbboleth.buildkite.pipeline_config.tests.conftest import (
    ALL_SUBSTEP_TYPE_PARAMS,
    STEP_TYPE_PARAMS,
    ALL_STEP_TYPE_PARAMS,
)

import pytest
from pytest import param


BASECAMP_CAMPFIRE_URL = "https://3.basecamp.com/1234567/integrations/qwertyuiop/buckets/1234567/chats/1234567/lines"

BOOLVALS = ("true", "false", True, False)
SKIP_VALS = (True, "true", False, "false", "", "reason")


class PipelineTestBase:
    def test_model_load(self, config):
        BuildkitePipeline.model_load(config)

    def test_generated_json_schema(self, config):
        jsonschema.validate(config, get_schema())

    def test_upstream_json_schema(self, config, pinned_bk_schema):
        # @UPSTREAM: No support for non-object pipelines
        if not isinstance(config, dict):
            config = {"steps": config}
        jsonschema.validate(config, pinned_bk_schema)

    # @TODO: What do I wanna name this? Integration? Upstream? Internet?
    @pytest.mark.integration
    def test_upstream_API(self, config):
        pass


class StepTestBase:
    def get_step(self, step, steptype_param):
        """
        Helper to get the (full) step.

        This makes it so tests can parameterize on less-than-a-full-step
        (for brevity) and we fill in the blanks.

        (Can be redefined in child classes)
        """
        return {**step, **steptype_param.dumped_default}

    def test_load_pipeline(self, step, steptype_param):
        step = self.get_step(step, steptype_param)
        BuildkitePipeline.model_load({"steps": [step]})

    def test_pipeline_valid(self, step, steptype_param):
        step = self.get_step(step, steptype_param)
        jsonschema.validate({"steps": [step]}, get_schema())

    def test_upstream_json_schema(self, step, steptype_param, pinned_bk_schema):
        jsonschema.validate({"steps": [step]}, pinned_bk_schema)

    @pytest.mark.integration
    def test_upstream_API(self, step, steptype_param):
        pass  # @TODO: Implement


@pytest.mark.parametrize(
    "config",
    [
        param([], id="empty-steps"),
        param(["block"], id="string-block"),
        param(["manual"], id="string-manual"),
        param(["command"], id="string-manual"),
        param(["commands"], id="string-commands"),
        param(["script"], id="string-script"),
        param(["input"], id="string-input"),
        param(["wait"], id="string-wait"),
        param(["waiter"], id="string-waiter"),
        param([{"block": None}], id="block-null"),
        # param([{"command": None}], id="command-null"),
        param([{"input": None}], id="input-null"),
        param([{"wait": None}], id="wait-null"),
        param(
            {
                "steps": [],
                "agents": {
                    "str": "string",
                    "int": "0",
                    "bool": "true",
                    "list": '["one", "two"]',
                    "obj": '{"key"=>"value"}',
                    "has-an-equal": "key=value",
                },
            },
            id="agents_dict",
        ),
        param(
            {
                "steps": [],
                "env": {
                    "string": "string",
                    "int": 0,
                    "bool": True,
                },
            },
            id="env_with_python_types",
        ),
        param(
            {"steps": [], "env": {"string": "string", "int": "0", "bool": "true"}},
            id="env_with_string_types",
        ),
        param(
            {
                "steps": [],
                "notify": [
                    "github_check",
                    "github_commit_status",
                    {"email": "email@example.com"},
                    {"webhook": "https://example.com"},
                    {"pagerduty_change_event": "pagerduty_change_event"},
                    {"basecamp_campfire": BASECAMP_CAMPFIRE_URL},
                    {"slack": "#general"},
                    {"slack": {"channels": ["#general"]}},
                    {"slack": {"channels": ["#general"], "message": "message"}},
                    {"github_commit_status": {"context": "context"}},
                    {"github_check": {"name": "name"}},
                ],
            },
            id="notify",
        ),
        # @TODO: Extra keys OK
    ],
)
class Test_ValidPipeline(PipelineTestBase):
    pass


@pytest.mark.parametrize("steptype_param", ALL_STEP_TYPE_PARAMS)
@pytest.mark.parametrize(
    "step",
    [
        *(
            param({"allow_dependency_failure": value}, id="allow_dependency_failrue")
            for value in BOOLVALS
        ),
        param({"if": "string"}, id="if"),
        param({"depends_on": "scalar"}, id="depends_on"),
        param({"depends_on": ["string"]}, id="depends_on"),
        param({"depends_on": [{"step": "id"}]}, id="depends_on"),
        *(
            param(
                {"depends_on": [{"step": "step_id", "allow_failure": value}]},
                id="depends_on_allow_failure",
            )
            for value in BOOLVALS
        ),
        param({"key": "key"}, id="key-id-identifier"),
        param({"id": "id"}, id="key-id-identifier"),
        param({"identifier": "identifier"}, id="key-id-identifier"),
        param({"key": "key", "id": "id"}, id="key-id-identifier"),
        param({"key": "key", "identifier": "identifier"}, id="key-id-identifier"),
        param({"id": "id", "identifier": "identifier"}, id="key-id-identifier"),
        param(
            {"key": "key", "id": "id", "identifier": "identifier"},
            id="key-id-identifier",
        ),
    ],
)
class Test_AnyStepType(StepTestBase):
    pass


@pytest.mark.parametrize("steptype_param", ALL_SUBSTEP_TYPE_PARAMS)
@pytest.mark.parametrize(
    "step",  # NB: type is `Step` or `Callable[StepTypeParam], Step]`
    [
        param({"branches": "master"}, id="branches"),
        param({"branches": ["master"]}, id="branches"),
        param({"type": lambda steptype: steptype.type}, id="type_label_name"),
        param(
            {"type": lambda steptype: steptype.type, "label": "label"},
            id="type_label_name",
        ),
        param(
            lambda steptype: {"type": steptype.type, "label": "label", "name": "name"},
            id="type_label_name",
        ),
        param({"label": "label"}, id="stepname_label_name"),
        param({"name": "name"}, id="stepname_label_name"),
        param({"label": "label", "name": "name"}, id="stepname_label_name"),
        param(
            lambda steptype: {steptype.stepname: steptype.stepname},
            id="stepname_label_name",
        ),
        param(
            lambda steptype: {
                **{steptype.stepname: steptype.stepname},
                "label": "label",
            },
            id="stepname_label_name",
        ),
        param(
            lambda steptype: {**{steptype.stepname: steptype.stepname}, "name": "name"},
            id="stepname_label_name",
        ),
        param(
            lambda steptype: {
                **{steptype.stepname: steptype.stepname},
                "label": "label",
                "name": "name",
            },
            id="stepname_label_name",
        ),
    ],
)
class Test_AnySubstepType(StepTestBase):
    def get_step(self, step, steptype_param):
        if callable(step):
            step = cast(dict, step(steptype_param))
        return {**step, **steptype_param.dumped_default}


@pytest.mark.parametrize("steptype_param", ALL_SUBSTEP_TYPE_PARAMS)
@pytest.mark.parametrize(
    "step",  # NB: type is `Callable[StepTypeParam], Step]`
    [param(lambda steptype: {steptype.stepname: steptype.ctor_defaults}, id="nested")],
)
class Test_NestedSubstep(StepTestBase):
    def get_step(self, step, steptype_param):
        return step(steptype_param)


@pytest.mark.parametrize("steptype_param", [STEP_TYPE_PARAMS["block"]])
@pytest.mark.parametrize(
    "step",
    [
        param({"blocked_state": "passed"}, id="blocked_state"),
        param({"blocked_state": "failed"}, id="blocked_state"),
        param({"blocked_state": "running"}, id="blocked_state"),
    ],
)
class Test_BlockStep(StepTestBase):
    pass


@pytest.mark.parametrize("steptype_param", [STEP_TYPE_PARAMS["command"]])
@pytest.mark.parametrize(
    "step",
    [
        *(
            param({"allow_dependency_failure": value}, id="allow_dependency_failure")
            for value in BOOLVALS
        ),
        param(
            {"agents": ["noequal", "key1=value", "key2=value=value"]}, id="agents-list"
        ),
        param(
            {
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
            id="agents-dict",
        ),
        param({"artifact_paths": "path"}, id="artifact_paths"),
        param({"artifact_paths": ["path"]}, id="artifact_paths"),
        param({"cache": "path"}, id="cache"),
        param({"cache": []}, id="cache"),
        param({"cache": ["path"]}, id="cache"),
        param(
            {
                "cache": {
                    "paths": ["path"],
                    "size": "20g",
                }
            },
            id="cache",
        ),
        param(
            {
                "cache": {
                    "paths": ["path"],
                    "name": "name",
                }
            },
            id="cache",
        ),
        param(
            {
                "cache": {
                    "paths": ["path"],
                    "size": "20g",
                    "name": "name",
                }
            },
            id="cache",
        ),
        *(
            param({"cancel_on_build_failing": value}, id="cancel_on_build_failing")
            for value in BOOLVALS
        ),
        param({"command": []}, id="command"),
        param({"command": ""}, id="command"),
        param({"command": "command"}, id="command"),
        param({"command": ["command1", "command2"]}, id="command"),
        param({"command": [""]}, id="command"),
        param({"command": ["command"]}, id="command"),
        param({"concurrency": 1, "concurrency_group": "group1"}, id="concurrency"),
        param(
            {
                "concurrency": 1,
                "concurrency_group": "group2",
                "concurrency_method": "ordered",
            },
            id="concurrency",
        ),
        param(
            {
                "concurrency": 1,
                "concurrency_group": "group3",
                "concurrency_method": "eager",
            },
            id="concurrency",
        ),
        param(
            {
                "env": {
                    "string": "string",
                    "int": 0,
                    "bool": True,
                    "list": [],
                    "obj": {"key": "value"},
                }
            },
            id="env",
        ),
        param({"env": {"string": "string", "int": "0", "bool": "true"}}, id="env"),
        param({"matrix": ["string", 0, True]}, id="matrix"),
        param({"matrix": {"setup": ["value"]}}, id="matrix"),
        param(
            {"matrix": {"setup": ["value"], "adjustments": [{"with": "newvalue"}]}},
            id="matrix",
        ),
        param(
            {
                "matrix": {
                    "setup": ["value"],
                    "adjustments": [{"with": "newvalue", "soft_fail": True}],
                }
            },
            id="matrix",
        ),
        *(
            param(
                {
                    "matrix": {
                        "setup": ["value"],
                        "adjustments": [{"with": "newvalue", "skip": input}],
                    }
                },
                id=f"matrix{input}",
            )
            for input in SKIP_VALS
        ),
        param(
            {"matrix": {"setup": {"key1": ["value"], "key2": ["value"]}}}, id="matrix"
        ),
        param({"matrix": {"setup": {"key1": []}, "adjustments": []}}, id="matrix"),
        param(
            {
                "matrix": {
                    "setup": {"key": ["value"]},
                    "adjustments": [
                        {
                            "with": {"key": "newvalue"},
                            "soft_fail": [{"exit_status": "*"}, {"exit_status": -1}],
                        }
                    ],
                }
            },
            id="matrix",
        ),
        *(
            param(
                {
                    "matrix": {
                        "setup": {"key1": []},
                        "adjustments": [{"with": {"key2": ""}, "skip": input}],
                    }
                },
                id="matrix",
            )
            for input in SKIP_VALS
        ),
        param(
            {
                "notify": [
                    "github_check",
                    "github_commit_status",
                    {
                        "basecamp_campfire": "https://3.basecamp.com/1234567/integrations/qwertyuiop/buckets/1234567/chats/1234567/lines"
                    },
                    {"slack": "#general"},
                    {"slack": {"channels": ["#general"]}},
                    {"slack": {"channels": ["#general"], "message": "message"}},
                    {"github_commit_status": {"context": "context"}},
                    {"github_check": {"name": "name"}},
                ]
            },
            id="notify",
        ),
        param({"parallelism": 1}, id="parallelism"),
        param(
            {"plugins": ["plugin", {"plugin": None}, {"plugin": {"key": "value"}}]},
            id="plugins",
        ),
        param(
            {"plugins": {"plugin-null": None, "pluginobj": {"key": "value"}}},
            id="plugins",
        ),
        param({"priority": 1}, id="priority"),
        *(
            param({"retry": {"automatic": value}}, id="retry__automatic")
            for value in BOOLVALS
        ),
        param(
            {"retry": {"automatic": {"exit_status": 1}}},
            id="retry__automatic_exit_status",
        ),
        param(
            {"retry": {"automatic": {"exit_status": "*"}}},
            id="retry__automatic_exit_status",
        ),
        param(
            {"retry": {"automatic": {"exit_status": [1, 2]}}},
            id="retry__automatic_exit_status",
        ),
        param({"retry": {"automatic": [{"limit": 5}]}}, id="retry__automatic_limit"),
        param(
            {"retry": {"automatic": [{"signal": "signal"}]}},
            id="retry__automatic_signal",
        ),
        param(
            {
                "retry": {
                    "automatic": [
                        {"signal_reason": "*"},
                        {"signal_reason": "none"},
                        {"signal_reason": "agent_refused"},
                        {"signal_reason": "agent_stop"},
                        {"signal_reason": "cancel"},
                        {"signal_reason": "process_run_error"},
                        {"signal_reason": "signature_rejected"},
                    ]
                }
            },
            id="retry__automatic_signal_reasons",
        ),
        *(
            param({"retry": {"manual": value}}, id=f"retry_manual_{value}")
            for value in BOOLVALS
        ),
        *(
            param(
                {"retry": {"manual": {"allowed": value}}},
                id=f"retry_manual_allowed_{value}",
            )
            for value in BOOLVALS
        ),
        *(
            param(
                {"retry": {"manual": {"permit_on_passed": value}}},
                id=f"retry_manual_permit_on_passed_{value}",
            )
            for value in BOOLVALS
        ),
        param(
            {"retry": {"manual": {"reason": "reason", "allowed": True}}},
            id="retry_manual_reason",
        ),
        param({"signature": {}}, id="signature_empty"),
        param({"signature": {"algorithm": "sha256"}}, id="signature_algorithm"),
        param(
            {"signature": {"signed_fields": ["field1"]}}, id="signature_signed_fields"
        ),
        param({"signature": {"value": "value"}}, id="signature_value"),
        *(param({"skip": input}, id=f"skip_{input}") for input in SKIP_VALS),
        *(param({"soft_fail": value}, id=f"soft_fail_{value}") for value in BOOLVALS),
        param({"soft_fail": []}, id="soft_fail_empty_list"),
        param({"soft_fail": [{"exit_status": "*"}]}, id="soft_fail_exit_status_any"),
        param({"soft_fail": [{"exit_status": 1}]}, id="soft_fail_exit_status_single"),
        param(
            {"soft_fail": [{"exit_status": 1}, {"exit_status": -1}]},
            id="soft_fail_exit_status_multiple",
        ),
        param(
            {"soft_fail": [{"exit_status": "*"}, {"exit_status": 1}]},
            id="soft_fail_exit_status_mixed",
        ),
        param({"timeout_in_minutes": 1}, id="timeout_in_minutes"),
    ],
)
class Test_CommandStep(StepTestBase):
    pass


@pytest.mark.parametrize("steptype_param", [STEP_TYPE_PARAMS["input"]])
@pytest.mark.parametrize("step", [])
class Test_InputStep(StepTestBase):
    pass


@pytest.mark.parametrize(
    "steptype_param", [STEP_TYPE_PARAMS["block"], STEP_TYPE_PARAMS["input"]]
)
@pytest.mark.parametrize(
    "step",
    [param({"prompt": "prompt"}, id="prompt")],
)
class Test_ManualStep(StepTestBase):
    pass


@pytest.mark.parametrize(
    "steptype_param", [STEP_TYPE_PARAMS["block"], STEP_TYPE_PARAMS["input"]]
)
@pytest.mark.parametrize(
    "step",  # NB: `step` is a misnomer, its actually the field's extra keys/values
    [
        param({}, id="bare"),
        param({"default": "default"}, id="default"),
        *[param({"multiple": value}, id="multiple") for value in BOOLVALS],
        param({"multiple": True, "default": "default"}, id="multiple_default"),
        param({"multiple": True, "default": ["default"]}, id="multiple_default"),
    ],
)
class Test_ManualStep__SelectField(StepTestBase):
    def get_step(self, step, steptype_param):
        return {
            "type": steptype_param.stepname,
            "fields": [
                {
                    "select": "select",
                    "key": "key",
                    **step,
                    "options": [{"label": "label", "value": "value"}],
                }
            ],
        }


@pytest.mark.parametrize(
    "steptype_param", [STEP_TYPE_PARAMS["block"], STEP_TYPE_PARAMS["input"]]
)
@pytest.mark.parametrize(
    "step",  # NB: `step` is a misnomer, its actually the field's' option's extra keys/values.
    [
        param({}, id="bare"),
        param({"hint": "hint"}, id="hint"),
        *[param({"required": value}, id="required") for value in BOOLVALS],
    ],
)
class Test_ManualStep__SelectField__Option(StepTestBase):
    def get_step(self, step, steptype_param):
        return {
            "type": steptype_param.stepname,
            "fields": [
                {
                    "select": "select",
                    "key": "key",
                    "options": [{"label": "label", "value": "value", **step}],
                }
            ],
        }


@pytest.mark.parametrize(
    "steptype_param", [STEP_TYPE_PARAMS["block"], STEP_TYPE_PARAMS["input"]]
)
@pytest.mark.parametrize(
    "step",  # NB: `step` is a misnomer, its actually the field's' extra keys/values.
    [
        param({}, id="bare"),
        param({"hint": "hint"}, id="hint"),
        param({"default": "default"}, id="default"),
        param({"format": "^$"}, id="format"),
        *[param({"required": value}, id="required") for value in BOOLVALS],
    ],
)
class Test_ManualStep__TextField(StepTestBase):
    def get_step(self, step, steptype_param):
        return {
            "type": steptype_param.stepname,
            "fields": [{"text": "text", "key": "key", **step}],
        }


@pytest.mark.parametrize("steptype_param", [STEP_TYPE_PARAMS["trigger"]])
@pytest.mark.parametrize(
    "step",
    [
        *(param({"async": value}, id="async") for value in BOOLVALS),
        param({"build": {"branch": "branch"}}, id="build_branch"),
        param({"build": {"commit": "commit"}}, id="build_commit"),
        param(
            {
                "build": {
                    "env": {
                        "str": "string",
                        "int": 0,
                        "bool": True,
                    }
                },
            },
            id="build_env",
        ),
        param(
            {
                "build": {"message": "message"},
            },
            id="build_message",
        ),
        param(
            {
                "build": {
                    "meta_data": {
                        "str": "string",
                        "int": 0,
                        "bool": True,
                    }
                },
            },
            id="build_meta_data",
        ),
        *(param({"skip": input}, id="skip") for input in SKIP_VALS),
        *(param({"soft_fail": value}, id="soft_fail") for value in BOOLVALS),
    ],
)
class Test_TriggerStep(StepTestBase):
    pass


@pytest.mark.parametrize("steptype_param", [STEP_TYPE_PARAMS["wait"]])
@pytest.mark.parametrize(
    "step",
    [
        *(
            param({"continue_on_failure": value}, id="continue_on_failure")
            for value in BOOLVALS
        ),
    ],
)
class Test_WaitStep(StepTestBase):
    pass


@pytest.mark.parametrize("steptype_param", [STEP_TYPE_PARAMS["group"]])
@pytest.mark.parametrize(
    "step",
    [
        param({"group": "group", "label": "label"}, id="label_name"),
        param({"group": "group", "name": "name"}, id="label_name"),
        param({"group": "group", "label": "label", "name": "name"}, id="label_name"),
        param(
            {
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
            id="notify",
        ),
        *[param({"skip": input}, id="skip") for input in SKIP_VALS],
    ],
)
class Test_GroupStep(StepTestBase):
    pass
