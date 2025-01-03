from typing import Literal
from typing_extensions import ClassVar

from shimbboleth._model import FieldAlias
from ._manual_step import ManualStepBase, field


class InputStep(ManualStepBase, extra=False):
    """
    An input step is used to collect information from a user.

    https://buildkite.com/docs/pipelines/input-step
    """

    input: str | None = field(default=None)
    """The label of the input step"""

    type: Literal["input"] = "input"

    label: ClassVar = FieldAlias("input", json_mode="prepend")
    name: ClassVar = FieldAlias("input", json_mode="prepend")
