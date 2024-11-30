from typing import Literal, Annotated
from typing_extensions import ClassVar, TypeAliasType

from pydantic import BaseModel, Field

from ._alias import FieldAlias
from ._base import BKStepBase
from ._types import (
    BranchesT,
    LabelT,
    PromptT,
)
from ._fields import FieldsT


class InputStep(BKStepBase, extra="forbid"):
    """
    An input step is used to collect information from a user.

    https://buildkite.com/docs/pipelines/input-step
    """

    branches: BranchesT | None = None
    fields: FieldsT | None = None
    prompt: PromptT | None = None
    name: ClassVar = FieldAlias("label")
    label: LabelT | None = Field(default=None)
    input: ClassVar = FieldAlias("label")
    type: Literal["input"] | None = None


class NestedInputStep(BaseModel, extra="forbid"):
    input: InputStep | None = None


StringInputStep = TypeAliasType(
    "StringInputStep",
    Annotated[
        Literal["input"],
        Field(
            description="Pauses the execution of a build and waits on a user to unblock it"
        ),
    ],
)
