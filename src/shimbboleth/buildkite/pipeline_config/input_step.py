from typing import Literal
from typing_extensions import ClassVar

from shimbboleth._model import FieldAlias
from ._interactive_step import InteractiveStepBase, field


class InputStep(InteractiveStepBase, extra=False):
    """
    An input step is used to collect information from a user.

    https://buildkite.com/docs/pipelines/input-step
    """

    input: str | None = field(default=None)
    """The label of the input step"""

    type: Literal["input"] = "input"

    label: ClassVar = FieldAlias("input", mode="prepend")
    name: ClassVar = FieldAlias("input", mode="prepend")
