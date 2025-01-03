from .block_step import BlockStep
from .input_step import InputStep
from .wait_step import WaitStep
from .trigger_step import TriggerStep
from .command_step import CommandStep
from .group_step import GroupStep
from ._nested_steps import (
    NestedWaitStep,
    NestedInputStep,
    NestedBlockStep,
    NestedCommandStep,
    NestedTriggerStep,
)
from typing import Literal


def parse_steps(
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
