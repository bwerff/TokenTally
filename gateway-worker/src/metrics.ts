export class Counter {
  private value: number = 0;
  inc(amount: number = 1): void {
    this.value += amount;
  }
  get(): number {
    return this.value;
  }
}

const latency: Record<string, Counter> = {};

export function recordLatency(provider: string, ms: number): void {
  if (!latency[provider]) latency[provider] = new Counter();
  latency[provider].inc(ms);
}

export function metricsText(): string {
  const lines: string[] = [];
  for (const [provider, counter] of Object.entries(latency)) {
    lines.push(`gateway_request_latency_ms_total{provider="${provider}"} ${counter.get()}`);
  }
  return lines.join('\n') + '\n';
}

export function resetMetrics(): void {
  for (const key of Object.keys(latency)) {
    delete latency[key];
  }
}
