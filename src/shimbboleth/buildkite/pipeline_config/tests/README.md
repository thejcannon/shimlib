# Pipeline Config Tests

This directory contains test files for validating Buildkite pipeline configurations. The tests serve two main purposes:

1. **Pipeline Validation**: Test files will be uploaded to Buildkite (via a planned smoke-test) to verify they are valid pipeline configurations. This ensures our schema matches Buildkite's actual requirements.

2. **Round-Trip Testing**: We verify that pipeline configurations maintain their integrity when:
   - Parsed from YAML into our internal representation
   - Converted back to YAML
   - (Future) Uploaded to Buildkite for validation

This round-trip testing ensures that our schema and transformations preserve all essential pipeline information.