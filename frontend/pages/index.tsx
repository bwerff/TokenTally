import Link from 'next/link'
import Navbar from '../components/Navbar'
import { useTranslations } from 'next-intl'

export default function Home() {
  const t = useTranslations()
  return (
    <>
      <Navbar />
      <main className="container mx-auto px-4 py-8">
        <h2 className="text-2xl font-bold mb-4">{t('home.welcome')}</h2>
        <p className="mb-6">
          {t.rich('home.message', {
            login: chunks => <Link className="text-blue-600" href="/login">{chunks}</Link>,
            register: chunks => <Link className="text-blue-600" href="/register">{chunks}</Link>,
          })}
        </p>
      </main>
    </>
  )
}
