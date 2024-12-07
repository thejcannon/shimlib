from typing import Literal, Annotated, Pattern
from typing_extensions import TypeAliasType


from pydantic import BaseModel, Field

from shimbboleth.buildkite.pipeline_config._types import LooseBoolT


class TextInput(BaseModel, extra="forbid"):
    """
    For Input Step: https://buildkite.com/docs/pipelines/input-step#text-input-attributes
    For Block Step: https://buildkite.com/docs/pipelines/block-step#text-input-attributes
    """

    key: str = Field(
        description="The meta-data key that stores the field's input",
        pattern="^[a-zA-Z0-9-_]+$",
        examples=["release-name"],
    )

    hint: str | None = Field(
        default=None,
        description="The explanatory text that is shown after the label",
        examples=["What's the code name for this release? :name_badge:"],
    )
    required: LooseBoolT = Field(
        default=True, description="Whether the field is required for form submission"
    )
    default: str | None = Field(
        default=None,
        description="The value that is pre-filled in the text field",
        examples=["Flying Dolphin"],
    )
    format: Pattern | None = Field(
        default=None,
        description="The format must be a regular expression implicitly anchored to the beginning and end of the input and is functionally equivalent to the HTML5 pattern attribute.",
        examples=["[0-9a-f]+"],
    )
    text: str | None = Field(
        default=None, description="The text input name", examples=["Release Name"]
    )


class SelectOption(BaseModel, extra="forbid"):
    label: str = Field(
        description="The text displayed on the select list item", examples=["Stable"]
    )
    value: str = Field(
        description="The value to be stored as meta-data", examples=["stable"]
    )

    hint: str | None = Field(
        default=None,
        description="The text displayed directly under the select field's label",
        examples=["Which release stream does this belong in? :fork:"],
    )
    required: LooseBoolT = Field(
        default=True, description="Whether the field is required for form submission"
    )


# @TODO: If `multiple` is falsey, then `default` cant be a list of strings
class SelectInput(BaseModel, extra="forbid"):
    """
    For Input Step: https://buildkite.com/docs/pipelines/input-step#select-input-attributes
    For Block Step: https://buildkite.com/docs/pipelines/block-step#select-input-attributes
    """

    key: str = Field(
        description="The meta-data key that stores the field's input",
        pattern="^[a-zA-Z0-9-_]+$",
        examples=["release-stream"],
    )
    # @TODO: Change validation error to: "`options` can't be empty"
    options: list[SelectOption] = Field(min_length=1)

    default: str | list[str] | None = Field(
        default=None,
        description="The value of the option(s) that will be pre-selected in the dropdown",
        examples=["beta", ["alpha", "beta"]],
    )
    hint: str | None = Field(
        default=None,
        description="The explanatory text that is shown after the label",
        examples=["What's the code name for this release? :name_badge:"],
    )
    multiple: LooseBoolT = Field(
        default=False, description="Whether more than one option may be selected"
    )
    required: LooseBoolT = Field(
        default=True, description="Whether the field is required for form submission"
    )
    select: str | None = Field(
        default=None, description="The text input name", examples=["Release Stream"]
    )


FieldsT = TypeAliasType(
    "FieldsT",
    Annotated[
        # @TODO: Use discriminator
        list[TextInput | SelectInput],
        Field(
            description="A list of input fields required to be filled out before unblocking the step"
        ),
    ],
)
