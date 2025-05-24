# TokenTally Helm Chart

This chart deploys the TokenTally gateway and billing server in a private Kubernetes cluster.

```bash
helm repo add tokentally https://example.com/charts
helm install my-tally tokentally/token-tally
```

Values can be overridden via `--set` or a custom `values.yaml`:

```yaml
image:
  repository: ghcr.io/tokentally/server
  tag: latest
service:
  type: LoadBalancer
```
