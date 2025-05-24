export async function getUsage(baseUrl: string): Promise<any[]> {
  const res = await fetch(`${baseUrl}/api/trpc/usage`);
  if (!res.ok) throw new Error('failed to fetch usage');
  const data = await res.json();
  return data.result?.data ?? [];
}
