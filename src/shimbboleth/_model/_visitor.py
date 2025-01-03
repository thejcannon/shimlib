from typing import (
    Protocol,
    TypeVar,
    Generic,
    Annotated,
    Literal,
    Callable,
    Concatenate,
    Any,
)
import re
from typing_extensions import TypeAliasType
from types import UnionType, GenericAlias
from shimbboleth._model.model_meta import ModelMeta

RetT = TypeVar("RetT", covariant=True)
_AnnotationType = type(Annotated[None, None])
_GenericUnionType = type(Annotated[None, None] | None)
_LiteralType = type(Literal[None])


# @TODO: Handle Enums
# @TODO: Framework for "attaching" errors during bubble up
#   (E.g. if a field has type `list[Union[list...]])` and we complain about a single type
#       inside of the outer type being incorrect, it's a bit frustrating to diagnose)
class Visitor(Protocol, Generic[RetT]):
    visit_bool: Callable[Concatenate["Visitor", type[bool], ...], RetT]
    visit_int: Callable[Concatenate["Visitor", type[int], ...], RetT]
    visit_str: Callable[Concatenate["Visitor", type[str], ...], RetT]
    visit_none: Callable[Concatenate["Visitor", None, ...], RetT]
    visit_list: Callable[Concatenate["Visitor", GenericAlias, ...], RetT]
    visit_dict: Callable[Concatenate["Visitor", GenericAlias, ...], RetT]
    visit_union_type: Callable[Concatenate["Visitor", UnionType, ...], RetT]
    visit_literal: Callable[Concatenate["Visitor", type, ...], RetT]
    visit_annotated: Callable[Concatenate["Visitor", type, ...], RetT]
    visit_pattern: Callable[Concatenate["Visitor", re.Pattern, ...], RetT]
    visit_type_alias_type: Callable[Concatenate["Visitor", TypeAliasType, ...], RetT]
    visit_model: Callable[Concatenate["Visitor", ModelMeta, ...], RetT]

    def visit(self, objType: Any, **kwargs) -> RetT:
        if objType is bool:
            return self.visit_bool(objType, **kwargs)
        if objType is int:
            return self.visit_int(objType, **kwargs)
        if objType is str:
            return self.visit_str(objType, **kwargs)
        if objType is None or objType is type(None):
            return self.visit_none(objType, **kwargs)
        if isinstance(objType, GenericAlias):
            container_t = objType.__origin__
            if container_t is list:
                return self.visit_list(objType, **kwargs)
            if container_t is dict:
                keyT = objType.__args__[0]
                if keyT is str or (
                    isinstance(keyT, _AnnotationType) and keyT.__origin__ is str
                ):
                    return self.visit_dict(objType, **kwargs)
                raise TypeError(f"Unsupported dict key type: {keyT}")
        if isinstance(objType, (UnionType, _GenericUnionType)):
            return self.visit_union_type(objType, **kwargs)
        if isinstance(objType, _LiteralType):
            return self.visit_literal(objType, **kwargs)
        if isinstance(objType, _AnnotationType):
            return self.visit_annotated(objType, **kwargs)
        if isinstance(objType, TypeAliasType):
            return self.visit_type_alias_type(objType, **kwargs)
        if isinstance(objType, ModelMeta):
            return self.visit_model(objType, **kwargs)
        if objType is re.Pattern:
            return self.visit_pattern(objType, **kwargs)

        raise TypeError(f"Unsupported type: {objType}")
