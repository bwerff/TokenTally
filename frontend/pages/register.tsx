import { useState } from 'react'
import { useRouter } from 'next/router'
import Navbar from '../components/Navbar'
import { register } from '../lib/api'

export default function Register() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    try {
      await register(email, password)
      router.push('/offers')
    } catch (err) {
      setError('Registration failed')
    }
  }

  return (
    <>
      <Navbar />
      <main className="container mx-auto px-4 py-8">
        <h2 className="text-2xl font-bold mb-4">Register</h2>
        {error && <p className="text-red-600 mb-2">{error}</p>}
        <form onSubmit={handleSubmit} className="space-y-4 max-w-sm">
          <div>
            <label className="block mb-1">Email</label>
            <input className="border rounded w-full p-2" value={email} onChange={e => setEmail(e.target.value)} type="email" required />
          </div>
          <div>
            <label className="block mb-1">Password</label>
            <input className="border rounded w-full p-2" value={password} onChange={e => setPassword(e.target.value)} type="password" required />
          </div>
          <button className="bg-blue-600 text-white px-4 py-2 rounded" type="submit">Register</button>
        </form>
      </main>
    </>
  )
}
