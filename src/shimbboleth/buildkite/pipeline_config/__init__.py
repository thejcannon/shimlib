from typing import Any, TypeAlias, Literal, cast
from functools import lru_cache

from shimbboleth._model import Model, field
from shimbboleth._model.jsonT import JSONArray, JSONObject
from shimbboleth._model.validation import InvalidValueError

from ._agents import agents_from_json
from .block_step import BlockStep
from .input_step import InputStep
from .wait_step import WaitStep
from .trigger_step import TriggerStep
from .command_step import CommandStep
from ._types import rubystr
from .group_step import GroupStep
from ._notify import BuildNotifyT
from ._nested_steps import (
    NestedWaitStep,
    NestedInputStep,
    NestedBlockStep,
    NestedCommandStep,
    NestedTriggerStep,
)
from ._parse_steps import parse_steps
from ._base import Dependency as Dependency

ALL_STEP_TYPES = (
    BlockStep,
    InputStep,
    CommandStep,
    WaitStep,
    TriggerStep,
    GroupStep,
)

StepsT: TypeAlias = list[
    BlockStep | InputStep | CommandStep | WaitStep | TriggerStep | GroupStep
]


@lru_cache(maxsize=1)
def get_schema():
    schema = BuildkitePipeline.model_json_schema
    pipeline_schema = schema.copy()
    defs = cast(JSONObject, pipeline_schema.pop("$defs"))
    return {
        # @TODO: Draft 2020?
        # "$schema": "https://json-schema.org/draft-07/schema",
        "oneOf": [
            {"$ref": "#/$defs/pipeline"},
            {"$ref": "#/$defs/pipeline/properties/steps"},
        ],
        "$defs": {
            "pipeline": pipeline_schema,
            **defs,
        },
    }


class BuildkitePipeline(Model, extra=True):
    steps: StepsT = field()
    """A list of steps"""

    agents: dict[str, str] = field(default_factory=dict, json_loader=agents_from_json)
    """
    Query rules to target specific agents.

    See https://buildkite.com/docs/agent/v3/cli-start#agent-targeting
    """

    env: dict[str, str] = field(default_factory=dict)
    """Environment variables for this pipeline"""

    notify: BuildNotifyT = field(default_factory=list)

    # @TODO: Missing cache? https://buildkite.com/docs/pipelines/hosted-agents/linux#cache-volumes

    @classmethod
    def model_load(cls, value: JSONArray | JSONObject):
        # NB: Handle "list of steps" as a pipeline
        if isinstance(value, list):
            try:
                return super().model_load({"steps": value})
            except InvalidValueError as e:
                e.path.pop(0)  # Remove the "steps"
                raise
        return super().model_load(value)


@BuildkitePipeline._json_loader_(
    "steps",
    json_schema_type=list[
        BlockStep
        | InputStep
        | CommandStep
        | WaitStep
        | TriggerStep
        | GroupStep
        | NestedWaitStep
        | NestedInputStep
        | NestedBlockStep
        | NestedCommandStep
        | NestedTriggerStep
        | Literal[
            "block",
            "manual",
            "input",
            "command",
            "commands",
            "script",
            "wait",
            "waiter",
        ]
    ],
)
def _load_steps(value: Any) -> StepsT:
    return parse_steps(value)


@BuildkitePipeline._json_loader_("env")
def _load_env(
    # NB: Unlike Command steps, invalid value types aren't allowed
    value: dict[str, str | int | bool],
) -> dict[str, str]:
    return {k: rubystr(v) for k, v in value.items()}


@BuildkitePipeline._json_loader_("notify", json_schema_type=BuildNotifyT)
def _load_notify(value: list[Any]) -> BuildNotifyT:
    from ._notify import parse_notify

    return parse_notify(value)
