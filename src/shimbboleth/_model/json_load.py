from types import UnionType, GenericAlias
import dataclasses
from typing import Any
import uuid
import re
from shimbboleth._model.model import ModelMeta
from typing_extensions import TypeAliasType
from shimbboleth._model._visitor import Visitor
import logging

LOG = logging.getLogger()


class ExtrasNotAllowedError(TypeError):
    pass


class NotAValidUUIDError(TypeError):
    pass


class WrongTypeError(TypeError):
    def __init__(self, expected, obj):
        super().__init__(f"Expected {expected}, got {type(obj)}")


class JSONLoadVisitor(Visitor[Any]):
    def visit_bool(self, objType: type[bool], *, obj: Any) -> bool:
        if type(obj) is not bool:
            raise WrongTypeError(objType, obj)
        return obj

    def visit_int(self, objType: type[int], *, obj: Any) -> int:
        if type(obj) is not int:
            raise WrongTypeError(objType, obj)
        return obj

    def visit_str(self, objType: type[str], *, obj: Any) -> str:
        if type(obj) is not str:
            raise WrongTypeError(objType, obj)
        return obj

    def visit_uuid(self, objType: type[uuid.UUID], *, obj: Any) -> uuid.UUID:
        if not isinstance(obj, str):
            raise WrongTypeError(objType, obj)
        try:
            return uuid.UUID(obj)
        except ValueError:
            raise NotAValidUUIDError(obj)

    def visit_none(self, objType: None, *, obj: Any) -> None:
        if obj is not None:
            raise WrongTypeError(objType, obj)
        return None

    def visit_list(self, objType: GenericAlias, *, obj: Any) -> list:
        if type(obj) is not list:
            raise WrongTypeError(list, obj)
        (argT,) = objType.__args__
        return [self.visit(argT, obj=item) for item in obj]

    def visit_dict(self, objType: GenericAlias, *, obj: Any) -> dict[str, Any]:
        if type(obj) is not dict:
            raise WrongTypeError(dict, obj)
        keyT, valueT = objType.__args__
        return {
            self.visit(keyT, obj=key): self.visit(valueT, obj=value)
            if valueT is not Any
            else value
            for key, value in obj.items()
        }

    def visit_union_type(self, objType: UnionType, *, obj: Any) -> Any:
        for t in objType.__args__:
            try:
                return self.visit(t, obj=obj)
            except TypeError as e:
                LOG.debug(f"{e=} for {t=}")
                continue
        raise WrongTypeError(objType, obj)

    def visit_literal(self, objType: type, *, obj: Any) -> Any:
        for possibility in objType.__args__:
            if (
                obj is possibility
            ):  # NB: compare bool/int by identity (since `bool` inherits from `int`)
                return obj
            if isinstance(possibility, str) and isinstance(obj, str):
                if obj == possibility:
                    return obj
        raise WrongTypeError(objType, obj)

    def visit_annotated(self, objType: type, *, obj: Any) -> Any:
        baseType = objType.__origin__
        return self.visit(baseType, obj=obj)

    def visit_pattern(self, objType: type[re.Pattern], *, obj: Any) -> re.Pattern:
        if not isinstance(obj, str):
            raise WrongTypeError(objType, obj)
        try:
            return re.compile(obj)
        except re.error:
            raise WrongTypeError(objType, obj)

    def visit_type_alias_type(self, field: TypeAliasType, *, obj: Any) -> Any:
        return self.visit(field.__value__, obj=obj)

    def visit_model_field(self, field: dataclasses.Field, *, obj: Any) -> Any:
        expected_type = field.type
        json_converter = field.metadata.get("json_converter", None)
        if json_converter:
            expected_type = json_converter.__annotations__["value"]

        value = self.visit(expected_type, obj=obj)

        if json_converter:
            value = json_converter(value)

        return value

    def visit_model(self, objType: ModelMeta, *, obj: Any) -> Any:
        if not isinstance(obj, dict):
            raise WrongTypeError(dict, obj)

        local_obj = obj
        for field_alias_name, field_alias in objType.__field_aliases__.items():
            if field_alias_name in obj:
                if local_obj is obj:
                    local_obj = obj.copy()

                value = local_obj.pop(field_alias_name)
                if (
                    field_alias.json_mode == "prepend"
                    or local_obj.get(field_alias.alias_of) is None
                ):
                    local_obj[field_alias.alias_of] = value

        init_fields = {field for field in dataclasses.fields(objType) if field.init}
        field_names = {
            field.metadata.get("json_alias", field.name) for field in init_fields
        }
        init_kwargs = {
            key: value for key, value in local_obj.items() if key in field_names
        }

        for field in init_fields:
            json_alias = field.metadata.get("json_alias")
            if json_alias and json_alias in init_kwargs:
                init_kwargs[field.name] = init_kwargs.pop(json_alias)

        extras = {
            key: value for key, value in local_obj.items() if key not in field_names
        }
        if extras and not objType.__allow_extra_properties__:
            # @TODO: Include more info
            raise ExtrasNotAllowedError(extras)

        for field in init_fields:
            if field.name in init_kwargs:
                init_kwargs[field.name] = self.visit_model_field(
                    field, obj=init_kwargs[field.name]
                )
            else:
                json_default = field.metadata.get("json_default", dataclasses.MISSING)
                if json_default is not dataclasses.MISSING:
                    init_kwargs[field.name] = json_default

        instance = objType(**init_kwargs)
        if objType.__allow_extra_properties__:
            instance._extra = extras

        return instance
