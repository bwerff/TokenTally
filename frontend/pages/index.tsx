import Link from 'next/link'
import Navbar from '../components/Navbar'

export default function Home() {
  return (
    <>
      <Navbar />
      <main className="container mx-auto px-4 py-8">
        <h2 className="text-2xl font-bold mb-4">Welcome to TokenTally</h2>
        <p className="mb-6">Please <Link className="text-blue-600" href="/login">login</Link> or <Link className="text-blue-600" href="/register">register</Link> to continue.</p>
      </main>
    </>
  )
}
