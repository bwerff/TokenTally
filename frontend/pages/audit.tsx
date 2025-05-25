import { trpc } from '../lib/trpc'
import Navbar from '../components/Navbar'
import { useTranslations } from 'next-intl'

export default function Audit() {
  const auditQuery = trpc.audit.useQuery()
  const logs = auditQuery.data ?? []
  const t = useTranslations()
  return (
    <>
      <Navbar />
      <main className="container mx-auto px-4 py-4">
        <h2 className="text-2xl font-bold mb-4">{t('audit.title')}</h2>
        <ul className="space-y-2">
          {logs.map((l: any) => (
            <li key={l.event_id} className="p-2 bg-white rounded shadow">
              {l.customer_id} {t('audit.tokens', { count: l.token_count })}
            </li>
          ))}
        </ul>
      </main>
    </>
  )
}
