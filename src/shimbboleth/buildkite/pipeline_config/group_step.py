from typing import Annotated, ClassVar

from pydantic import Field

from ._types import (
    SkipT,
)
from ._alias import FieldAlias
from .block_step import BlockStep, NestedBlockStep, StringBlockStep
from .input_step import InputStep, NestedInputStep, StringInputStep
from .wait_step import WaitStep, NestedWaitStep, StringWaitStep
from .trigger_step import TriggerStep, NestedTriggerStep
from .command_step import CommandStep, NestedCommandStep
from ._notify import BuildNotifyT
from ._base import BKStepBase


class GroupStep(BKStepBase, extra="forbid"):
    """
    A group step can contain various sub-steps, and display them in a single logical group on the Build page.

    https://buildkite.com/docs/pipelines/group-step
    """

    group: str | None = Field(
        description="The name to give to this group of steps",
        examples=["Tests"],
    )
    name: ClassVar = FieldAlias("group")
    label: ClassVar = FieldAlias("group")

    notify: BuildNotifyT | None = None
    skip: SkipT | None = None
    steps: Annotated[
        list[
            BlockStep
            | NestedBlockStep
            | StringBlockStep
            | InputStep
            | NestedInputStep
            | StringInputStep
            | CommandStep
            | NestedCommandStep
            | WaitStep
            | NestedWaitStep
            | StringWaitStep
            | TriggerStep
            | NestedTriggerStep
        ]
        | None,
        Field(description="A list of steps", min_length=1),
    ]
