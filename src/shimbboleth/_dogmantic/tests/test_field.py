from shimbboleth._dogmantic.field import Model, field
import dataclasses


def test_something():
    @dataclasses.dataclass
    class MyModel(Model):
        bare_field: str
        myfield: str = field(default="")

    MyModel(bare_field="").bare_field
    print(dataclasses.fields(MyModel))
