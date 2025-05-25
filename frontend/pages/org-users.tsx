import { useState, useEffect } from 'react'
import { useRouter } from 'next/router'
import { useSession } from 'next-auth/react'
import Navbar from '../components/Navbar'
import { trpc } from '../lib/trpc'
import { useTranslations } from 'next-intl'

export default function OrgUsers() {
  const orgId = 'org1'
  const { data: session, status } = useSession()
  const utils = trpc.useUtils()
  const usersQuery = trpc.users.list.useQuery({ orgId }, { enabled: status === 'authenticated' })
  const add = trpc.users.add.useMutation()
  const remove = trpc.users.remove.useMutation()
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [role, setRole] = useState('member')

  useEffect(() => {
    if (status === 'unauthenticated') router.push('/login')
  }, [status, router])

  const t = useTranslations()

  if (status === 'loading') return <p>{t('users.loading')}</p>

  const users = usersQuery.data ?? []
  const isAdmin = users.some(u => u.email === session?.user?.email && u.role === 'admin')
  if (!isAdmin) return <p>{t('users.denied')}</p>

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault()
    await add.mutateAsync({ orgId, email, role: role as 'admin' | 'member' })
    setEmail('')
    setRole('member')
    utils.users.list.invalidate({ orgId })
  }

  async function handleRemove(uEmail: string) {
    await remove.mutateAsync({ orgId, email: uEmail })
    utils.users.list.invalidate({ orgId })
  }

  return (
    <>
      <Navbar />
      <main className="container mx-auto px-4 py-8">
        <h2 className="text-2xl font-bold mb-4">{t('users.title')}</h2>
        <form onSubmit={handleAdd} className="space-x-2 mb-4">
          <input className="border p-1" value={email} onChange={e => setEmail(e.target.value)} placeholder={t('login.email')} />
          <select className="border p-1" value={role} onChange={e => setRole(e.target.value)}>
            <option value="member">member</option>
            <option value="admin">admin</option>
          </select>
          <button className="bg-blue-600 text-white px-2 py-1 rounded" type="submit">{t('users.add')}</button>
        </form>
        <ul className="space-y-2">
          {users.map(u => (
            <li key={u.email} className="p-2 bg-white rounded shadow flex justify-between">
              <span>{u.email} {u.role}</span>
              <button className="text-red-600" onClick={() => handleRemove(u.email)}>{t('users.remove')}</button>
            </li>
          ))}
        </ul>
      </main>
    </>
  )
}
