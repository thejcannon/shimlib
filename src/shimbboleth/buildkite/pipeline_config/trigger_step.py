from typing import Literal, ClassVar, Any


from shimbboleth._model import field, FieldAlias, Model

from ._base import StepBase
from ._types import bool_from_json, list_str_from_json, skip_from_json


class TriggeredBuild(Model, extra=False):
    """Properties of the build that will be created when the step is triggered"""

    branch: str | None = None
    """
    The branch for the build.

    NOTE: The upstream default is the pipeline's default branch.
    """

    commit: str = "HEAD"
    """The commit hash for the build"""

    # @TODO: upstream allows list and object
    env: dict[str, str | int | bool] = field(default_factory=dict)
    """Environment variables for this step"""

    message: str | None = None
    """
    The message for the build (supports emoji).

    NOTE: The upstream default is the label of the trigger step.
    """

    # @TODO: Not "Any" but "any JSON type
    meta_data: dict[str, Any] = field(default_factory=dict)
    """Meta-data for the build"""


class TriggerStep(StepBase, extra=False):
    """
    A trigger step creates a build on another pipeline.

    https://buildkite.com/docs/pipelines/trigger-step
    """

    trigger: str
    """The slug of the pipeline to create a build"""

    is_async: bool = field(
        default=False, json_alias="async", json_loader=bool_from_json
    )
    """Whether to continue the build without waiting for the triggered step to complete"""

    branches: list[str] = field(default_factory=list, json_loader=list_str_from_json)
    """Which branches will include this step in their builds"""

    build: TriggeredBuild | None = None
    """Attributes for the triggered build"""

    # NB: Passing an empty string is equivalent to false.
    skip: bool | str = field(default=False, json_loader=skip_from_json)
    """Whether to skip this step or not. Passing a string provides a reason for skipping this command"""

    soft_fail: bool = field(default=False, json_loader=bool_from_json)
    """When true, failure of the triggered build will not cause the triggering build to fail"""

    # @TODO: This has some default from the trigger
    #   In canvas view it's "Trigger build on xyz", on classic its "Trigger Build"
    label: str | None = None
    """The label that will be displayed in the pipeline visualisation in Buildkite. Supports emoji"""

    type: Literal["trigger"] = "trigger"

    name: ClassVar = FieldAlias("label", json_mode="prepend")
