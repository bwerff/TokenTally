export async function getUsage(
  baseUrl: string,
  attempts = 3,
  backoff = 100
): Promise<any[]> {
  let delay = backoff;
  for (let i = 0; i < attempts; i++) {
    try {
      const res = await fetch(`${baseUrl}/api/trpc/usage`);
      if (!res.ok) throw new Error(`status ${res.status}`);
      const data = await res.json();
      return data.result?.data ?? [];
    } catch (err) {
      if (i === attempts - 1) throw err;
      await new Promise((r) => setTimeout(r, delay));
      delay *= 2;
    }
  }
  return [];
}
