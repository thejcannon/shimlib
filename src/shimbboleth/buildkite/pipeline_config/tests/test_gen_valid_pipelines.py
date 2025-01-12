"""
@TODO: ...
"""

from shimbboleth.buildkite.pipeline_config import BuildkitePipeline, Dependency

from shimbboleth.buildkite.pipeline_config.block_step import BlockStep
from shimbboleth.buildkite.pipeline_config.command_step import CommandStep
from shimbboleth.buildkite.pipeline_config.input_step import InputStep
from shimbboleth.buildkite.pipeline_config.trigger_step import TriggerStep
from shimbboleth.buildkite.pipeline_config.wait_step import WaitStep
from shimbboleth.buildkite.pipeline_config.group_step import GroupStep
from shimbboleth.buildkite.pipeline_config.tests.conftest import STEP_TYPE_PARAMS

import pytest


BASECAMP_CAMPFIRE_URL = "https://3.basecamp.com/1234567/integrations/qwertyuiop/buckets/1234567/chats/1234567/lines"

BOOLVALS = ("true", "false", True, False)


class _ValidPipelineBase:
    # @TODO: Eventually, compare this against the generated schema
    #   and also against the upstream schema
    #   and also against the API
    def load_step(self, step, steptype_param=None):
        if steptype_param is not None:
            step = {**step, **steptype_param.dumped_default}

        pipeline = BuildkitePipeline.model_load([step])
        assert pipeline == BuildkitePipeline.model_load({"steps": [step]})
        # @TODO: Group step too
        return pipeline.steps[0]


@pytest.mark.parametrize(
    "steptype_param",
    [
        pytest.param(steptype_param, id=steptype_param.stepname)
        for steptype_param in STEP_TYPE_PARAMS.values()
    ],
)
class TestValidPipeline_AnyStepType(_ValidPipelineBase):
    @pytest.mark.parametrize("value", BOOLVALS)
    def test_allow_dependency_failure(self, value, steptype_param):
        self.load_step(
            {"allow_dependency_failure": value},
            steptype_param,
        )

    def test_depends_on(self, steptype_param):
        assert self.load_step({"depends_on": "scalar"}, steptype_param).depends_on == [
            Dependency(step="scalar")
        ]
        assert self.load_step(
            {"depends_on": ["string"]}, steptype_param
        ).depends_on == [Dependency(step="string")]
        assert self.load_step(
            {"depends_on": [{"step": "id"}]}, steptype_param
        ).depends_on == [Dependency(step="id")]

    @pytest.mark.parametrize("value", BOOLVALS)
    def test_depends_on__allow_failure__bool(self, value, steptype_param):
        self.load_step(
            {"depends_on": [{"step": "step_id", "allow_failure": value}]},
            steptype_param,
        )

    def test_key_id_identifier(self, steptype_param):
        assert self.load_step({"key": "key"}, steptype_param).key == "key"
        assert self.load_step({"id": "id"}, steptype_param).key == "id"
        assert (
            self.load_step({"identifier": "identifier"}, steptype_param).key
            == "identifier"
        )
        assert self.load_step({"key": "key", "id": "id"}, steptype_param).key == "key"
        assert (
            self.load_step(
                {"key": "key", "identifier": "identifier"}, steptype_param
            ).key
            == "key"
        )
        assert (
            self.load_step({"id": "id", "identifier": "identifier"}, steptype_param).key
            == "id"
        )
        assert (
            self.load_step(
                {"key": "key", "id": "id", "identifier": "identifier"}, steptype_param
            ).key
            == "key"
        )

    def test_if(self, steptype_param):
        self.load_step({"if": "string"}, steptype_param)


@pytest.mark.parametrize(
    "steptype_param",
    [
        pytest.param(steptype_param, id=steptype_param.stepname)
        for steptype_param in STEP_TYPE_PARAMS.values()
        if steptype_param.stepname != "group"
    ],
)
class TestValidPipeline_AnySubstepType(_ValidPipelineBase):
    @pytest.mark.parametrize("value", ("master", ["master"]))
    def test_branches(self, value, steptype_param):
        self.load_step({"branches": value}, steptype_param)

    def test_type_label_name(self, steptype_param):
        self.load_step({"type": steptype_param.type}, steptype_param)
        self.load_step({"type": steptype_param.type, "label": "label"}, steptype_param)
        self.load_step(
            {"type": steptype_param.type, "label": "label", "name": "name"},
            steptype_param,
        )

    def test_stepname_label_name(self, steptype_param):
        assert self.load_step({"label": "label"}, steptype_param).label == "label"
        assert self.load_step({"name": "name"}, steptype_param).label == "name"
        assert (
            self.load_step({"label": "label", "name": "name"}, steptype_param).label
            == "name"
        )
        if steptype_param.stepname in ("command", "trigger"):
            return

        stepname_base = {steptype_param.stepname: steptype_param.stepname}
        assert (
            self.load_step(stepname_base, steptype_param).label
            == steptype_param.stepname
        )
        assert (
            self.load_step({**stepname_base, "label": "label"}, steptype_param).label
            == "label"
        )
        assert (
            self.load_step({**stepname_base, "name": "name"}, steptype_param).label
            == "name"
        )
        assert (
            self.load_step(
                {**stepname_base, "label": "label", "name": "name"}, steptype_param
            ).label
            == "name"
        )

    def test_nested(self, steptype_param):
        self.load_step(
            {steptype_param.stepname: steptype_param.ctor_defaults},
        )


