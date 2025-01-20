from typing import Any

from shimbboleth.internal.clay.jsonT import JSONObject
from shimbboleth.internal.clay.validation import InvalidValueError

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


def _parse_step(
    step: Any,
) -> BlockStep | InputStep | CommandStep | WaitStep | TriggerStep | GroupStep:
    if isinstance(step, str):
        if step in ("block", "manual"):
            return BlockStep(type=step)
        elif step == "input":
            return InputStep(type=step)
        elif step in ("command", "commands", "script"):
            return CommandStep(type=step)
        elif step == "wait" or step == "waiter":
            return WaitStep(type=step)

    elif isinstance(step, dict):
        # @TODO: Ensure keys are strings?
        for stepkey, nestedmodel, stepmodel in (
            ("block", NestedBlockStep, BlockStep),
            ("manual", NestedBlockStep, BlockStep),
            ("input", NestedInputStep, InputStep),
            ("trigger", NestedTriggerStep, TriggerStep),
            ("wait", NestedWaitStep, WaitStep),
            ("waiter", NestedWaitStep, WaitStep),
            ("command", NestedCommandStep, CommandStep),
            ("commands", NestedCommandStep, CommandStep),
            ("script", NestedCommandStep, CommandStep),
            ("group", None, GroupStep),
        ):
            if stepkey in step:
                if isinstance(step[stepkey], dict) and nestedmodel:
                    return getattr(nestedmodel.model_load(step), stepkey)
                return stepmodel.model_load(step)

            if step.get("type", None) == stepkey:
                return stepmodel.model_load(step)

    raise InvalidValueError(f"Unrecognizable step: `{step!r}`")


def parse_steps(
    steps: list[str | JSONObject],
) -> list[BlockStep | InputStep | CommandStep | WaitStep | TriggerStep | GroupStep]:
    ret = []
    for index, step in enumerate(steps):
        with InvalidValueError.context(index=index):
            ret.append(_parse_step(step))
    return ret
