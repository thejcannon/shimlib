# @TODO: Validate limits? https://buildkite.com/docs/pipelines/configure/workflows/build-matrix#matrix-limits
# @TODO: Should adjustment classes be inner classes?

"""
@TODO: docstring

See: https://buildkite.com/docs/pipelines/configure/step-types/command-step#matrix-attributes
"""

from typing import TypeAlias, Literal, Annotated

from shimbboleth._model import Model, field, NonEmptyList, Not
from ._types import skip_from_json, soft_fail_from_json, soft_fail_to_json


MatrixElementT: TypeAlias = str | int | bool
MatrixArray: TypeAlias = list[MatrixElementT]


class _AdjustmentBase(Model):
    # NB: Passing an empty string is equivalent to false.
    skip: bool | str = field(default=False, json_loader=skip_from_json)
    """Whether to skip this step or not. Passing a string provides a reason for skipping this command."""

    # NB: This differs from the upstream schema in that we "unpack"
    #  the `exit_status` object into the status.
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

    adjustments: list[ScalarAdjustment] | None = None


class MultiDimensionMatrixAdjustment(_AdjustmentBase, Model):
    """An adjustment to a multi-dimension Build Matrix"""

    with_value: dict[str, list[MatrixElementT]] = field(json_alias="with")
    """Specification of a new or existing Build Matrix combination"""

    # NB: other fields from base


class MultiDimensionMatrix(Model, extra=False):
    """Configuration for multi-dimension Build Matrix (e.g. map of elements/adjustments)."""

    setup: dict[str, list[MatrixElementT]]
    """Maps dimension names to a lists of elements"""

    adjustments: list[MultiDimensionMatrixAdjustment] | None = None