class TestValidPipeline_BlockStep(_ValidPipelineBase):
    def load_step(self, step, steptype_param=None) -> BlockStep:
        step = super().load_step(step)
        assert isinstance(step, BlockStep)
        return step

    def test_null(self):
        self.load_step({"block": None})

    def test_string(self):
        self.load_step("block")
        assert isinstance(self.load_step("manual"), BlockStep)

    @pytest.mark.parametrize("blocked_state", ["passed", "failed", "running"])
    def test_blocked_state(self, blocked_state):
        self.load_step({"block": {"blocked_state": blocked_state}})


class TestValidPipeline_CommandStep(_ValidPipelineBase):
    def load_step(self, step, steptype_param=None) -> CommandStep:
        if isinstance(step, dict):
            step = super().load_step(step, STEP_TYPE_PARAMS["command"])
        else:
            step = super().load_step(step)
        assert isinstance(step, CommandStep)
        return step

    def test_string(self):
        self.load_step("command")
        self.load_step("commands")
        self.load_step("script")

    @pytest.mark.parametrize("value", BOOLVALS)
    def test_command_allow_dependency_failure(self, value):
        self.load_step({"allow_dependency_failure": value})

    def test_command_agents(self):
        assert self.load_step(
            {"agents": ["noequal", "key1=value", "key2=value=value"]}
        ).agents == {"noequal": "true", "key1": "value", "key2": "value=value"}
        self.load_step(
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
            }
        )
        self.load_step(
            {"agents": {"noequal": "true", "key1": "value", "key2": "value=value"}}
        )
        self.load_step(
            {
                "agents": {
                    "str": "string",
                    "int": "0",
                    "bool": "true",
                    "list": '["one", "two"]',
                    "obj": '{"key"=>"value"}',
                    "has-an-equal": "key=value",
                },
            }
        )

    def test_command_artifact_paths(self):
        self.load_step({"artifact_paths": "scalar"})
        self.load_step({"artifact_paths": ["path1"]})
        self.load_step({"artifact_paths": ["scalar"]})

    def test_command_cache(self):
        self.load_step({"cache": "path"})
        self.load_step({"cache": []})
        self.load_step({"cache": ["path"]})
        self.load_step(
            {
                "cache": {
                    "paths": ["path"],
                    "size": "20g",
                }
            }
        )
        self.load_step(
            {
                "cache": {
                    "paths": ["path"],
                    "name": "name",
                }
            }
        )
        self.load_step(
            {
                "cache": {
                    "paths": ["path"],
                    "size": "20g",
                    "name": "name",
                }
            }
        )

    @pytest.mark.parametrize("value", BOOLVALS)
    def test_command_cancel_on_build_failing(self, value):
        self.load_step({"cancel_on_build_failing": value})

    def test_command_command(self):
        assert self.load_step({"command": []}).command == []
        self.load_step({"command": ""})
        self.load_step({"command": "command"})
        self.load_step({"command": ["command1", "command2"]})
        self.load_step({"command": [""]})
        self.load_step({"command": ["command"]})

    def test_command_concurrency(self):
        self.load_step({"concurrency": 1, "concurrency_group": "group1"})
        self.load_step(
            {
                "concurrency": 1,
                "concurrency_group": "group2",
                "concurrency_method": "ordered",
            }
        )
        self.load_step(
            {
                "concurrency": 1,
                "concurrency_group": "group3",
                "concurrency_method": "eager",
            }
        )

    def test_command_env(self):
        self.load_step(
            {
                "env": {
                    "string": "string",
                    "int": 0,
                    "bool": True,
                    "list": [],
                    "obj": {"key": "value"},
                }
            }
        )
        self.load_step({"env": {"string": "string", "int": "0", "bool": "true"}})

    def test_command_matrix__simple_array(self):
        self.load_step({"matrix": ["string", 0, True]})

    def test_command_matrix__single_dimension(self):
        self.load_step({"matrix": {"setup": ["value"]}})
        self.load_step(
            {"matrix": {"setup": ["value"], "adjustments": [{"with": "newvalue"}]}}
        )
        self.load_step(
            {
                "matrix": {
                    "setup": ["value"],
                    "adjustments": [{"with": "newvalue", "soft_fail": True}],
                }
            }
        )

    @pytest.mark.parametrize("value", BOOLVALS)
    def test_command_matrix__single_dimension__skip_bool(self, value):
        self.load_step(
            {
                "matrix": {
                    "setup": ["value"],
                    "adjustments": [{"with": "newvalue", "skip": value}],
                }
            }
        )

    def test_command_matrix__multi_dimension(self):
        self.load_step({"matrix": {"setup": {"key1": ["value"], "key2": ["value"]}}})
        self.load_step(
            {
                "matrix": {
                    "setup": ["value"],
                    "adjustments": [
                        {
                            "with": "newvalue",
                            "soft_fail": [{"exit_status": "*"}, {"exit_status": -1}],
                        }
                    ],
                }
            }
        )

    @pytest.mark.parametrize("value", BOOLVALS)
    def test_command_matrix__multi_dimension__skip_bool(self, value):
        self.load_step(
            {
                "matrix": {
                    "setup": {"key1": []},
                    "adjustments": [{"with": {"key2": []}, "skip": value}],
                }
            }
        )

    def test_command_notify(self):
        self.load_step(
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
            }
        )

    def test_command_parallelism(self):
        self.load_step({"parallelism": 1})

    def test_command_plugins(self):
        self.load_step(
            {"plugins": ["plugin", {"plugin": None}, {"plugin": {"key": "value"}}]}
        )
        self.load_step(
            {"plugins": {"plugin-null": None, "pluginobj": {"key": "value"}}}
        )

    def test_command_priority(self):
        self.load_step({"priority": 1})

    @pytest.mark.parametrize("value", BOOLVALS)
    def test_command_retry__automatic_bool(self, value):
        self.load_step({"retry": {"automatic": value}})

    def test_command_retry__automatic(self):
        self.load_step({"retry": {"automatic": {"exit_status": 1}}})
        self.load_step({"retry": {"automatic": {"exit_status": "*"}}})
        self.load_step({"retry": {"automatic": {"exit_status": [1, 2]}}})
        self.load_step({"retry": {"automatic": [{"limit": 5}]}})
        self.load_step({"retry": {"automatic": [{"signal": "signal"}]}})
        self.load_step(
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
            }
        )

    @pytest.mark.parametrize("value", BOOLVALS)
    def test_command_retry__manual_bool(self, value):
        self.load_step({"retry": {"manual": value}})

    @pytest.mark.parametrize("value", BOOLVALS)
    def test_command_retry__manual_allowed(self, value):
        self.load_step({"retry": {"manual": {"allowed": value}}})

    @pytest.mark.parametrize("value", BOOLVALS)
    def test_command_retry__manual_permit_on_passed(self, value):
        self.load_step({"retry": {"manual": {"permit_on_passed": value}}})

    def test_command_retry__manual(self):
        self.load_step({"retry": {"manual": {"reason": "reason", "allowed": True}}})

    def test_command_signature(self):
        self.load_step({"signature": {}})
        self.load_step({"signature": {"algorithm": "sha256"}})
        self.load_step({"signature": {"signed_fields": ["field1"]}})
        self.load_step({"signature": {"value": "value"}})

    @pytest.mark.parametrize("value", (True, False, "", "reason"))
    def test_command_skip(self, value):
        self.load_step({"skip": value})

    @pytest.mark.parametrize("value", BOOLVALS)
    def test_command_soft_fail__bool(self, value):
        self.load_step({"soft_fail": value})

    def test_command_soft_fail(self):
        self.load_step({"soft_fail": []})
        self.load_step({"soft_fail": [{"exit_status": "*"}]})
        self.load_step({"soft_fail": [{"exit_status": 1}]})
        self.load_step({"soft_fail": [{"exit_status": 1}, {"exit_status": -1}]})
        self.load_step({"soft_fail": [{"exit_status": "*"}, {"exit_status": 1}]})

    def test_command_timeout_in_minutes(self):
        self.load_step({"timeout_in_minutes": 1})


