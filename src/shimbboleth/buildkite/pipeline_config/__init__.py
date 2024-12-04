from typing import Annotated

from pydantic import BaseModel, Field

from ._types import EnvT
from ._agents import AgentsT
from .block_step import BlockStep, NestedBlockStep, StringBlockStep
from .input_step import InputStep, NestedInputStep, StringInputStep
from .wait_step import WaitStep, NestedWaitStep, StringWaitStep
from .trigger_step import TriggerStep, NestedTriggerStep
from .command_step import CommandStep, NestedCommandStep
from .group_step import GroupStep
from ._notify import BuildNotifyT

ALL_STEP_TYPES = (
    BlockStep,
    InputStep,
    CommandStep,
    WaitStep,
    TriggerStep,
    GroupStep,
)


class BuildkitePipeline(BaseModel):
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
            | GroupStep
        ],
        Field(description="A list of steps"),
    ]

    agents: AgentsT | None = None
    env: EnvT | None = None
    notify: BuildNotifyT | None = None
