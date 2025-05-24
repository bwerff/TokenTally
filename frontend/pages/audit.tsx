import { trpc } from '../lib/trpc'
import Navbar from '../components/Navbar'

export default function Audit() {
  const auditQuery = trpc.audit.useQuery()
  const logs = auditQuery.data ?? []
  return (
    <>
      <Navbar />
      <main className="container mx-auto px-4 py-4">
        <h2 className="text-2xl font-bold mb-4">Audit Trail</h2>
        <ul className="space-y-2">
          {logs.map((l: any) => (
            <li key={l.event_id} className="p-2 bg-white rounded shadow">
              {l.customer_id} {l.token_count} tokens
            </li>
          ))}
        </ul>
      </main>
    </>
  )
}
