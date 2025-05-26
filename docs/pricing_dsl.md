# Pricing DSL

TokenTally supports a simple domain specific language for defining markup rules.
Each line in a DSL file defines one rule with the following fields:

```
provider model markup effective_date
```

- **provider** – identifier for the LLM provider (e.g. `openai`).
- **model** – model name (`gpt-4`, `claude-3`, ...).
- **markup** – decimal or percent value (e.g. `0.2` or `20%`).
- **effective_date** – start date in `YYYY-MM-DD` format.

Lines beginning with `#` are treated as comments and ignored.

Example:

```
# provider  model      markup  start date
openai      gpt-4      20%     2024-01-01
anthropic   claude-3   0.1     2024-06-01
```

The parser converts the text into a list of rule dictionaries, each containing
`id`, `provider`, `model`, `markup`, and `effective_date` fields. The `id` field
is generated automatically using the provider, model and date.
