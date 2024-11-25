from typing import Literal, Annotated
from typing_extensions import TypeAliasType

from pydantic import AliasChoices, BaseModel, Field

from ._types import (
    AllowDependencyFailureT,
    IfT,
    DependsOnT,
    IdentifierT,
    KeyT,
)


class WaitStep(BaseModel, extra="forbid"):
    """
    A wait step waits for all previous steps to have successfully completed before allowing following jobs to continue.

    https://buildkite.com/docs/pipelines/wait-step
    """

    allow_dependency_failure: AllowDependencyFailureT = False
    continue_on_failure: bool | None = Field(
        default=None,
        description="Continue to the next steps, even if the previous group of steps fail",
    )
    depends_on: DependsOnT | None = None
    if_condition: IfT | None = Field(default=None, alias="if")
    key: KeyT | None = Field(
        default=None, validation_alias=AliasChoices("key", "id", "identifier")
    )
    type: Literal["wait", "waiter"] | None = None
    wait: Literal[""] | None = Field(
        default=None,
        description="Waits for previous steps to pass before continuing",
        validation_alias=AliasChoices("wait", "waiter"),
    )


class NestedWaitStep(BaseModel, extra="forbid"):
    wait: WaitStep | None = Field(
        default=None,
        description="Waits for previous steps to pass before continuing",
        validation_alias=AliasChoices("wait", "waiter"),
    )


StringWaitStep = TypeAliasType(
    "StringWaitStep",
    Annotated[
        Literal["wait", "waiter"],
        Field(description="Waits for previous steps to pass before continuing"),
    ],
)