class TestValidPipeline_InputStep(_ValidPipelineBase):
    def load_step(self, step, steptype_param=None) -> InputStep:
        step = super().load_step(step)
        assert isinstance(step, InputStep)
        return step

    def test_null(self):
        self.load_step({"input": None})

    def test_string(self):
        self.load_step("input")


@pytest.mark.parametrize("step_type", ["block", "input"])
class TestValidPipeline_ManualStep(_ValidPipelineBase):
    def _load_step_with_text_field(self, step_type, extra={}):
        return self.load_step(
            {step_type: step_type, "fields": [{"text": "text", "key": "key", **extra}]}
        )

    def _load_step_with_select_field(self, step_type, extra={}):
        return self.load_step(
            {
                step_type: step_type,
                "fields": [
                    {
                        "select": "select",
                        "key": "key",
                        **extra,
                        "options": [{"label": "label", "value": "value"}],
                    }
                ],
            }
        )

    def test_fields_text(self, step_type):
        self._load_step_with_text_field(step_type)
        self._load_step_with_text_field(step_type, {"hint": "hint"})
        self._load_step_with_text_field(step_type, {"default": "default"})
        self._load_step_with_text_field(step_type, {"format": "^$"})

    @pytest.mark.parametrize("value", BOOLVALS)
    def test_fields_text_required(self, step_type, value):
        self._load_step_with_text_field(step_type, {"required": value})

    def test_fields_select(self, step_type):
        self._load_step_with_select_field(step_type)
        self._load_step_with_select_field(step_type, {"hint": "hint"})
        self._load_step_with_select_field(step_type, {"default": "default"})
        self._load_step_with_select_field(
            step_type, {"multiple": True, "default": "default"}
        )
        self._load_step_with_select_field(
            step_type, {"multiple": True, "default": ["default"]}
        )
        self._load_step_with_select_field(
            step_type,
            {"options": [{"label": "label", "value": "value", "hint": "hint"}]},
        )

    @pytest.mark.parametrize("value", BOOLVALS)
    def test_fields_select_multiple(self, step_type, value):
        self._load_step_with_select_field(step_type, {"multiple": value})

    @pytest.mark.parametrize("value", BOOLVALS)
    def test_fields_select_option_required(self, step_type, value):
        self._load_step_with_select_field(
            step_type,
            {"options": [{"label": "label", "value": "value", "required": value}]},
        )

    @pytest.mark.parametrize("value", BOOLVALS)
    def test_fields_select_required(self, step_type, value):
        self.load_step(
            {
                step_type: {
                    "fields": [
                        {
                            "select": "select",
                            "key": "key",
                            "options": [{"label": "label", "value": "value"}],
                            "required": value,
                        }
                    ],
                }
            }
        )

    def test_prompt(self, step_type):
        self.load_step({"type": step_type, "prompt": "prompt"})


