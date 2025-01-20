# @TODO: Validate limits? https://buildkite.com/docs/pipelines/configure/workflows/build-matrix#matrix-limits
# @TODO: Should adjustment classes be inner classes?

"""
@TODO: docstring

See: https://buildkite.com/docs/pipelines/configure/step-types/command-step#matrix-attributes
"""

from typing import TypeAlias, Literal, Annotated

from shimbboleth.internal.clay import Model, field, NonEmptyList, Not, NonEmptyDict
from shimbboleth.internal.clay.validation import MatchesRegex
from ._types import skip_from_json, soft_fail_from_json, soft_fail_to_json


MatrixElementT: TypeAlias = str | int | bool
MatrixArray: TypeAlias = list[MatrixElementT]


class _AdjustmentBase(Model):
    # NB: Passing an empty string is equivalent to false.
    skip: bool | str = field(default=False, json_loader=skip_from_json)
    """Whether to skip this step or not. Passing a string provides a reason for skipping this command."""

    # NB: This differs from the upstream schema in that we "unpack"
    #  the `exit_status` object into the status.
    # @TODO: Upstream allows exit status to be 0...
    soft_fail: bool | NonEmptyList[Annotated[int, Not[Literal[0]]]] = field(
        default=False, json_loader=soft_fail_from_json, json_dumper=soft_fail_to_json
    )
    """Allow specified non-zero exit statuses not to fail the build."""


class ScalarAdjustment(_AdjustmentBase, Model, extra=False):
    """An adjustment to a Build Matrix scalar element (e.g. single-dimension matrix)."""

    with_value: str = field(json_alias="with")
    """An existing (or new) element to adjust"""

    # NB: other fields from base


class SingleDimensionMatrix(Model, extra=False):
    """Configuration for single-dimension Build Matrix (e.g. list of elements/adjustments)."""

    setup: NonEmptyList[MatrixElementT]

    adjustments: list[ScalarAdjustment] = field(default_factory=list)


class MultiDimensionMatrixAdjustment(_AdjustmentBase, Model):
    """An adjustment to a multi-dimension Build Matrix"""

    # NB: other fields from base

    # @TODO: Each key in a `matrix.adjustments.with` must exist in the associated `matrix.setup`;
    #   new dimensions may not be created by an adjustment, only new elements; missing [...]
    # @TODO: Techincally, we could do the same MatchesRegex, but due to the above it's kind of pointless
    #   (but also this would be schema-invalid vs the above is logic-invalid)
    with_value: dict[str, MatrixElementT] = field(json_alias="with")
    """Specification of a new or existing Build Matrix combination"""


class MultiDimensionMatrix(Model, extra=False):
    """Configuration for multi-dimension Build Matrix (e.g. map of elements/adjustments)."""

    setup: NonEmptyDict[
        Annotated[str, MatchesRegex(r"^[a-zA-Z0-9_]+$")], list[MatrixElementT]
    ]
    """Maps dimension names to a lists of elements"""

    adjustments: list[MultiDimensionMatrixAdjustment] = field(default_factory=list)
