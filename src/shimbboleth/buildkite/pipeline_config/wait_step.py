from typing import ClassVar, Literal, Annotated
from typing_extensions import TypeAliasType

from pydantic import Field

from shimbboleth.buildkite.pipeline_config._types import LooseBoolT

from ._types import BranchesT
from ._base import BKStepBase
from ._alias import FieldAlias, FieldAliasSupport


class WaitStep(BKStepBase, extra="forbid"):
    """
    A wait step waits for all previous steps to have successfully completed before allowing following jobs to continue.

    https://buildkite.com/docs/pipelines/wait-step
    """

    branches: BranchesT | None = None
    continue_on_failure: LooseBoolT | None = Field(
        default=False,
        description="Continue to the next steps, even if the previous group of steps fail",
    )
    wait: str | None = Field(
        default=None,
        description="Waits for previous steps to pass before continuing",
    )
    type: Literal["wait", "waiter"] | None = None

    # (NB: These are somewhat meaningless, since they never appear in the UI)
    label: ClassVar = FieldAlias("wait", mode="prepend")
    name: ClassVar = FieldAlias("wait", mode="prepend")


class NestedWaitStep(FieldAliasSupport, extra="forbid"):
    wait: WaitStep | None = Field(
        default=None,
        description="Waits for previous steps to pass before continuing",
    )

    waiter: ClassVar = FieldAlias("wait")


StringWaitStep = TypeAliasType(
    "StringWaitStep",
    Annotated[
        Literal["wait", "waiter"],
        Field(description="Waits for previous steps to pass before continuing"),
    ],
)
