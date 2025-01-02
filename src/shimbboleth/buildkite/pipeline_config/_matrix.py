# @TODO: Validate limits? https://buildkite.com/docs/pipelines/configure/workflows/build-matrix#matrix-limits
# @TODO: Should adjustment classes be inner classes?

from typing import TypeAlias

from shimbboleth._model import Model, field
from ._types import ExitStatus


MatrixElementT: TypeAlias = str | int | bool
MatrixArray: TypeAlias = list[MatrixElementT]


class _AdjustmentBase(Model):
    # NB: Passing an empty string is equivalent to false.
    skip: str | bool = False
    """Whether to skip this step or not. Passing a string provides a reason for skipping this command."""

    # @TODO: JSON Converter
    soft_fail: list[ExitStatus] = field(default_factory=list)
    """Allow specified non-zero exit statuses not to fail the build."""


class ScalarAdjustment(_AdjustmentBase, Model, extra=False):
    """An adjustment to a Build Matrix scalar element (e.g. single-dimension matrix)."""

    with_value: str = field(json_alias="with")
    """An existing (or new) element to adjust"""

    # NB: other fields from base


class SingleDimensionMatrix(Model, extra=False):
    """Configuration for single-dimension Build Matrix (e.g. list of elements/adjustments)."""

    setup: list[MatrixElementT]

    adjustments: list[ScalarAdjustment] | None = None


class MultiDimensionMatrixAdjustment(_AdjustmentBase, Model):
    """An adjustment to a multi-dimension Build Matrix"""

    with_value: dict[str, list[MatrixElementT]] = field(alias="with")
    """Specification of a new or existing Build Matrix combination"""

    # NB: other fields from base


class MultiDimensionMatrix(Model, extra=False):
    """Configuration for multi-dimension Build Matrix (e.g. map of elements/adjustments)."""

    setup: dict[str, list[MatrixElementT]]
    """Maps dimension names to a lists of elements"""

    adjustments: list[MultiDimensionMatrixAdjustment] | None = None
