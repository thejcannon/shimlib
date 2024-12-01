from typing import Literal, ClassVar

from pydantic import BaseModel, Field

from ._alias import FieldAlias
from ._base import BKStepBase
from ._types import (
    BranchesT,
    EnvT,
    LabelT,
    SkipT,
)
from ._fields import SoftFailT


class TriggeredBuild(BaseModel, extra="forbid"):
    """Properties of the build that will be created when the step is triggered"""

    branch: str = Field(
        "master",
        description="The branch for the build",
        examples=["master", "feature/xyz"],
    )
    commit: str = Field(
        "HEAD",
        description="The commit hash for the build",
        examples=["HEAD", "b5fb108"],
    )
    env: EnvT | None = None
    message: str = Field(
        "The label of the trigger step",
        description="The message for the build (supports emoji)",
        examples=["Deployment 123 :rocket:"],
    )
    meta_data: dict | None = Field(
        default=None,
        description="Meta-data for the build",
        examples=[{"server": "i-b244e37160c"}],
    )


class TriggerStep(BKStepBase, extra="forbid"):
    """
    A trigger step creates a build on another pipeline.

    https://buildkite.com/docs/pipelines/trigger-step
    """

    trigger: str = Field(description="The slug of the pipeline to create a build")

    is_async: bool = Field(
        default=False,
        description="Whether to continue the build without waiting for the triggered step to complete",
        alias="async",
    )
    branches: BranchesT | None = None
    build: TriggeredBuild | None = None
    skip: SkipT | None = None
    soft_fail: SoftFailT | None = None
    label: LabelT | None = Field(default=None)
    type: Literal["trigger"] | None = None

    name: ClassVar = FieldAlias("label", mode="prepend")


class NestedTriggerStep(BaseModel, extra="forbid"):
    trigger: TriggerStep | None = None
