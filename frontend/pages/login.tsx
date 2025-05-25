import { useState } from 'react'
import { useRouter } from 'next/router'
import Navbar from '../components/Navbar'
import { signIn } from 'next-auth/react'
import { useTranslations } from 'next-intl'

export default function Login() {
  const router = useRouter()
  const t = useTranslations()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const res = await signIn('credentials', {
      redirect: false,
      email,
      password,
    })
    if (res?.error) {
      setError(t('login.invalid'))
    } else {
      router.push('/offers')
    }
  }

  return (
    <>
      <Navbar />
      <main className="container mx-auto px-4 py-8">
        <h2 className="text-2xl font-bold mb-4">{t('login.title')}</h2>
        {error && <p className="text-red-600 mb-2">{error}</p>}
        <form onSubmit={handleSubmit} className="space-y-4 max-w-sm">
          <div>
            <label className="block mb-1">{t('login.email')}</label>
            <input className="border rounded w-full p-2" value={email} onChange={e => setEmail(e.target.value)} type="email" required />
          </div>
          <div>
            <label className="block mb-1">{t('login.password')}</label>
            <input className="border rounded w-full p-2" value={password} onChange={e => setPassword(e.target.value)} type="password" required />
          </div>
          <button className="bg-blue-600 text-white px-4 py-2 rounded" type="submit">{t('login.submit')}</button>
        </form>
      </main>
    </>
  )
}
