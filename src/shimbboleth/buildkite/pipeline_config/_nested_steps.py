from typing import ClassVar

from shimbboleth._model import Model, FieldAlias

from .block_step import BlockStep
from .input_step import InputStep
from .wait_step import WaitStep
from .trigger_step import TriggerStep
from .command_step import CommandStep


class NestedBlockStep(Model, extra=False):
    block: BlockStep | None = None


class NestedInputStep(Model, extra=False):
    input: InputStep | None = None


class NestedTriggerStep(Model, extra=False):
    trigger: TriggerStep | None = None


class NestedWaitStep(Model, extra=False):
    wait: WaitStep | None = None
    """Waits for previous steps to pass before continuing"""

    # @TODO: If both are given it gets mad about `waiter`.
    # But this actually looks like the discriminator
    # is choosing `WaitStep` over `NestedWaitStep`.
    waiter: ClassVar = FieldAlias("wait")


class NestedCommandStep(Model, extra=False):
    command: CommandStep | None = None

    commands: ClassVar = FieldAlias("command")
    script: ClassVar = FieldAlias("command")

    # @model_validator(mode="before")
    # @classmethod
    # def _check_command_commands_script(cls, data: Any) -> Any:
    #     # @TODO: I think this should be in `_alias`.
    #     if isinstance(data, dict):
    #         keys = [
    #             f"`{key}`" for key in ["command", "commands", "script"] if key in data
    #         ]
    #         if len(keys) > 1:
    #             raise ValueError(
    #                 f"Step type is ambiguous: use only one of {' or '.join(keys)}"
    #             )
    #     return data
