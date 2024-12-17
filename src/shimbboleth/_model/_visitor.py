from typing import Protocol, TypeVar, Generic, Annotated, Literal, Callable, Concatenate
from types import UnionType, GenericAlias
from shimbboleth._model.model import ModelMeta

RetT = TypeVar("RetT", covariant=True)
_AnnotationType = type(Annotated[None, None])
_LiteralType = type(Literal[None])


# @TODO: Handle Enums
# @TODO: Framework for "attaching" errors during bubble up
#   (E.g. if a field has type `list[Union[list...]])` and we complain about a single type
#       inside of the outer type being incorrect, it's a bit frustrating to diagnose)
class Visitor(Protocol, Generic[RetT]):
    visit_bool_field: Callable[Concatenate["Visitor", type[bool], ...], RetT]
    visit_int_field: Callable[Concatenate["Visitor", type[int], ...], RetT]
    visit_str_field: Callable[Concatenate["Visitor", type[str], ...], RetT]
    visit_none_field: Callable[Concatenate["Visitor", None, ...], RetT]
    visit_list_field: Callable[Concatenate["Visitor", GenericAlias, ...], RetT]
    visit_dict_field: Callable[Concatenate["Visitor", GenericAlias, ...], RetT]
    visit_union_type_field: Callable[Concatenate["Visitor", UnionType, ...], RetT]
    visit_annotated_field: Callable[Concatenate["Visitor", type, ...], RetT]
    visit_literal_field: Callable[Concatenate["Visitor", type, ...], RetT]
    visit_model_field: Callable[Concatenate["Visitor", ModelMeta, ...], RetT]

    def visit(self, objType: type, **kwargs) -> RetT:
        if objType is bool:
            return self.visit_bool_field(objType, **kwargs)
        if objType is int:
            return self.visit_int_field(objType, **kwargs)
        if objType is str:
            return self.visit_str_field(objType, **kwargs)
        if objType is None:
            return self.visit_none_field(objType, **kwargs)
        if isinstance(objType, GenericAlias):
            container_t = objType.__origin__
            if container_t is list:
                return self.visit_list_field(objType, **kwargs)
            if container_t is dict:
                keyT = objType.__args__[0]
                if keyT is str or (
                    isinstance(keyT, _AnnotationType) and keyT.__origin__ is str
                ):
                    return self.visit_dict_field(objType, **kwargs)
                raise TypeError(f"Unsupported dict key type: {keyT}")
        if isinstance(objType, UnionType):
            return self.visit_union_type_field(objType, **kwargs)
        if isinstance(objType, _LiteralType):
            return self.visit_literal_field(objType, **kwargs)
        if isinstance(objType, _AnnotationType):
            return self.visit_annotated_field(objType, **kwargs)
        if isinstance(objType, ModelMeta):
            return self.visit_model_field(objType, **kwargs)

        raise TypeError(f"Unsupported type: {objType}")
