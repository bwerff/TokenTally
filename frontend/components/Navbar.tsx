import Link from 'next/link'
import { useRouter } from 'next/router'
import { useTranslations } from 'next-intl'

export default function Navbar() {
  const t = useTranslations()
  const router = useRouter()

  function changeLocale(e: React.ChangeEvent<HTMLSelectElement>) {
    router.push(router.pathname, router.asPath, { locale: e.target.value })
  }

  return (
    <nav className="bg-white shadow mb-6">
      <div className="container mx-auto px-4 py-4 flex justify-between items-center">
        <h1 className="text-xl font-semibold">{t('tokenTally')}</h1>
        <div className="space-x-4 flex items-center">
          <Link className="text-blue-600" href="/offers">{t('navbar.offers')}</Link>
          <Link className="text-blue-600" href="/upload-receipt">{t('navbar.upload')}</Link>
          <Link className="text-blue-600" href="/usage">{t('navbar.usage')}</Link>
          <Link className="text-blue-600" href="/audit">{t('navbar.audit')}</Link>
          <select onChange={changeLocale} value={router.locale} className="border ml-4 p-1">
            <option value="en">EN</option>
            <option value="fr">FR</option>
          </select>
        </div>
      </div>
    </nav>
  )
}
