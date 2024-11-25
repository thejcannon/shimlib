from typing import Literal, Any

from pydantic import BaseModel, Field, AliasChoices

from ._types import (
    AllowDependencyFailureT,
    BranchesT,
    EnvT,
    IfT,
    DependsOnT,
    IdentifierT,
    KeyT,
    LabelT,
    SkipT,
    SoftFailT,
)


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


class TriggerStep(BaseModel, extra="forbid"):
    """
    A trigger step creates a build on another pipeline.

    https://buildkite.com/docs/pipelines/trigger-step
    """

    trigger: str = Field(description="The slug of the pipeline to create a build")

    allow_dependency_failure: AllowDependencyFailureT = False
    is_async: bool = Field(
        default=False,
        description="Whether to continue the build without waiting for the triggered step to complete",
        alias="async",
    )
    branches: BranchesT | None = None
    build: TriggeredBuild | None = None
    depends_on: DependsOnT | None = None
    if_condition: IfT | None = Field(default=None, alias="if")
    key: KeyT | None = Field(
        default=None, validation_alias=AliasChoices("key", "id", "identifier")
    )
    label: LabelT | None = Field(
        default=None, validation_alias=AliasChoices("label", "name")
    )
    skip: SkipT | None = None
    soft_fail: SoftFailT | None = None
    type: Literal["trigger"] | None = None


class NestedTriggerStep(BaseModel, extra="forbid"):
    trigger: TriggerStep | None = None
