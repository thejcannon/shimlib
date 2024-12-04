# @TODO: Inline some annotations

from typing import Literal, Any, Annotated, ClassVar
from typing_extensions import TypeAliasType

from pydantic import (
    BaseModel,
    Field,
)

from shimbboleth.buildkite.pipeline_config._alias import FieldAlias, FieldAliasSupport

from ._base import BKStepBase
from ._agents import AgentsT
from ._types import (
    BranchesT,
    EnvT,
    LabelT,
    SkipT,
    LooseBoolT,
)
from ._fields import SoftFailT
from ._notify import CommandNotifyT


# @TODO: Extra allow?
class CommandStepSignature(BaseModel):
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
    allowed: LooseBoolT = Field(
        default=True,
        description="Whether or not this job can be retried manually",
    )
    permit_on_passed: LooseBoolT = Field(
        default=True,
        description="Whether or not this job can be retried after it has passed",
    )
    reason: str | None = Field(
        default=None,
        description="A string that will be displayed in a tooltip on the Retry button in Buildkite. This will only be displayed if the allowed attribute is set to false.",
        examples=["No retries allowed on deploy steps"],
    )


class AutomaticRetry(BaseModel, extra="forbid"):
    # @TODO: Canonicalize?
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
class RetryConditions(BaseModel):
    """The conditions for retrying this step."""

    # @TODO: Canonicalize?
    automatic: LooseBoolT | AutomaticRetry | list[AutomaticRetry] | None = Field(
        # @TODO: Why does default have Nones here?
        default=[AutomaticRetry(exit_status="*", limit=2)],
        description="Whether to allow a job to retry automatically. If set to true, the retry conditions are set to the default value.",
    )
    # @TODO: Canonicalize?
    manual: LooseBoolT | ManualRetryConditions | None = Field(
        default=None, description="Whether to allow a job to be retried manually"
    )


# @TODO: Canonicalize?
MatrixElementT = TypeAliasType("MatrixElementT", str | int | bool)
SingleDimensionalMatrix = Annotated[
    list[MatrixElementT],
    Field(
        description="List of elements for simple single-dimension Build Matrix",
        examples=[["linux", "freebsd"]],
    ),
]


class MatrixAdjustment(BaseModel):
    """An adjustment to a Build Matrix"""

    with_value: (
        # @TODO: Canonicalize?
        Annotated[
            list[MatrixElementT],
            Field(
                description="List of existing or new elements for single-dimension Build Matrix"
            ),
        ]
        | Annotated[
            dict[
                Annotated[
                    str,
                    Field(
                        description="Build Matrix dimension name",
                    ),
                ],
                Annotated[str, Field(description="Build Matrix dimension element")],
            ],
            Field(
                description="Specification of a new or existing Build Matrix combination",
                examples=[{"arch": "arm64", "os": "linux"}],
            ),
        ]
    ) = Field(alias="with")

    skip: SkipT | None = None
    soft_fail: SoftFailT | None = None


class MultiDimenisonalMatrix(BaseModel):
    "Configuration for multi-dimension Build Matrix"

    setup: (
        # @TODO: Canonicalize?
        Annotated[
            list[MatrixElementT],
            Field(
                description="List of elements for single-dimension Build Matrix",
                examples=[["linux", "freebsd"]],
            ),
        ]
        | Annotated[
            dict[
                Annotated[
                    str,
                    Field(
                        description="Build Matrix dimension name",
                        pattern="^[a-zA-Z0-9_]+$",
                    ),
                ],
                Annotated[
                    list[MatrixElementT],
                    Field(
                        description="List of elements for this Build Matrix dimension"
                    ),
                ],
            ],
            Field(
                description="Mapping of Build Matrix dimension names to their lists of elements",
                examples=[{"arch": ["arm64", "riscv"], "os": ["linux", "freebsd"]}],
            ),
        ]
    )

    adjustments: list[MatrixAdjustment] | None = Field(
        default=None, description="List of Build Matrix adjustments"
    )


PluginArrayItem = Annotated[
    # @TODO: Any?
    dict[str, Any],
    Field(
        examples=[{"docker-compose#v1.0.0": {"run": "app"}}],
        # @TODO: Validate this Python-side
        json_schema_extra={"maxProperties": 1},
    ),
]
PluginArrayT = Annotated[
    # @TODO: Canonicalize?
    list[str | PluginArrayItem], Field(description="Array of plugins for this step")
]
PluginMapT = Annotated[
    dict[str, Any],
    Field(
        # @TODO: Deprecated (Python-side)
        description="A map of plugins for this step. Deprecated: please use the array syntax."
    ),
]


class CacheMap(BaseModel):
    # @TODO: Canonicalize?
    paths: str | list[str]

    name: str | None = None
    size: str | None = Field(default=None, pattern="^\\d+g$")


CacheT = TypeAliasType(
    "CacheT",
    Annotated[
        # @TODO: Canonicalize?
        str | list[str] | CacheMap,
        Field(
            description="The paths for the caches to be used in the step",
            examples=[
                "dist/",
                [".build/*", "assets/*"],
                {
                    "name": "cool-cache",
                    "paths": ["/path/one", "/path/two"],
                    "size": "20g",
                },
            ],
        ),
    ],
)

CancelOnBuildFailingT = TypeAliasType(
    "CancelOnBuildFailingT",
    Annotated[
        LooseBoolT,
        Field(
            default=False,
            description="Whether to cancel the job as soon as the build is marked as failing",
        ),
    ],
)


class CommandStep(BKStepBase, extra="forbid"):
    """
    A command step runs one or more shell commands on one or more agents.

    https://buildkite.com/docs/pipelines/command-step
    """

    agents: AgentsT | None = None
    # @TODO: Canonicalize?
    artifact_paths: str | list[str] | None = Field(
        default=None,
        description="The glob path/s of artifacts to upload once this step has finished running",
        examples=[["screenshots/*"], ["dist/myapp.zip", "dist/myapp.tgz"]],
    )
    branches: BranchesT | None = None
    cache: CacheT | None = None
    cancel_on_build_failing: CancelOnBuildFailingT | None = None
    # @TODO: Canonicalize?
    command: list[str] | str | None = Field(
        default=None,
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
    env: EnvT | None = None
    matrix: SingleDimensionalMatrix | MultiDimenisonalMatrix | None = None
    notify: CommandNotifyT | None = None
    parallelism: int | None = Field(
        default=None,
        description="The number of parallel jobs that will be created based on this step",
        examples=[42],
    )
    plugins: PluginArrayT | PluginMapT | None = None
    priority: int | None = Field(
        default=None,
        description="Priority of the job, higher priorities are assigned to agents",
        examples=[-1, 1],
    )
    retry: RetryConditions | None = None
    signature: CommandStepSignature | None = None
    skip: SkipT | None = None
    soft_fail: SoftFailT | None = None
    timeout_in_minutes: int | None = Field(
        default=None,
        description="The number of minutes to time out a job",
        examples=[60],
        ge=1,
    )

    label: LabelT | None = Field(default=None)
    type: Literal["script", "command", "commands"] | None = None

    name: ClassVar = FieldAlias("label", mode="prepend")
    commands: ClassVar = FieldAlias(
        "command", description="The commands to run on the agent"
    )

    # @TODO: Reject command and commands both being provided


class NestedCommandStep(FieldAliasSupport, extra="forbid"):
    command: CommandStep | None = Field(default=None)

    commands: ClassVar = FieldAlias("command")
    script: ClassVar = FieldAlias("command")
