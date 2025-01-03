from typing import Annotated, TypeAlias
import re
from shimbboleth._model import MatchesRegex, field, Model, NonEmptyList
from ._types import bool_from_json
from ._types import list_str_from_json
from ._base import StepBase

MetaDataKey: TypeAlias = Annotated[str, MatchesRegex("^[a-zA-Z0-9-_]+$")]


class TextInput(Model, extra=False):
    """
    For Input Step: https://buildkite.com/docs/pipelines/input-step#text-input-attributes
    For Block Step: https://buildkite.com/docs/pipelines/block-step#text-input-attributes
    """

    key: MetaDataKey
    """The meta-data key that stores the field's input"""

    hint: str | None = None
    """The explanatory text that is shown after the label"""

    required: bool = field(default=True, json_converter=bool_from_json)
    """Whether the field is required for form submission"""

    default: str | None = None
    """The value that is pre-filled in the text field"""

    format: re.Pattern | None = None
    """The format must be a regular expression implicitly anchored to the beginning and end of the input and is functionally equivalent to the HTML5 pattern attribute."""

    text: str | None = None
    """The text input name"""


class SelectOption(Model, extra=False):
    label: str
    """The text displayed on the select list item"""

    value: str
    """The value to be stored as meta-data"""

    hint: str | None = None
    """The text displayed directly under the select field's label"""

    required: bool = field(default=True, json_converter=bool_from_json)
    """Whether the field is required for form submission"""


# @TODO: If `multiple` is falsey, then `default` cant be a list of strings
class SelectInput(Model, extra=False):
    """
    For Input Step: https://buildkite.com/docs/pipelines/input-step#select-input-attributes
    For Block Step: https://buildkite.com/docs/pipelines/block-step#select-input-attributes
    """

    key: MetaDataKey
    """The meta-data key that stores the field's input"""

    options: NonEmptyList[list[SelectOption]]

    default: str | list[str] | None = None
    """The value of the option(s) that will be pre-selected in the dropdown"""

    hint: str | None = None
    """The explanatory text that is shown after the label"""

    multiple: bool = field(default=False, json_converter=bool_from_json)
    """Whether more than one option may be selected"""

    required: bool = field(default=True, json_converter=bool_from_json)
    """Whether the field is required for form submission"""

    select: str | None = None
    """The text input name"""


def input_from_json(
    value: list[TextInput | SelectInput],
) -> list[TextInput | SelectInput]:
    return []


class InteractiveStepBase(StepBase, extra=False):
    """
    (The base of both Input and Block steps)
    """

    branches: list[str] = field(default_factory=list, json_converter=list_str_from_json)
    """Which branches will include this step in their builds"""

    fields: list[TextInput | SelectInput] = field(
        default_factory=list, json_converter=input_from_json
    )
    """A list of input fields required to be filled out before unblocking the step"""

    prompt: str | None = None
    """The instructional message displayed in the dialog box when the unblock step is activated"""
