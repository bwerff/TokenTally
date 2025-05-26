# Pricing DSL

TokenTally supports a small domain specific language (DSL) for pricing rules. Each
rule describes a markup to apply to usage events based on provider and model.
Rules are compiled into the SQLite `markup_rules.db` used at runtime.

## Rule syntax

```
rule "<id>" {
    provider = "<llm provider>"
    model    = "<model name>"
    markup   = <decimal markup>
    effective_date = "YYYY-MM-DD"
}
```

- `markup` is a decimal fraction. `0.2` adds a 20% markup to the provider's base
  price.
- `effective_date` controls when the rule becomes active.

Multiple rules can be defined in a single file. A later `effective_date` takes
precedence when more than one rule matches.

## Compiling rules

Use the helper command to compile the DSL into `markup_rules.db`:

```bash
python -m token_tally.pricing_dsl path/to/rules.tally
```

This parses the file, validates each rule and writes them into the SQLite store.
At runtime the gateway looks up the active rule for each event.
