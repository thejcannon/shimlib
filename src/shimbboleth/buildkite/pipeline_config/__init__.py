from typing import Annotated, Any

from pydantic import BaseModel, Field, Discriminator, Tag

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


def get_step_tag(v: Any) -> str | None:
    # @TODO: Support models as well (serialization)
    if isinstance(v, dict):
        if step_type := v.get("type"):
            return step_type
        if "group" in v:
            return "group"
        for step_type in ["block", "input", "command", "wait", "trigger"]:
            if step_type in v:
                # @TODO: ambiguous? E.g. `block: ~`
                return (
                    f"nested-{step_type}"
                    if isinstance(v[step_type], dict)
                    else step_type
                )
        if "commands" in v:
            return "nested-command" if isinstance(v[step_type], dict) else "command"
        if "waiter" in v:
            return "nested-wait" if isinstance(v[step_type], dict) else "wait"
        if "script" in v:
            return "nested-command"
        # @TODO: What if label + some unique field?!

    elif isinstance(v, str):
        v = {"waiter": "wait", "commands": "command", "script": "command"}.get(v, v)
        return f"string-{v}"

    return None


class BuildkitePipeline(BaseModel, extra="allow"):
    # @TODO: Canonicalize
    steps: Annotated[
        list[
            Annotated[
                Annotated[BlockStep, Tag("block")]
                | Annotated[NestedBlockStep, Tag("nested-block")]
                | Annotated[StringBlockStep, Tag("string-block")]
                | Annotated[InputStep, Tag("input")]
                | Annotated[NestedInputStep, Tag("nested-input")]
                | Annotated[StringInputStep, Tag("string-input")]
                | Annotated[CommandStep, Tag("command")]
                | Annotated[NestedCommandStep, Tag("nested-command")]
                | Annotated[WaitStep, Tag("wait")]
                | Annotated[NestedWaitStep, Tag("nested-wait")]
                | Annotated[StringWaitStep, Tag("string-wait")]
                | Annotated[TriggerStep, Tag("trigger")]
                | Annotated[NestedTriggerStep, Tag("nested-trigger")]
                | Annotated[GroupStep, Tag("group")],
                Discriminator(get_step_tag),
            ]
        ],
        Field(description="A list of steps"),
    ]

    agents: AgentsT | None = None
    env: EnvT | None = None
    notify: BuildNotifyT | None = None
    # @TODO: Missing cache? https://buildkite.com/docs/pipelines/hosted-agents/linux#cache-volumes
