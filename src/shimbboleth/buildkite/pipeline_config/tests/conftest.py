import pytest
from dataclasses import dataclass
from typing import TypeVar, Generic, Any

from shimbboleth.buildkite.pipeline_config import (
    BlockStep,
    InputStep,
    CommandStep,
    WaitStep,
    TriggerStep,
    GroupStep,
)
from shimbboleth._model import Model

T = TypeVar("T", bound=Model)


@dataclass(slots=True, frozen=True)
class StepTypeParam(Generic[T]):
    cls: type[T]
    ctor_defaults: dict[str, Any]

    @property
    def stepname(self) -> str:
        return self.cls.__name__.lower().removesuffix("step")

    def ctor(self, **kwargs) -> T:
        return self.cls(**{**kwargs, **self.ctor_defaults})

    def model_load(self, value: dict[str, Any]) -> T:
        return self.cls.model_load({**value, **self.dumped_default})

    @property
    def dumped_default(self) -> dict[str, Any]:
        return self.ctor().model_dump()

    @property
    def type(self) -> str:
        return self.ctor_defaults["type"]


STEP_TYPE_PARAMS = {
    "block": StepTypeParam(BlockStep, {"type": "block"}),
    "command": StepTypeParam(CommandStep, {"type": "command"}),
    "input": StepTypeParam(InputStep, {"type": "input"}),
    "wait": StepTypeParam(WaitStep, {"type": "wait"}),
    "trigger": StepTypeParam(TriggerStep, {"type": "trigger", "trigger": "trigger"}),
    "group": StepTypeParam(GroupStep, {"group": "group", "steps": [WaitStep()]}),
}
ALL_STEP_TYPE_PARAMS = [
    pytest.param(step_type_param, id=step_type_param.cls.__name__)
    for step_type_param in STEP_TYPE_PARAMS.values()
]
ALL_SUBSTEP_TYPE_PARAMS = [
    pytest.param(step_type_param, id=step_type_param.cls.__name__)
    for step_type_param in STEP_TYPE_PARAMS.values()
    if step_type_param.stepname != "group"
]


@pytest.fixture(params=ALL_STEP_TYPE_PARAMS)
def all_step_types(request) -> StepTypeParam:
    return request.param


@pytest.fixture(params=ALL_SUBSTEP_TYPE_PARAMS)
def all_substep_types(request) -> StepTypeParam:
    return request.param
