import { trpc } from '../lib/trpc'
import Navbar from '../components/Navbar'

export default function Usage() {
  const usageQuery = trpc.usage.useQuery()
  const usage = usageQuery.data ?? []
  return (
    <>
      <Navbar />
      <main className="container mx-auto px-4 py-4">
        <h2 className="text-2xl font-bold mb-4">Usage Explorer</h2>
        <ul className="space-y-2">
          {usage.map((u: any) => (
            <li key={u.event_id} className="p-2 bg-white rounded shadow">
              {u.customer_id} {u.provider} {u.model} {u.units}
            </li>
          ))}
        </ul>
      </main>
    </>
  )
}
