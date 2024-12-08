# @TODO: Inline some annotations?

from typing import Literal, Any, Annotated, ClassVar
from typing_extensions import TypeAliasType

from pydantic import (
    BaseModel,
    Field,
    model_validator,
)

from shimbboleth.buildkite.pipeline_config._alias import FieldAlias, FieldAliasSupport
from shimbboleth.buildkite.pipeline_config._canonicalize import (
    Canonicalizer,
    ListofStringCanonicalizer,
)
from shimbboleth.buildkite.pipeline_config._base import BKStepBase
from shimbboleth.buildkite.pipeline_config._agents import AgentsT
from shimbboleth.buildkite.pipeline_config._types import (
    BranchesT,
    EnvT,
    LabelT,
    SkipT,
    LooseBoolT,
    SoftFailT,
)
from shimbboleth.buildkite.pipeline_config._notify import CommandNotifyT
from shimbboleth.buildkite.pipeline_config._matrix import (
    SimpleMatrixT,
    SingleDimensionMatrix,
    MultiDimensionMatrix,
)


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


_AUTOMATIC_RETRY_DEFAULT = [AutomaticRetry(exit_status="*", limit=2)]


class _AutomaticRetryCanonicalizer(
    Canonicalizer[
        LooseBoolT | AutomaticRetry | list[AutomaticRetry] | None, list[AutomaticRetry]
    ]
):
    # @TODO: We could inject the default here

    @classmethod
    def canonicalize(
        cls, value: LooseBoolT | AutomaticRetry | list[AutomaticRetry] | None
    ) -> list[AutomaticRetry]:
        if value is None or value == "false" or value is False:
            return []
        if value == "true" or value is True:
            return _AUTOMATIC_RETRY_DEFAULT
        if not isinstance(value, list):
            return [value]
        return value


class _ManualRetryCanonicalizer(
    Canonicalizer[
        LooseBoolT | ManualRetryConditions | None,
        ManualRetryConditions,
    ]
):
    @classmethod
    def canonicalize(
        cls, value: LooseBoolT | ManualRetryConditions | None
    ) -> ManualRetryConditions:
        if value is None or value == "true" or value is True:
            return ManualRetryConditions(allowed=True)
        if value == "false" or value is False:
            return ManualRetryConditions(allowed=False)
        return value


class RetryRuleset(BaseModel, extra="forbid"):
    """The conditions for retrying this step."""

    automatic: Annotated[list[AutomaticRetry], _AutomaticRetryCanonicalizer()] = Field(
        # @TODO: Why does default have Nones here in the schema?
        default=_AUTOMATIC_RETRY_DEFAULT,
        description="Whether to allow a job to retry automatically. If set to true, the retry conditions are set to the default value.",
    )
    # NB: This canonicalizes truthy values into `ManualRetryConditions(allowed=True)`
    manual: Annotated[ManualRetryConditions, _ManualRetryCanonicalizer()] = Field(
        default=ManualRetryConditions(allowed=True),
        description="Whether to allow a job to be retried manually",
        json_schema_extra={"default": True},
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
    # @TODO: Any?
    dict[str, Any],
    Field(
        description="A map of plugins for this step. Deprecated: please use the array syntax.",
        deprecated=True,
    ),
]


class CacheMap(BaseModel, extra="allow"):
    paths: list[str]

    name: str | None = None
    size: str | None = Field(default=None, pattern="^\\d+g$")


class _CacheCanonicalizer(Canonicalizer[str | list[str] | CacheMap, CacheMap]):
    @classmethod
    def canonicalize(cls, value: str | list[str] | CacheMap) -> CacheMap:
        if isinstance(value, str):
            return CacheMap(paths=[value])
        if isinstance(value, list):
            return CacheMap(paths=value)
        return value


CacheT = TypeAliasType(
    "CacheT",
    Annotated[
        CacheMap,
        _CacheCanonicalizer(),
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
    artifact_paths: Annotated[list[str], ListofStringCanonicalizer()] = Field(
        default=[],
        description="The glob path/s of artifacts to upload once this step has finished running",
        examples=[["screenshots/*"], ["dist/myapp.zip", "dist/myapp.tgz"]],
    )
    branches: BranchesT | None = None
    cache: CacheT | None = None
    cancel_on_build_failing: CancelOnBuildFailingT | None = None
    command: Annotated[list[str], ListofStringCanonicalizer()] = Field(
        default=[],
        description="The commands to run on the agent",
    )
    # @TODO: Validate these together
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
    matrix: SimpleMatrixT | SingleDimensionMatrix | MultiDimensionMatrix | None = None
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
    retry: RetryRuleset | None = None
    signature: CommandStepSignature | None = None
    skip: SkipT | None = None
    soft_fail: SoftFailT = Field(default=[])
    timeout_in_minutes: int | None = Field(
        default=None,
        description="The number of minutes to time out a job",
        examples=[60],
        ge=1,
    )

    label: LabelT | None = None
    type: Literal["script", "command", "commands"] | None = None

    name: ClassVar = FieldAlias("label", mode="prepend")
    commands: ClassVar = FieldAlias(
        "command", description="The commands to run on the agent"
    )

    @model_validator(mode="before")
    @classmethod
    def _check_command_commands(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "command" in data and "commands" in data:
                raise ValueError(
                    "Step type is ambiguous: use only one of `command` or `commands`"
                )
        return data


class NestedCommandStep(FieldAliasSupport, extra="forbid"):
    command: CommandStep | None = None

    commands: ClassVar = FieldAlias("command")
    script: ClassVar = FieldAlias("command")
