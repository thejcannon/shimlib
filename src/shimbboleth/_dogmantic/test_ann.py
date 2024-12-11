from typing import Annotated, ClassVar
from pydantic import BaseModel, Field, field_validator, AfterValidator, ValidatorFunctionWrapHandler

from shimbboleth._dogmantic.converter import from_json_converter

def Description(description: str, /):
    return Field(description=description)

def Examples(*examples):
    return Field(examples=list(examples))

def farts(value: str) -> bool:
    print(value)
    return True

def others(value: str) -> str:
    print(value)
    return value

def bar(sosos, handler):
    return None

class Model(BaseModel):
    field: Annotated[bool, Description(""), Examples()] = False

    field2: str = Field(
        default="",
        json_converter=bar
    )



    _field2_converter: ClassVar = from_json_converter("field2")(bar)

print(Model.model_json_schema())

Model.model_validate({"field": "farts"})
