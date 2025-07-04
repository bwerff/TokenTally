import Navbar from '../components/Navbar'
import { useTranslations } from 'next-intl'

const offers = [
  { id: 1, title: '10% off first month' },
  { id: 2, title: 'Free trial for 14 days' },
]

export default function Offers() {
  const t = useTranslations()
  return (
    <>
      <Navbar />
      <main className="container mx-auto px-4 py-8">
        <h2 className="text-2xl font-bold mb-4">{t('offers.title')}</h2>
        <ul className="space-y-2">
          {offers.map(o => (
            <li key={o.id} className="p-4 bg-white rounded shadow">{o.title}</li>
          ))}
        </ul>
      </main>
    </>
  )
}
