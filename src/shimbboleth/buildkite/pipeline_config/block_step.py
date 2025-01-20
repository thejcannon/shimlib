from typing import Literal, ClassVar


from shimbboleth.internal.clay import field, FieldAlias


from ._manual_step import ManualStepBase


class BlockStep(ManualStepBase, extra=False):
    """
    A block step is used to pause the execution of a build and wait on a team member to unblock it using the web or the API.

    https://buildkite.com/docs/pipelines/block-step
    """

    blocked_state: Literal["passed", "failed", "running"] = field(default="passed")
    """The state that the build is set to when the build is blocked by this block step"""

    block: str | None = field(default=None)
    """The label of the block step"""

    type: Literal["block", "manual"] = "block"

    label: ClassVar = FieldAlias("block", json_mode="prepend")
    name: ClassVar = FieldAlias("block", json_mode="prepend")
