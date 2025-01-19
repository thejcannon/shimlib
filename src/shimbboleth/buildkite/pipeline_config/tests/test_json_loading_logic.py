"""
Tests for the logic of JSON loading (e.g. `FieldAlias` usage or `json_loader` semantics).

There's some overlap here with `test_schema_valid_pipelines.py`, but that's OK.
Each module tests different things.
"""

from shimbboleth.buildkite.pipeline_config import BuildkitePipeline, Dependency

from shimbboleth.buildkite.pipeline_config.command_step import (
    CommandStep,
    CommandCache,
    Plugin,
)
from shimbboleth.buildkite.pipeline_config.group_step import GroupStep
from shimbboleth.buildkite.pipeline_config.tests.conftest import StepTypeParam

import pytest

SKIP_VALS = {
    True: True,
    "true": True,
    False: False,
    "false": False,
    "": False,
    "reason": "reason",
}


def test_agents_list():
    assert BuildkitePipeline.model_load(
        {"steps": [], "agents": ["noequal", "key1=value", "key2=value=value"]}
    ).agents == {"noequal": "true", "key1": "value", "key2": "value=value"}


def test_depends_on(all_step_types: StepTypeParam):
    assert all_step_types.model_load({"depends_on": "scalar"}).depends_on == [
        Dependency(step="scalar")
    ]
    assert all_step_types.model_load({"depends_on": ["string"]}).depends_on == [
        Dependency(step="string")
    ]
    assert all_step_types.model_load({"depends_on": [{"step": "id"}]}).depends_on == [
        Dependency(step="id")
    ]

    def test_key_id_identifier(self, all_step_types):
        assert all_step_types.model_load({"key": "key"}).key == "key"
        assert all_step_types.model_load({"id": "id"}).key == "id"
        assert (
            all_step_types.model_load({"identifier": "identifier"}).key == "identifier"
        )
        assert all_step_types.model_load({"key": "key", "id": "id"}).key == "key"
        assert (
            all_step_types.model_load({"key": "key", "identifier": "identifier"}).key
            == "key"
        )
        assert (
            all_step_types.model_load({"id": "id", "identifier": "identifier"}).key
            == "id"
        )
        assert (
            all_step_types.model_load(
                {"key": "key", "id": "id", "identifier": "identifier"}
            ).key
            == "key"
        )


def test_stepname_label_name(all_substep_types):
    assert all_substep_types.model_load({"label": "label"}).label == "label"
    assert all_substep_types.model_load({"name": "name"}).label == "name"
    assert (
        all_substep_types.model_load({"label": "label", "name": "name"}).label == "name"
    )
    if all_substep_types.stepname in ("command", "trigger"):
        return

    stepname_base = {all_substep_types.stepname: all_substep_types.stepname}
    assert (
        all_substep_types.model_load(stepname_base).label == all_substep_types.stepname
    )
    assert (
        all_substep_types.model_load({**stepname_base, "label": "label"}).label
        == "label"
    )
    assert (
        all_substep_types.model_load({**stepname_base, "name": "name"}).label == "name"
    )
    assert (
        all_substep_types.model_load(
            {**stepname_base, "label": "label", "name": "name"}
        ).label
        == "name"
    )


class Test_CommandStep:
    def test_agents__list(self):
        assert CommandStep.model_load(
            {"agents": ["noequal", "key1=value", "key2=value=value"]}
        ).agents == {"noequal": "true", "key1": "value", "key2": "value=value"}

    def test_agents__dict(self):
        # @TODO: what to assert here?
        assert CommandStep.model_load(
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
        ).agents

    def test_artifact_paths(self):
        assert CommandStep.model_load({"artifact_paths": "path"}).artifact_paths == [
            "path"
        ]
        assert CommandStep.model_load({"artifact_paths": ["path"]}).artifact_paths == [
            "path"
        ]

    def test_cache(self):
        assert CommandStep.model_load({"cache": "path"}).cache == CommandCache(
            paths=["path"]
        )
        assert CommandStep.model_load({"cache": []}).cache == CommandCache(paths=[])
        assert CommandStep.model_load({"cache": ["path"]}).cache == CommandCache(
            paths=["path"]
        )

    def test_command(self):
        assert CommandStep.model_load({"command": []}).command == []
        assert CommandStep.model_load({"command": ""}).command == [""]
        assert CommandStep.model_load({"command": "command"}).command == ["command"]
        assert CommandStep.model_load(
            {"command": ["command1", "command2"]}
        ).command == [
            "command1",
            "command2",
        ]
        assert CommandStep.model_load({"command": [""]}).command == [""]
        assert CommandStep.model_load({"command": ["command"]}).command == ["command"]

    def test_plugins(self):
        assert CommandStep.model_load(
            {"plugins": ["plugin", {"plugin": None}, {"plugin": {"key": "value"}}]}
        ).plugins == [
            Plugin(spec="plugin"),
            Plugin(spec="plugin"),
            Plugin(spec="plugin", config={"key": "value"}),
        ]
        assert CommandStep.model_load(
            {"plugins": {"plugin-null": None, "pluginobj": {"key": "value"}}}
        ).plugins == [
            Plugin(spec="plugin-null"),
            Plugin(spec="pluginobj", config={"key": "value"}),
        ]

        @pytest.mark.parametrize(["input", "expected"], SKIP_VALS.items())
        def test_matrix__single_dimension__skip_bool(self, input, expected):
            assert (
                CommandStep.model_load(
                    {
                        "matrix": {
                            "setup": ["value"],
                            "adjustments": [{"with": "newvalue", "skip": input}],
                        }
                    }
                )
                .matrix.adjustments[0]  # type: ignore
                .skip
                == expected
            )

    @pytest.mark.parametrize(["input", "expected"], SKIP_VALS)
    def test_matrix__multi_dimension__skip_bool(self, input, expected):
        assert (
            CommandStep.model_load(
                {
                    "matrix": {
                        "setup": {"key1": []},
                        "adjustments": [{"with": {"key2": ""}, "skip": input}],
                    }
                }
            )
            .matrix.adjustments[0]  # type: ignore
            .skip
            == expected
        )

    @pytest.mark.parametrize(["input", "expected"], SKIP_VALS)
    def test_skip(self, input, expected):
        assert CommandStep.model_load({"skip": input}).skip == expected


class TestGroupStep:
    def test_label_name(self):
        assert (
            GroupStep.model_load({"group": "group", "label": "label"}).label == "group"
        )
        assert GroupStep.model_load({"group": "group", "name": "name"}).label == "group"
        assert (
            GroupStep.model_load(
                {"group": "group", "label": "label", "name": "name"}
            ).label
            == "group"
        )
