from typing import Any, Literal

from shimbboleth._model import Model, field

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
    # @TODO: (Why does BK allow this to be empty? lol)
    #   (make a test case)
    steps: list[
        BlockStep | InputStep | CommandStep | WaitStep | TriggerStep | GroupStep
    ] = field()

    agents: dict[str, str] = field(
        default_factory=dict, json_converter=agents_from_json
    )
    """Query rules to target specific agents. See https://buildkite.com/docs/agent/v3/cli-start#agent-targeting"""

    env: dict[str, str | int | bool] = field(
        default_factory=dict, json_converter=env_from_json
    )
    """Environment variables for this pipeline"""

    notify: BuildNotifyT = field(default_factory=list)

    # @TODO: Missing cache? https://buildkite.com/docs/pipelines/hosted-agents/linux#cache-volumes

    @Model._json_converter_(steps)
    @staticmethod
    def __steps__from_json(
        value: list[
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
            | Literal["block", "manual"]
            | Literal["input"]
            | Literal["command", "commands", "script"]
            | Literal["wait", "waiter"]
        ],
    ) -> list[BlockStep | InputStep | CommandStep | WaitStep | TriggerStep | GroupStep]:
        ret = []
        for step in value:
            if isinstance(
                step,
                (BlockStep, InputStep, CommandStep, WaitStep, TriggerStep, GroupStep),
            ):
                ret.append(step)
            elif isinstance(step, NestedBlockStep):
                ret.append(step.block)
            elif isinstance(step, NestedInputStep):
                ret.append(step.input)
            elif isinstance(step, NestedCommandStep):
                ret.append(step.command)
            elif isinstance(step, NestedWaitStep):
                ret.append(step.wait)
            elif isinstance(step, NestedTriggerStep):
                ret.append(step.trigger)
            elif step in ("block", "manual"):
                ret.append(BlockStep(type=step))
            elif step == "input":
                ret.append(InputStep(type=step))
            elif step in ("command", "commands", "script"):
                ret.append(CommandStep(type=step))
            elif step == "wait" or step == "waiter":
                ret.append(WaitStep(type=step))
        return ret
