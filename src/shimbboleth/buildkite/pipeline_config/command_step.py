from typing import Literal, Any, Annotated, ClassVar

from shimbboleth._model import (
    Model,
    field,
    MatchesRegex,
    FieldAlias,
    Ge,
    Le,
    Not,
    NonEmptyList,
)
from shimbboleth._model.jsonT import JSONObject

from ._base import StepBase
from ._agents import agents_from_json
from ._types import (
    list_str_from_json,
    bool_from_json,
    rubystr,
    skip_from_json,
    soft_fail_from_json,
    soft_fail_to_json,
)
from ._notify import (
    StepNotifyT,
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

    signed_fields: list[str] = field(default_factory=list)
    """The fields that were signed to form the signature value"""

    value: str | None = None
    """The signature value, a JWS compact signature with a detached body"""


class ManualRetry(Model, extra=False):
    """See https://buildkite.com/docs/pipelines/configure/step-types/command-step#retry-attributes-manual-retry-attributes"""

    allowed: bool = field(default=True, json_loader=bool_from_json)
    """Whether or not this job can be retried manually"""

    permit_on_passed: bool = field(default=True, json_loader=bool_from_json)
    """Whether or not this job can be retried after it has passed"""

    reason: str | None = None
    """
    A string that will be displayed in a tooltip on the Retry button in Buildkite.

    This will only be displayed if the `allowed` attribute is set to false.
    """


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
    """See https://buildkite.com/docs/pipelines/configure/step-types/command-step#retry-attributes-automatic-retry-attributes"""

    exit_status: Literal["*"] | list[int] = field(default="*")
    """The exit status number that will cause this job to retry"""

    # @TODO: Upstram allows 0 (but not 11)
    limit: Annotated[int, Ge(1), Le(10)] | None = None
    """The number of times this job can be retried"""

    signal: str = "*"
    """The exit signal, that may be retried"""

    signal_reason: SignalReasons = "*"
    """The exit signal reason, that may be retried"""


class RetryConditions(Model, extra=False):
    automatic: list[AutomaticRetry] = field(
        default_factory=lambda: [AutomaticRetry(limit=2)]
    )
    """When to allow a job to retry automatically"""

    manual: ManualRetry = field(default_factory=lambda: ManualRetry(allowed=True))
    """When to allow a job to be retried manually"""


class CommandCache(Model, extra=True):
    paths: list[str]

    name: str | None = None
    size: Annotated[str, MatchesRegex("^\\d+g$")] | None = None


class Plugin(Model, extra=False):
    spec: str = field()
    """The plugin "spec". Usually in `<org>/<repo>#<tag>` format"""

    config: JSONObject | None = field(default=None)
    """The configuration to use (or None)"""

    # @FEAT: parse the spec and expose properties

    def model_dump(self) -> JSONObject:
        return {self.spec: self.config}


class CommandStep(StepBase, extra=False):
    """
    A command step runs one or more shell commands on one or more agents.

    https://buildkite.com/docs/pipelines/command-step
    """

    agents: dict[str, str] = field(default_factory=dict, json_loader=agents_from_json)
    """
    Query rules to target specific agents.

    See https://buildkite.com/docs/agent/v3/cli-start#agent-targeting
    """

    artifact_paths: list[str] = field(
        default_factory=list, json_loader=list_str_from_json
    )
    """The glob paths of artifacts to upload once this step has finished running"""

    branches: list[str] = field(default_factory=list, json_loader=list_str_from_json)
    """Which branches will include this step in their builds"""

    cache: CommandCache = field(default_factory=lambda: CommandCache(paths=[]))
    """(@TODO) See: https://buildkite.com/docs/pipelines/hosted-agents/linux"""

    cancel_on_build_failing: bool = field(default=False, json_loader=bool_from_json)
    """Whether to cancel the job as soon as the build is marked as failing"""

    command: list[str] = field(default_factory=list, json_loader=list_str_from_json)
    """The commands to run on the agent"""

    concurrency: int | None = None
    """The maximum number of jobs created from this step that are allowed to run at the same time. If you use this attribute, you must also define concurrency_group."""

    concurrency_group: str | None = None
    """A unique name for the concurrency group that you are creating with the concurrency attribute"""

    concurrency_method: Literal["ordered", "eager"] | None = None
    """Control command order, allowed values are 'ordered' (default) and 'eager'. If you use this attribute, you must also define concurrency_group and concurrency."""

    env: dict[str, str] = field(default_factory=dict)
    """Environment variables for this step"""

    # @TODO: default_factory=list?
    matrix: MatrixArray | SingleDimensionMatrix | MultiDimensionMatrix | None = None
    """
    Matrix expansions for this step.

    See https://buildkite.com/docs/pipelines/configure/workflows/build-matrix
    """

    notify: StepNotifyT = field(default_factory=list)
    """Array of notification options for this step"""

    parallelism: int | None = None
    """The number of parallel jobs that will be created based on this step"""

    # NB: We use a list of plugins, since the same plugin can appear multiple times
    plugins: list[Plugin] = field(default_factory=list)
    """An array of plugins for this step."""

    priority: int | None = None
    """Priority of the job, higher priorities are assigned to agents"""

    retry: RetryConditions | None = None
    """The conditions for retrying this step."""

    signature: CommandStepSignature | None = None
    """@TODO (missing description)"""

    # NB: Passing an empty string is equivalent to false.
    skip: bool | str = field(default=False, json_loader=skip_from_json)
    """Whether to skip this step or not. Passing a string provides a reason for skipping this command."""

    # NB: This differs from the upstream schema in that we "unpack"
    #  the `exit_status` object into the status.
    # @TODO: Upstream allows 0
    soft_fail: bool | NonEmptyList[Annotated[int, Not[Literal[0]]]] = field(
        default=False, json_loader=soft_fail_from_json, json_dumper=soft_fail_to_json
    )
    """Allow specified non-zero exit statuses not to fail the build."""

    # @TODO: Zero is OK upstream?
    timeout_in_minutes: Annotated[int, Ge(1)] | None = None
    """The number of minutes to time out a job"""

    # @TODO: I think this defaults to the command?
    label: str | None = None
    """The label that will be displayed in the pipeline visualization in Buildkite. Supports emoji."""

    type: Literal["script", "command", "commands"] = "command"

    name: ClassVar = FieldAlias("label", json_mode="prepend")
    commands: ClassVar = FieldAlias("command")

    # @TODO: This should just be `model_load`, but that maybe too late?
    #   (We can add this support to FieldAlias)
    # @model_validator(mode="before")
    # @classmethod
    # def _check_command_commands(cls, data: Any) -> Any:
    #     if isinstance(data, dict):
    #         if "command" in data and "commands" in data:
    #             raise ValueError(
    #                 "Step type is ambiguous: use only one of `command` or `commands`"
    #             )
    #     return data

    def __post_init__(self):
        # @TODO: Verify the concurrency_group fields (together)
        pass


@AutomaticRetry._json_loader_("exit_status")
def _load_exit_status(
    value: Literal["*"] | int | list[int],
) -> Literal["*"] | list[int]:
    if isinstance(value, int):
        return [value]
    if value == "*":
        return value
    return value


@RetryConditions._json_loader_("automatic")
def _load_automatic(
    value: bool | Literal["true", "false"] | AutomaticRetry | list[AutomaticRetry],
) -> list[AutomaticRetry]:
    if value in (False, "false"):
        return []
    elif value in (True, "true"):
        return [AutomaticRetry(limit=2)]
    elif isinstance(value, AutomaticRetry):
        return [value]
    return value


@RetryConditions._json_loader_("manual")
def _load_manual(
    value: bool | Literal["true", "false"] | ManualRetry,
) -> ManualRetry:
    if value in (False, "false"):
        return ManualRetry(allowed=False)
    elif value in (True, "true"):
        return ManualRetry(allowed=True)
    return value


@CommandStep._json_loader_("cache")
def _convert_cache(value: str | list[str] | CommandCache) -> CommandCache:
    if isinstance(value, str):
        return CommandCache(paths=[value])
    if isinstance(value, list):
        return CommandCache(paths=value)
    return value


@CommandStep._json_loader_("env")
def _convert_env(
    # @TODO: Upstream allows value to be anything and ignores non-dict. WTF
    value: JSONObject,
) -> dict[str, str]:
    return {
        k: rubystr(v)
        for k, v in value.items()
        # NB: Upstream just ignores invalid types
        if isinstance(v, (str, int, bool))
    }


@CommandStep._json_loader_(
    "matrix",
    json_schema_type=MatrixArray | SingleDimensionMatrix | MultiDimensionMatrix,
)
def _load_matrix(
    value: MatrixArray | JSONObject | None,
) -> MatrixArray | SingleDimensionMatrix | MultiDimensionMatrix | None:
    if value is None:
        return None
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        if isinstance(value["setup"], list):
            return SingleDimensionMatrix.model_load(value)
        return MultiDimensionMatrix.model_load(value)

    # @TODO: Error on wrong type


@CommandStep._json_loader_("notify", json_schema_type=StepNotifyT)
def _load_notify(
    value: list[Any],
) -> StepNotifyT:
    from shimbboleth.buildkite.pipeline_config._notify import parse_step_notify

    return parse_step_notify(value)


@CommandStep._json_loader_("plugins")
def _load_plugins(
    # @TODO: the dictionaries should only have one property.
    #   (e.g. `"maxProperties": 1`)
    value: dict[str, JSONObject | None] | list[str | dict[str, JSONObject | None]],
) -> list[Plugin]:
    # @TODO: Should use `model_load`
    if isinstance(value, dict):
        return [Plugin(spec=spec, config=config) for spec, config in value.items()]
    return [
        Plugin(spec=elem, config=None)
        if isinstance(elem, str)
        else Plugin(spec=list(elem.keys())[0], config=list(elem.values())[0])
        for elem in value
    ]
