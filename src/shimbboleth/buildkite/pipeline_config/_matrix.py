# @TODO: Validate limits? https://buildkite.com/docs/pipelines/configure/workflows/build-matrix#matrix-limits

from typing import Literal, Any, Annotated, ClassVar
from typing_extensions import TypeAliasType


from pydantic import (
    BaseModel,
    Field,
    model_validator,
)

from shimbboleth.buildkite.pipeline_config._types import SoftFailT, SkipT


# @TODO: Validation: "Each item within a `matrix` must be either a string, boolean or integer"
MatrixElementT = TypeAliasType("MatrixElementT", str | int | bool)
SimpleMatrixT = Annotated[
    list[MatrixElementT],
    Field(
        description="List of elements for simple single-dimension Build Matrix",
        examples=[["linux", "freebsd"]],
    ),
]


class SingleDimensionMatrixAdjustment(BaseModel, extra="forbid"):
    """An adjustment to a single-dimension Build Matrix"""

    with_value: Annotated[
        str,
        Field(
            description="An existing or new element for single-dimension Build Matrix"
        ),
    ] = Field(alias="with")

    skip: SkipT | None = None
    soft_fail: SoftFailT | None = None


class SingleDimensionMatrix(BaseModel, extra="forbid"):
    """Configuration for single-dimension Build Matrix"""

    setup: Annotated[
        list[MatrixElementT],
        Field(
            description="List of elements for single-dimension Build Matrix",
            examples=[["linux", "freebsd"]],
        ),
    ]

    adjustments: list[SingleDimensionMatrixAdjustment] | None = Field(
        default=None, description="List of single-dimension Build Matrix adjustments"
    )


class MultiDimensionMatrixAdjustment(BaseModel, extra="forbid"):
    """An adjustment to a multi-dimension Build Matrix"""

    with_value: Annotated[
        dict[
            Annotated[
                str,
                Field(
                    description="Build Matrix dimension name",
                    # pattern="^[a-zA-Z0-9_]+$",
                ),
            ],
            Annotated[
                MatrixElementT,
                Field(description="Build Matrix dimension element"),
            ],
        ],
        Field(
            description="Specification of a new or existing Build Matrix combination",
            examples=[{"os": "linux", "arch": "arm64"}],
        ),
    ] = Field(alias="with")

    skip: SkipT | None = None
    soft_fail: SoftFailT | None = None


class MultiDimensionMatrix(BaseModel, extra="forbid"):
    """Configuration for multi-dimension Build Matrix"""

    setup: Annotated[
        dict[
            Annotated[
                str,
                Field(
                    description="Build Matrix dimension name",
                    pattern="^[a-zA-Z0-9_]+$",
                ),
            ],
            Annotated[
                list[MatrixElementT],
                Field(description="List of elements for this Build Matrix dimension"),
            ],
        ],
        Field(
            description="Mapping of Build Matrix dimension names to their lists of elements",
            examples=[{"arch": ["arm64", "riscv"], "os": ["linux", "freebsd"]}],
        ),
    ]

    adjustments: list[MultiDimensionMatrixAdjustment] | None = Field(
        default=None, description="List of multi-dimension Build Matrix adjustments"
    )