class TestValidPipeline_TriggerStep(_ValidPipelineBase):
    def load_step(self, step, steptype_param=None) -> TriggerStep:
        step = super().load_step(step, STEP_TYPE_PARAMS["trigger"])
        assert isinstance(step, TriggerStep)
        return step

    @pytest.mark.parametrize("value", BOOLVALS)
    def test_async(self, value):
        self.load_step({"async": value})

    def test_build_branch(self):
        self.load_step({"build": {"branch": "branch"}})

    def test_build_commit(self):
        self.load_step({"build": {"commit": "commit"}})

    def test_build_env(self):
        self.load_step(
            {
                "build": {
                    "env": {
                        "str": "string",
                        "int": 0,
                        "bool": True,
                    }
                },
            }
        )

    def test_build_message(self):
        self.load_step(
            {
                "build": {"message": "message"},
            }
        )

    def test_build_meta_data(self):
        self.load_step(
            {
                "build": {
                    "meta_data": {
                        "str": "string",
                        "int": 0,
                        "bool": True,
                    }
                },
            }
        )

    @pytest.mark.parametrize("value", (True, False, "", "reason"))
    def test_skip(self, value):
        self.load_step({"skip": value})

    @pytest.mark.parametrize("value", BOOLVALS)
    def test_soft_fail(self, value):
        self.load_step({"soft_fail": value})


class TestValidPipeline_WaitStep(_ValidPipelineBase):
    def load_step(self, step, steptype_param=None) -> WaitStep:
        step = super().load_step(step)
        assert isinstance(step, WaitStep)
        return step

    def test_null(self):
        self.load_step({"wait": None})

    def test_string(self):
        self.load_step("wait")
        self.load_step("waiter")

    @pytest.mark.parametrize("value", BOOLVALS)
    def test_continue_on_failure(self, value):
        self.load_step({"wait": {"continue_on_failure": value}})


class TestValidPipeline_GroupStep(_ValidPipelineBase):
    def load_step(self, step, steptype_param=None) -> GroupStep:
        step = super().load_step(step, STEP_TYPE_PARAMS["group"])
        assert isinstance(step, GroupStep)
        return step

    def test_label_name(self):
        assert self.load_step({"group": "group", "label": "label"}).label == "group"
        assert self.load_step({"group": "group", "name": "name"}).label == "group"
        assert (
            self.load_step({"group": "group", "label": "label", "name": "name"}).label
            == "group"
        )

    def test_group_notify(self):
        self.load_step(
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
            }
        )

    @pytest.mark.parametrize("value", (True, False, "", "reason"))
    def test_group_skip(self, value):
        self.load_step({"skip": value})
