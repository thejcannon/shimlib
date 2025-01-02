from typing import Literal, ClassVar


from shimbboleth._model import field, FieldAlias


from ._interactive_step import InteractiveStepBase


class BlockStep(InteractiveStepBase, extra=False):
    """
    A block step is used to pause the execution of a build and wait on a team member to unblock it using the web or the API.

    https://buildkite.com/docs/pipelines/block-step
    """

    blocked_state: Literal["passed", "failed", "running"] = field(default="passed")
    """The state that the build is set to when the build is blocked by this block step"""

    block: str | None = field(default=None)
    """The label of the block step"""

    type: Literal["block"] = "block"

    label: ClassVar = FieldAlias("block", mode="prepend")
    name: ClassVar = FieldAlias("block", mode="prepend")
