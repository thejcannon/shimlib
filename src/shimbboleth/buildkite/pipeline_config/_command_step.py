from typing import Literal, Any, Annotated
from typing_extensions import TypeAliasType

from pydantic import BaseModel, Field, AliasChoices

from ._types import (
    AllowDependencyFailureT,
    BranchesT,
    EnvT,
    IfT,
    DependsOnT,
    AgentsT,
    IdentifierT,
    KeyT,
    LabelT,
    SkipT,
    CacheT,
    CancelOnBuildFailingT,
)
from ._notify import BuildNotifyT


# @TODO: Extra allow?
class CommandStepSignature(BaseModel, extra="allow"):
    """
    The signature of the command step, generally injected by agents at pipeline upload
    """

    algorithm: str | None = Field(
        default=None,
        description="The algorithm used to generate the signature",
        examples=["HS512", "EdDSA", "PS256"],
    )
    signed_fields: list[str] | None = Field(
        default=None,
        description="The fields that were signed to form the signature value",
        examples=[["command", "matrix", "plugins", "env::SOME_ENV_VAR"]],
    )
    value: str | None = Field(
        default=None,
        description="The signature value, a JWS compact signature with a detached body",
    )


class ManualRetryConditions(BaseModel, extra="forbid"):
    allowed: bool | Literal["true", "false"] = Field(
        default=True,
        description="Whether or not this job can be retried manually",
    )
    permit_on_passed: bool | Literal["true", "false"] = Field(
        default=True,
        description="Whether or not this job can be retried after it has passed",
    )
    reason: str | None = Field(
        default=None,
        description="A string that will be displayed in a tooltip on the Retry button in Buildkite. This will only be displayed if the allowed attribute is set to false.",
        examples=["No retries allowed on deploy steps"],
    )


class AutomaticRetry(BaseModel, extra="forbid"):
    exit_status: Literal["*"] | int | list[int] | None = Field(
        default=None,
        description="The exit status number that will cause this job to retry",
    )
    limit: int | None = Field(
        default=None,
        description="The number of times this job can be retried",
        ge=1,
        le=10,
    )
    signal: str | None = Field(
        default=None,
        description="The exit signal, if any, that may be retried",
        examples=["*", "none", "SIGKILL", "term"],
    )
    signal_reason: (
        Literal[
            "*",
            "none",
            "agent_refused",
            "agent_stop",
            "cancel",
            "process_run_error",
            "signature_rejected",
        ]
        | None
    ) = Field(
        default=None, description="The exit signal reason, if any, that may be retried"
    )


# @TODO: Extra allow?
class RetryConditions(BaseModel, extra="allow"):
    """The conditions for retrying this step."""

    # @TODO "string true/false" use validators?
    automatic: (
        bool | Literal["true", "false"] | AutomaticRetry | list[AutomaticRetry] | None
    ) = Field(
        default=[AutomaticRetry(exit_status="*", limit=2)],
        description="Whether to allow a job to retry automatically. If set to true, the retry conditions are set to the default value.",
    )
    manual: bool | Literal["true", "false"] | AutomaticRetry | None = Field(
        default=None, description="Whether to allow a job to be retried manually"
    )


MatrixElementT = TypeAliasType("MatrixElementT", str | int | bool)
MatrixElementsListT = Annotated[
    list[MatrixElementT],
    Field(
        description="List of elements for single-dimension Build Matrix",
        examples=[["linux", "freebsd"]],
    ),
]
MatrixDimensionNameT = Annotated[
    str, Field(pattern=r"^[a-zA-Z0-9_]+$", description="Build Matrix dimension name")
]
MatrixMapT = Annotated[
    dict[MatrixDimensionNameT, MatrixElementsListT],
    Field(
        description="Mapping of Build Matrix dimension names to their lists of elements",
        examples=[{"arch": ["arm64", "riscv"], "os": ["linux", "freebsd"]}],
    ),
]


class MatrixAdjustment(BaseModel, extra="allow"):
    with_value: MatrixElementsListT | MatrixMapT = Field(
        alias="with",
        description="An adjustment to a Build Matrix",
    )

    skip: SkipT | None = None
    soft_fail: bool | None = None


class MultiDimenisonalMatrix(BaseModel, extra="allow"):
    """
    Configuration for multi-dimension Build Matrix

    https://buildkite.com/docs/pipelines/command-step#matrix-attributes
    """

    setup: MatrixElementsListT | MatrixMapT

    adjustments: list[MatrixAdjustment] | None = Field(
        default=None, description="List of Build Matrix adjustments"
    )


class CommandStep(BaseModel, extra="forbid"):
    """
    A command step runs one or more shell commands on one or more agents.

    https://buildkite.com/docs/pipelines/command-step
    """

    agents: AgentsT | None = None
    allow_dependency_failure: AllowDependencyFailureT = False
    artifacts_paths: str | list[str] | None = Field(
        default=None,
        description="The glob path/s of artifacts to upload once this step has finished running",
        examples=[["screenshots/*"], ["dist/myapp.zip", "dist/myapp.tgz"]],
    )
    branches: BranchesT | None = None
    cache: CacheT | None = None
    cancel_on_build_failing: CancelOnBuildFailingT | None = None
    command: list[str] | str | None = Field(
        default=None,
        validation_alias=AliasChoices("command", "commands"),
        description="The commands to run on the agent",
    )
    concurrency: int | None = Field(
        default=None,
        description="The maximum number of jobs created from this step that are allowed to run at the same time. If you use this attribute, you must also define concurrency_group.",
        examples=[1],
    )
    concurrency_group: str | None = Field(
        default=None,
        description="A unique name for the concurrency group that you are creating with the concurrency attribute",
        examples=["my-pipeline/deploy"],
    )
    concurrency_method: Literal["ordered", "eager"] | None = Field(
        default=None,
        description="Control command order, allowed values are 'ordered' (default) and 'eager'.  If you use this attribute, you must also define concurrency_group and concurrency.",
        examples=["ordered"],
    )
    depends_on: DependsOnT | None = None
    env: EnvT | None = None
    if_condition: IfT | None = Field(default=None, alias="if")
    key: KeyT | None = Field(
        default=None, validation_alias=AliasChoices("key", "id", "identifier")
    )
    label: LabelT | None = Field(
        default=None, validation_alias=AliasChoices("label", "name")
    )
    matrix: MatrixElementsListT | MultiDimenisonalMatrix | None = None
    notify: BuildNotifyT | None = (
        None  # @TODO: This doesnt use BuildNotify in the schema??
    )
    parallelism: int | None = Field(
        default=None,
        description="The number of parallel jobs that will be created based on this step",
        examples=[42],
    )
    plugins: list[str | dict[str, Any]] | dict[str, Any] | None = None
    priority: int | None = Field(
        default=None,
        description="Priority of the job, higher priorities are assigned to agents",
        examples=[-1, 1],
    )
    retry: RetryConditions | None = None
    signature: CommandStepSignature | None = None
    skip: SkipT | None = None
    timeout_in_minutes: int | None = Field(
        default=None,
        description="The number of minutes to time out a job",
        examples=[60],
        ge=1,
    )

    type: Literal["script", "command", "commands"] | None = None


class NestedCommandStep(BaseModel, extra="forbid"):
    command: CommandStep | None = Field(
        default=None, validation_alias=AliasChoices("command", "commands")
    )  # @TODO: alias "script" as well
