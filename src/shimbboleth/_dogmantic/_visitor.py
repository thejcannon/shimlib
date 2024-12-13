from typing import Protocol, TypeVar, Generic, Annotated
from types import UnionType, GenericAlias
from shimbboleth._dogmantic.model import ModelMeta

RetT = TypeVar("RetT", covariant=True)
ContextT = TypeVar("ContextT", contravariant=True)
_AnnotationType = type(Annotated[None, None])


class Visitor(Protocol, Generic[RetT, ContextT]):
    def visit_bool_field(
        self, obj: type[bool], *, context: ContextT | None = None
    ) -> RetT: ...
    def visit_int_field(
        self, obj: type[int], *, context: ContextT | None = None
    ) -> RetT: ...
    def visit_str_field(
        self, obj: type[str], *, context: ContextT | None = None
    ) -> RetT: ...
    def visit_none_field(
        self, obj: None, *, context: ContextT | None = None
    ) -> RetT: ...
    def visit_list_field(
        self, obj: GenericAlias, *, context: ContextT | None = None
    ) -> RetT: ...
    def visit_dict_field(
        self, obj: GenericAlias, *, context: ContextT | None = None
    ) -> RetT: ...
    def visit_union_type_field(
        self, obj: type[UnionType], *, context: ContextT | None = None
    ) -> RetT: ...
    def visit_annotated_field(
        self, obj: type, *, context: ContextT | None = None
    ) -> RetT: ...
    def visit_model_field(
        self, obj: ModelMeta, *, context: ContextT | None = None
    ) -> RetT: ...

    def visit(self, obj: type, *, context: ContextT | None = None) -> RetT:
        if obj is bool:
            return self.visit_bool_field(obj, context=context)
        if obj is int:
            return self.visit_int_field(obj, context=context)
        if obj is str:
            return self.visit_str_field(obj, context=context)
        if obj is None:
            return self.visit_none_field(obj, context=context)
        if isinstance(obj, GenericAlias):
            container_t = obj.__origin__
            if container_t is list:
                return self.visit_list_field(obj, context=context)
            if container_t is dict:
                keyT = obj.__args__[0]
                if keyT is str or (
                    isinstance(keyT, _AnnotationType) and keyT.__origin__ is str
                ):
                    return self.visit_dict_field(obj, context=context)
                raise TypeError(f"Unsupported dict key type: {keyT}")
        if isinstance(obj, UnionType):
            return self.visit_union_type_field(obj, context=context)
        if isinstance(obj, _AnnotationType):
            return self.visit_annotated_field(obj, context=context)
        if isinstance(obj, ModelMeta):
            return self.visit_model_field(obj, context=context)

        raise TypeError(f"Unsupported type: {obj}")
