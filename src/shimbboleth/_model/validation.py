from types import UnionType, GenericAlias
import dataclasses
from typing import Any
from shimbboleth._model.model import ModelMeta
from shimbboleth._model.field_types import (
    Description,
    Examples,
    MatchesRegex,
    NonEmpty,
)
from shimbboleth._model._visitor import Visitor


class ValidationError(TypeError):
    # @TODO: Improve this
    pass


class _Validator(Visitor[None]):
    def visit_bool_field(self, objType: type[bool], *, obj: Any) -> None:
        if type(obj) is not bool:
            raise ValidationError

    def visit_int_field(self, objType: type[int], *, obj: Any) -> None:
        if type(obj) is not int:
            raise ValidationError

    def visit_str_field(self, objType: type[str], *, obj: Any) -> None:
        if type(obj) is not str:
            raise ValidationError

    def visit_none_field(self, objType: None, *, obj: Any) -> None:
        if obj is not None:
            raise ValidationError

    def visit_list_field(self, objType: GenericAlias, *, obj: Any) -> None:
        if type(obj) is not list:
            raise ValidationError
        (argT,) = objType.__args__
        for item in obj:
            self.visit(argT, obj=item)

    def visit_dict_field(self, objType: GenericAlias, *, obj: Any) -> None:
        if type(obj) is not dict:
            raise ValidationError
        keyT, valueT = objType.__args__
        for key, value in obj.items():
            self.visit(keyT, obj=key)
            self.visit(valueT, obj=value)

    def visit_union_type_field(
        self, objType: UnionType, *, obj: Any
    ) -> None:
        for t in objType.__args__:
            try:
                return self.visit(t, obj=obj)
            except ValidationError:
                continue
        raise ValidationError

    def visit_annotated_field(self, objType: type, *, obj: Any) -> None:
        baseType = objType.__origin__
        self.visit(baseType, obj=obj)
        for annotation in objType.__metadata__:
            if isinstance(annotation, MatchesRegex) and not annotation.regex.match(obj):
                raise ValidationError
            if annotation is NonEmpty and len(obj) == 0:
                raise ValidationError


    def visit_literal_field(self, objType: type, *, obj: Any) -> None:
        for possibility in objType.__args__:
            if obj is possibility:  # NB: compare bool/int by identity
                return
            if isinstance(possibility, str) and isinstance(obj, str):
                if obj == possibility:
                    return
        raise ValidationError

    def _get_field_type_schema(self, field: dataclasses.Field) -> None:
        json_converter = field.metadata.get("json_converter", None)
        if json_converter:
            input_type = json_converter.__annotations__["value"]
            output_type = json_converter.__annotations__["return"]
            assert (
                output_type == field.type
            ), f"{output_type=} {field.type=}"  # @TODO: what about `Annotated`?
        return None

    def _get_field_schema(self, field: dataclasses.Field) -> None:
        return None

    def visit_model_field(self, objType: ModelMeta, *, obj: Any) -> None:
        if not isinstance(obj, objType):
            raise ValidationError
        for field in dataclasses.fields(objType):
            value = getattr(obj, field.name)
            self.visit(field.type, obj=value)


def validate(*, objType: type, obj: Any) -> None:
    return _Validator().visit(objType, obj=obj)
