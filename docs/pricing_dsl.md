# Pricing DSL

TokenTally can compile simple pricing DSL files into JSON for easier consumption.

## Writing rules

A DSL file consists of `key=value` pairs. Lines beginning with `#` are ignored.
Values that look like JSON (numbers, lists, objects) are parsed accordingly.

Example `rules.tally`:

```
provider=openai
model=gpt-4
tokens_per_dollar=1000
```

## Compile to JSON

Use the `pricing_cli.py` tool:

```bash
python -m token_tally.pricing_cli compile rules.tally -o rules.json
```

This will produce a JSON file:

```json
{
  "provider": "openai",
  "model": "gpt-4",
  "tokens_per_dollar": 1000
}
```
