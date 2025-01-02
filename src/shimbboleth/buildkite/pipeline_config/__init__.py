from typing import Annotated, Any, Literal

from shimbboleth._model import Model, Description, field

from ._agents import agents_from_json
from .block_step import BlockStep
from .input_step import InputStep
from .wait_step import WaitStep
from .trigger_step import TriggerStep
from .command_step import CommandStep
from ._types import env_from_json
from .group_step import GroupStep
from ._notify import BuildNotifyT
from ._nested_steps import (
    NestedWaitStep,
    NestedInputStep,
    NestedBlockStep,
    NestedCommandStep,
    NestedTriggerStep,
)

ALL_STEP_TYPES = (
    BlockStep,
    InputStep,
    CommandStep,
    WaitStep,
    TriggerStep,
    GroupStep,
)


class BuildkitePipeline(Model, extra=True):
    # @TODO: Non empty?
    steps: list[
        BlockStep | InputStep | CommandStep | WaitStep | TriggerStep | GroupStep
    ] = field()

    agents: dict[str, str] = field(
        default_factory=dict, json_converter=agents_from_json
    )
    """Query rules to target specific agents. See https://buildkite.com/docs/agent/v3/cli-start#agent-targeting"""
    env: dict[str, Any] = field(default_factory=dict, json_converter=env_from_json)
    """Environment variables for this pipeline"""
    notify: BuildNotifyT | None = None

    # @TODO: Missing cache? https://buildkite.com/docs/pipelines/hosted-agents/linux#cache-volumes

    @Model._json_converter_(steps)
    @classmethod
    def __steps__from_json(
        cls,
        value: Annotated[
            list[
                BlockStep
                | InputStep
                | CommandStep
                | WaitStep
                | TriggerStep
                | GroupStep
                | NestedBlockStep
                | NestedInputStep
                | NestedCommandStep
                | NestedWaitStep
                | NestedTriggerStep
                | Literal["block", "wait", "waiter", "input"]
            ],
            Description("A list of steps"),
        ],
        data: Any,
    ) -> list[BlockStep | InputStep | CommandStep | WaitStep | TriggerStep | GroupStep]:
        return []
