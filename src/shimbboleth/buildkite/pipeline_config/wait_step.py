from typing import ClassVar, Literal, Annotated
from typing_extensions import TypeAliasType

from pydantic import BaseModel, Field

from shimbboleth.buildkite.pipeline_config._types import LabelT

from ._base import BKStepBase
from ._alias import FieldAlias, FieldAliasSupport


class WaitStep(BKStepBase, extra="forbid"):
    """
    A wait step waits for all previous steps to have successfully completed before allowing following jobs to continue.

    https://buildkite.com/docs/pipelines/wait-step
    """

    continue_on_failure: bool | None = Field(
        default=None,
        description="Continue to the next steps, even if the previous group of steps fail",
    )
    # (NB: These are somewhat meaningless, since they never appear in the UI)
    name: ClassVar = FieldAlias("label")
    label: LabelT | None = Field(default=None)
    wait: ClassVar = FieldAlias(
        "label",
        description="Waits for previous steps to pass before continuing",
    )
    type: Literal["wait", "waiter"] | None = None


class NestedWaitStep(FieldAliasSupport, extra="forbid"):
    wait: WaitStep | None = Field(
        default=None,
        description="Waits for previous steps to pass before continuing",
    )


StringWaitStep = TypeAliasType(
    "StringWaitStep",
    Annotated[
        Literal["wait", "waiter"],
        Field(description="Waits for previous steps to pass before continuing"),
    ],
)
