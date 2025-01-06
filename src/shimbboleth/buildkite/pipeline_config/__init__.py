from shimbboleth._model import Model, field

from ._agents import agents_from_json
from .block_step import BlockStep
from .input_step import InputStep
from .wait_step import WaitStep
from .trigger_step import TriggerStep
from .command_step import CommandStep
from ._types import rubystr
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


# @TODO: When loading yaml, you can omit steps and just inline the steps themselves
class BuildkitePipeline(Model, extra=True):
    steps: list[
        BlockStep | InputStep | CommandStep | WaitStep | TriggerStep | GroupStep
    ] = field(json_loader=parse_steps)

    agents: dict[str, str] = field(default_factory=dict, json_loader=agents_from_json)
    """Query rules to target specific agents. See https://buildkite.com/docs/agent/v3/cli-start#agent-targeting"""

    env: dict[str, str] = field(default_factory=dict)
    """Environment variables for this pipeline"""

    notify: BuildNotifyT = field(default_factory=list)

    # @TODO: Missing cache? https://buildkite.com/docs/pipelines/hosted-agents/linux#cache-volumes

    @Model._json_loader_(env)
    @staticmethod
    def _convert_env(
        # NB: Unlike Command steps, invalid value types aren't allowed
        value: dict[str, str | int | bool],
    ) -> dict[str, str]:
        return {k: rubystr(v) for k, v in value.items()}
