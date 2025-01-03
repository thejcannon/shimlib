from shimbboleth._model import Model, field

from ._agents import agents_from_json
from .block_step import BlockStep
from .input_step import InputStep
from .wait_step import WaitStep
from .trigger_step import TriggerStep
from .command_step import CommandStep
from ._types import env_from_json
from .group_step import GroupStep
from ._notify import BuildNotifyT
from ._parse_steps import parse_steps

ALL_STEP_TYPES = (
    BlockStep,
    InputStep,
    CommandStep,
    WaitStep,
    TriggerStep,
    GroupStep,
)


class BuildkitePipeline(Model, extra=True):
    steps: list[
        BlockStep | InputStep | CommandStep | WaitStep | TriggerStep | GroupStep
    ] = field(json_converter=parse_steps)

    agents: dict[str, str] = field(
        default_factory=dict, json_converter=agents_from_json
    )
    """Query rules to target specific agents. See https://buildkite.com/docs/agent/v3/cli-start#agent-targeting"""

    env: dict[str, str | int | bool] = field(
        default_factory=dict, json_converter=env_from_json
    )
    """Environment variables for this pipeline"""

    notify: BuildNotifyT = field(default_factory=list)

    # @TODO: Missing cache? https://buildkite.com/docs/pipelines/hosted-agents/linux#cache-volumes
