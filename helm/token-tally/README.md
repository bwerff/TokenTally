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
privateLink:
  enabled: true
```

## EU Residency

To deploy TokenTally in the EU, override `image.tag` with the EU build and specify any region-specific settings in your values file.

```yaml
image:
  repository: ghcr.io/tokentally/server
  tag: eu-latest
region: eu-west-1
```

Install with:

```bash
helm install my-tally tokentally/token-tally -f eu-values.yaml
```
Set `privateLink.enabled` to `true` when you need the service exposed via an internal load balancer for PrivateLink deployments.

