import { useState } from 'react'
import { trpc } from '../lib/trpc'
import Navbar from '../components/Navbar'
import { useTranslations } from 'next-intl'

export default function Usage() {
  const [start, setStart] = useState('')
  const [end, setEnd] = useState('')
  const [customer, setCustomer] = useState('')
  const [params, setParams] = useState({})

  const usageQuery = trpc.usage.useQuery(params)
  const usage = usageQuery.data ?? []
  const customers = Array.from(new Set(usage.map((u: any) => u.customer_id)))

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setParams({
      start: start || undefined,
      end: end || undefined,
      customer: customer || undefined,
    })
  }

  const t = useTranslations()
  return (
    <>
      <Navbar />
      <main className="container mx-auto px-4 py-4">
        <h2 className="text-2xl font-bold mb-4">Usage Explorer</h2>
        <form onSubmit={handleSubmit} className="space-x-2 mb-4">
          <input
            type="date"
            value={start}
            onChange={e => setStart(e.target.value)}
            className="border p-1 rounded"
          />
          <input
            type="date"
            value={end}
            onChange={e => setEnd(e.target.value)}
            className="border p-1 rounded"
          />
          <select
            value={customer}
            onChange={e => setCustomer(e.target.value)}
            className="border p-1 rounded"
          >
            <option value="">All Customers</option>
            {customers.map(c => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
          <button className="bg-blue-600 text-white px-3 py-1 rounded" type="submit">
            Apply
          </button>
        </form>
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
