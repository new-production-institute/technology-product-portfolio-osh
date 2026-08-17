# Contribution rules

## Data pipeline

- Run all commands from the repository root.
- Fetch the ODS mirror first: `python3 src/script/mirror_spreadsheet.py`.
- Convert the fetched Health sheet second: `python3 src/script/convert_health.py`.
- Never run conversion against a stale ODS mirror.
- Never edit mirrored or generated data manually.
- Commit the updated ODS and generated JavaScript together.
- Stop when either script fails; do not commit partial output.

## Roles

### Backend developer

- May change any repository file.
- Owns specifications, scripts, data mappings, and generated datasets.
- Must run the complete data pipeline after data-related changes.

### Front-end developer

- Works only on the `website` branch, where the static website is generated.
- May change presentation only: layouts, styles, typography, colors, and visual assets.
- May consume generated data but must not edit it.
- Must not change `spec/`, `src/script/`, `res/var/data/`, or `res/data/`.
- Must not change schemas, mappings, pipeline behavior, or data semantics.
