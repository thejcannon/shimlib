import dataclasses
import uuid
import re
from typing import Any
from shimbboleth._model.model import Model
from functools import singledispatch


@singledispatch
def dump(obj):
    # NB: Dispatched manually, so we can avoid ciruclar definition with `Model.model_dump`
    if isinstance(obj, Model):
        return obj.model_dump()
    return obj


@dump.register
def dump_uuid(obj: uuid.UUID):
    return str(obj)


@dump.register
def dump_list(obj: list):
    return [dump(item) for item in obj]


@dump.register
def dump_dict(obj: dict):
    return {dump(key): dump(value) for key, value in obj.items()}


@dump.register
def dump_pattern(obj: re.Pattern):
    return obj.pattern


def dump_model(obj: Model) -> dict[str, Any]:
    ret = {}
    for field in dataclasses.fields(obj):
        value = getattr(obj, field.name)
        if value == field.default or (
            field.default_factory is not dataclasses.MISSING
            and value == field.default_factory()
        ):
            continue

        json_dumper = field.metadata.get("json_dumper", None)
        if json_dumper:
            dumped_value = json_dumper(value)
        else:
            dumped_value = dump(value)

        if dumped_value is not None:
            key = field.metadata.get("json_alias", field.name)
            ret[key] = dumped_value

    if hasattr(obj, "_extra") and obj._extra:
        ret.update(obj._extra)

    return ret
