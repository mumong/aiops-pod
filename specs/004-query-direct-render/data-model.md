# Data Model: Query Direct Render

## QueryResult

- `query_target`: original user query summary
- `collection_summary`: human-readable collection completeness
- `columns`: ordered list of `{key, label}` display columns
- `rows`: list of dictionaries keyed by column key
- `notes`: optional user-facing notes
- `missing`: list of `{field, reason}` missing-data explanations
- `sources`: list of `{tool, query}` real executed query sources

Validation rules:
- `rows` or `missing` must be present for a usable query response.
- Rows must only come from successful semantic tool results or parsed JSON derived from the same first query collection loop.
- TodoWrite and planning tools are never data sources.
- Metadata queries such as `node_uname_info` may enrich labels but must not create usage metric columns.

## Query Tool Event

- `type`: `tool_result` for usable observations
- `tool_name`: executed tool name
- `tool_args`: real tool arguments
- `status`: execution status
- `semantic_success`: domain success flag
- `result`: bounded archived observation content
- `structured`: processor metadata

Validation rules:
- Only Prometheus query tools can create metric rows.
- Failed or semantically empty Prometheus results create missing reasons, not fabricated rows.

## Query Direct State

- `query_mode`: must be `direct`
- `layer`: must be `QUERY`
- `query_result`: structured query answer passed to conclusion

Validation rules:
- Query-only shortcuts must require both direct mode and query layer.
- Non-query states must continue through existing diagnosis behavior.
