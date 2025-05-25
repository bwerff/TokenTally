# TokenTally Go Client

Retrieve usage information from TokenTally.

```go
usage, err := tokentally.GetUsage("https://example.com")
```

## Retry behaviour

`GetUsage` automatically retries up to three times with exponential backoff.
