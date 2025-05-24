import Link from 'next/link'

export default function Navbar() {
  return (
    <nav className="bg-white shadow mb-6">
      <div className="container mx-auto px-4 py-4 flex justify-between items-center">
        <h1 className="text-xl font-semibold">TokenTally</h1>
        <div className="space-x-4">
          <Link className="text-blue-600" href="/offers">Offers</Link>
          <Link className="text-blue-600" href="/upload-receipt">Upload Receipt</Link>
        </div>
      </div>
    </nav>
  )
}
