

# Buildkite Pipeline Config Types

This module provides rich Python types for working with Buildkite pipeline configurations.

The primary goal is to enable reading existing pipeline YAML files into strongly-typed Python objects for analysis and transformation, with the ability to write them back out if needed.

## Key Features

- Full type coverage of the [Buildkite Pipeline Schema](https://github.com/buildkite/pipeline-schema)
- Pydantic models for robust validation and (de)serialization
- Support for all pipeline step types (Command, Wait, Block, Input, Trigger, Group)
- Field aliases to support common alternative names (e.g. `name`/`label`)
- Automatic canonicalization of certain field types

## Intent and Limitations

This module is primarily designed for:

- Reading and parsing existing pipeline configurations
- Programmatically analyzing pipeline structure
- Making targeted modifications to pipelines

It is not specifically designed for:

- Creating pipelines from scratch (though possible)
- Perfectly round-trip preserving pipeline files
- Complete validation of all Buildkite pipeline rules

## Usage

```python
from shimbboleth.buildkite.pipeline_config import BuildkitePipeline
import yaml

# Read an existing pipeline
with open('pipeline.yml') as f:
    pipeline = BuildkitePipeline.model_validate(yaml.safe_load(f))

# Access typed fields
for step in pipeline.steps:
    if isinstance(step, CommandStep):
        print(f"Command step: {step.label}")

# Make changes
pipeline.steps[1].label = "Updated label"
pipeline.steps[1].command = ["./my_script.sh", "--flag", "value"]

# And write it back out
with open('pipeline.yml', 'w') as f:
    yaml.dump(pipeline.model_dump(exclude_none=True), f)
```

## Type Canonicalization

To simplify working with pipeline configs, certain fields are automatically canonicalized to consistent types:

- String or list fields are normalized to lists (e.g. `artifact_paths`, `branches`)
- Boolean-like strings (`"true"`, `"false"`) are converted to Python bools
- Agent query rules are normalized to dictionaries

For example:
```python
step = CommandStep(
    artifact_paths="logs/*",  # Will be converted to ["logs/*"]
    branches="main",          # Will be converted to ["main"]
)
```

## Field Validation

While not comprehensive compared to Buildkite's server-side validation, the module performs some basic validation. For example:

- Step `key` fields cannot be UUIDs
- Required fields are enforced
- Enum values are validated
- Basic type checking and coercion

Contributions to expand validation coverage are welcome!

## Testing

- The schema is tested for compatibility against the official [Buildkite Pipeline Schema](https://github.com/buildkite/pipeline-schema) to ensure ongoing compatibility.
- As well as Python-specific tests for `shimbboleth` additions (e.g. field aliasing)
