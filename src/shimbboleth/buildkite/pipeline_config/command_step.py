from typing import Literal, Any, Annotated, ClassVar

from shimbboleth._model import Model, field, MatchesRegex, FieldAlias, Ge, Le

from ._base import BKStepBase
from ._agents import agents_from_json
from ._types import list_str_from_json, bool_from_json, env_from_json, ExitStatus
from ._notify import (
    BasecampCampfireNotify,
    SlackNotify,
    GitHubCommitStatusNotify,
    GitHubCheckNotify,
)
from ._matrix import (
    MatrixArray,
    SingleDimensionMatrix,
    MultiDimensionMatrix,
)


class CommandStepSignature(Model, extra=True):
    """
    The signature of the command step, generally injected by agents at pipeline upload
    """

    algorithm: str | None = None
    """The algorithm used to generate the signature"""

    signed_fields: list[str] | None = None
    """The fields that were signed to form the signature value"""

    value: str | None = None
    """The signature value, a JWS compact signature with a detached body"""


class ManualRetry(Model, extra=False):
    allowed: bool = field(default=True, json_converter=bool_from_json)
    """Whether or not this job can be retried manually"""

    permit_on_passed: bool = field(default=True, json_converter=bool_from_json)
    """Whether or not this job can be retried after it has passed"""

    reason: str | None = None
    """A string that will be displayed in a tooltip on the Retry button in Buildkite. This will only be displayed if the allowed attribute is set to false."""


SignalReasons = Literal[
    "*",
    "none",
    "agent_refused",
    "agent_stop",
    "cancel",
    "process_run_error",
    "signature_rejected",
]


class AutomaticRetry(Model, extra=False):
    # @TODO: Canonicalize?
    exit_status: Literal["*"] | int | list[int] = "*"
    """The exit status number that will cause this job to retry"""

    limit: Annotated[int, Ge(1), Le(10)] | None = None
    """The number of times this job can be retried"""

    signal: str = "*"
    """The exit signal, that may be retried"""

    signal_reason: SignalReasons = "*"
    """The exit signal reason, that may be retried"""


class RetryConditions(Model, extra=False):
    # @TODO: From JSON
    automatic: list[AutomaticRetry] = [AutomaticRetry(limit=2)]
    """Whether to allow a job to retry automatically"""

    # @TODO: From JSON
    manual: ManualRetry = ManualRetry(allowed=True)
    """Whether (and when) to allow a job to be retried manually"""


class CacheMap(Model, extra=True):
    paths: list[str]

    name: str | None = None
    size: Annotated[str, MatchesRegex("^\\d+g$")] | None = None


class CommandStep(BKStepBase, extra=False):
    """
    A command step runs one or more shell commands on one or more agents.

    https://buildkite.com/docs/pipelines/command-step
    """

    agents: dict[str, str] = field(
        default_factory=dict, json_converter=agents_from_json
    )
    """Query rules to target specific agents. See https://buildkite.com/docs/agent/v3/cli-start#agent-targeting"""

    artifact_paths: list[str] = field(
        default_factory=list, json_converter=list_str_from_json
    )
    """The glob paths of artifacts to upload once this step has finished running"""

    branches: list[str] = field(default_factory=list, json_converter=list_str_from_json)
    """Which branches will include this step in their builds"""

    cache: CacheMap | None = None
    """(@TODO) See: https://buildkite.com/docs/pipelines/hosted-agents/linux"""

    cancel_on_build_failing: bool = field(default=False, json_converter=bool_from_json)
    """Whether to cancel the job as soon as the build is marked as failing"""

    # @TODO: Empty?
    command: list[str] = field(default=[], json_converter=list_str_from_json)
    """The commands to run on the agent"""

    # @TODO: Validate concurrency fields together

    concurrency: int | None = None
    """The maximum number of jobs created from this step that are allowed to run at the same time. If you use this attribute, you must also define concurrency_group."""

    concurrency_group: str | None = None
    """A unique name for the concurrency group that you are creating with the concurrency attribute"""

    concurrency_method: Literal["ordered", "eager"] | None = None
    """Control command order, allowed values are 'ordered' (default) and 'eager'. If you use this attribute, you must also define concurrency_group and concurrency."""

    env: dict[str, Any] = field(default_factory=dict, json_converter=env_from_json)
    """Environment variables for this step"""

    matrix: MatrixArray | SingleDimensionMatrix | MultiDimensionMatrix | None = None
    """Matrix expandsions for this step. See https://buildkite.com/docs/pipelines/configure/workflows/build-matrix"""

    notify: list[
        Literal["github_check", "github_commit_status"]
        | BasecampCampfireNotify
        | SlackNotify
        | GitHubCommitStatusNotify
        | GitHubCheckNotify
    ] = field(default_factory=list)
    """Array of notification options for this step"""

    parallelism: int | None = None
    """The number of parallel jobs that will be created based on this step"""

    # @TODO: Make sure order is preserved from YAML/JSON
    # @TODO: Better type for plugins? Validation? (e.g. `"maxProperties": 1`)
    plugins: list[dict[str, Any]] = field(default_factory=list)
    """An array of plugins for this step."""

    priority: int | None = None
    """Priority of the job, higher priorities are assigned to agents"""

    retry: RetryConditions | None = None
    """The conditions for retrying this step."""

    signature: CommandStepSignature | None = None

    # NB: Passing an empty string is equivalent to false.
    skip: str | bool = False
    """Whether to skip this step or not. Passing a string provides a reason for skipping this command."""

    # @TODO: JSON Converter
    soft_fail: list[ExitStatus] = field(default_factory=list)
    """Allow specified non-zero exit statuses not to fail the build."""

    timeout_in_minutes: Annotated[int, Ge(1)] | None = None
    """The number of minutes to time out a job"""

    # @TODO: I think this defaults to the command?
    label: str | None = None
    """The label that will be displayed in the pipeline visualization in Buildkite. Supports emoji."""

    type: Literal["script", "command", "commands"] = "command"

    name: ClassVar = FieldAlias("label", mode="prepend")
    commands: ClassVar = FieldAlias("command")

    # @model_validator(mode="before")
    # @classmethod
    # def _check_command_commands(cls, data: Any) -> Any:
    #     if isinstance(data, dict):
    #         if "command" in data and "commands" in data:
    #             raise ValueError(
    #                 "Step type is ambiguous: use only one of `command` or `commands`"
    #             )
    #     return data

    @Model._json_converter_(cache)
    @classmethod
    def _cache_map_from_json(cls, value: str | list[str] | CacheMap) -> CacheMap:
        if isinstance(value, str):
            return CacheMap(paths=[value])
        if isinstance(value, list):
            return CacheMap(paths=value)
        return value

    @Model._json_converter_(cache)
    @classmethod
    def _plugins_from_json(
        cls, value: list[str | dict[str, Any]] | dict[str, Any]
    ) -> list[dict[str, Any]]:
        # @TODO: ...
        return []
