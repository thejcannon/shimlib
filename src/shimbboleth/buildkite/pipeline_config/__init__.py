from typing import Any, TypeAlias

from shimbboleth._model import Model, field

from ._agents import agents_from_json
from .block_step import BlockStep
from .input_step import InputStep
from .wait_step import WaitStep
from .trigger_step import TriggerStep
from .command_step import CommandStep
from ._types import rubystr
from .group_step import GroupStep
from ._notify import BuildNotifyT
from ._parse_steps import parse_steps2

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

    # @TODO: Add `json_schema_type` to the mega-list of types
    @Model._json_loader_(steps)
    @staticmethod
    def _load_steps(value: list[dict[str, Any] | str]) -> StepsT:
        return parse_steps2(value)

    @Model._json_loader_(env)
    @staticmethod
    def _load_env(
        # NB: Unlike Command steps, invalid value types aren't allowed
        value: dict[str, str | int | bool],
    ) -> dict[str, str]:
        return {k: rubystr(v) for k, v in value.items()}

    @classmethod
    def model_load(cls, value: dict[str, Any] | list[Any]):
        # NB: Handle "list of steps" as a pipeline
        if isinstance(value, list):
            return super().model_load({"steps": value})
        return super().model_load(value)
