(TODO: Flesh out morex)

Features:

- Rich alias support
- Customizing a field with a validator using `Field` (not using types)
- Helpers to reduce `Field` usage in annotations

- (assumes types are correct Python-side)

Things required from pydantic:

- dataclass semantics
- loading/dumping
- type validation
- JSON Schema
- constraints (less than, not empty, pattern)
- aliases (both the raw ones and heirarchical ones)
- Discriminators
- (reading from annotations)

For heirarchical aliases:

- the converter should take in the entire input and choose, then the descriptors are simple
