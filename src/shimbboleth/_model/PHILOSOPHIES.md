## Philosohpies

- Data is assumed to be type-correct in Python APIs (e.g. only type-validate when taking in JSON)
- Data restrictions (like "must not be empty") are a property of a field's **type** (e.g. the field should have type `Annotated[..., NonEmpty]`)
  and not a property of the field itself.
- Field types should be "reduced" to their lowest-common-denominator. (E.g. `str | list[str]` should be `list[str]` when applicable)
  (and JSON loaders can be used if the input data allows `str | list[str]`)
