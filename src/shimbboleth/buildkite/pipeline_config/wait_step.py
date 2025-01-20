from typing import ClassVar, Literal


from shimbboleth.internal.clay import FieldAlias, field

from shimbboleth.buildkite.pipeline_config._types import (
    list_str_from_json,
    bool_from_json,
)
from shimbboleth.buildkite.pipeline_config._base import StepBase


class WaitStep(StepBase, extra=False):
    """
    A wait step waits for all previous steps to have successfully completed before allowing following jobs to continue.

    https://buildkite.com/docs/pipelines/wait-step
    """

    branches: list[str] = field(default_factory=list, json_loader=list_str_from_json)
    """Which branches will include this step in their builds"""

    continue_on_failure: bool = field(default=False, json_loader=bool_from_json)
    """Continue to the next steps, even if the previous group of steps fail"""

    wait: str | None = None
    """Waits for previous steps to pass before continuing"""

    type: Literal["wait", "waiter"] = "wait"

    # (NB: These are somewhat meaningless, since they never appear in the UI)
    label: ClassVar = FieldAlias("wait", json_mode="prepend")
    name: ClassVar = FieldAlias("wait", json_mode="prepend")
