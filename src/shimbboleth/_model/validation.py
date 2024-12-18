from types import UnionType, GenericAlias
import dataclasses
from typing import Any
from shimbboleth._model.field_types import (
    MatchesRegex,
    NonEmpty,
)
from shimbboleth._model._visitor import Visitor
from shimbboleth._model.model_meta import ModelMeta


class ValidationError(ValueError):
    # @TODO: Improve this, with more info
    pass


class ValidationVisitor(Visitor[None]):
    def visit_bool(self, objType: type[bool], *, obj: Any) -> None:
        pass

    def visit_int(self, objType: type[int], *, obj: Any) -> None:
        pass

    def visit_str(self, objType: type[str], *, obj: Any) -> None:
        pass

    def visit_none(self, objType: None, *, obj: Any) -> None:
        pass

    def visit_list(self, objType: GenericAlias, *, obj: Any) -> None:
        (argT,) = objType.__args__
        for item in obj:
            self.visit(argT, obj=item)

    def visit_dict(self, objType: GenericAlias, *, obj: Any) -> None:
        for key, value in obj.items():
            keyT, valueT = objType.__args__
            self.visit(keyT, obj=key)
            self.visit(valueT, obj=value)

    def visit_union_type(self, objType: UnionType, *, obj: Any) -> None:
        # @TODO: We might want to validate UnionType, but that's pretty hard
        pass

    def visit_annotated(self, objType: type, *, obj: Any) -> None:
        for annotation in objType.__metadata__:
            if isinstance(annotation, MatchesRegex) and not annotation.regex.match(obj):
                raise ValidationError
            if annotation is NonEmpty and len(obj) == 0:
                raise ValidationError
        self.visit(objType=objType.__origin__, obj=obj)

    def visit_literal(self, objType: type, *, obj: Any) -> None:
        pass

    def visit_model(self, objType: "ModelMeta", *, obj: Any) -> None:
        fields = dataclasses.fields(objType)
        for field in fields:
            self.visit(objType=field.type, obj=getattr(obj, field.name))
