import { useState } from 'react'
import Navbar from '../components/Navbar'

export default function UploadReceipt() {
  const [file, setFile] = useState<File | null>(null)
  const [message, setMessage] = useState('')

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!file) return
    const formData = new FormData()
    formData.append('file', file)
    const res = await fetch('/api/upload', {
      method: 'POST',
      body: formData,
    })
    if (res.ok) setMessage('Uploaded!')
    else setMessage('Upload failed')
  }

  return (
    <>
      <Navbar />
      <main className="container mx-auto px-4 py-8">
        <h2 className="text-2xl font-bold mb-4">Upload Receipt</h2>
        <form onSubmit={handleSubmit} className="space-y-4 max-w-sm">
          <input type="file" onChange={e => setFile(e.target.files?.[0] || null)} />
          <button className="bg-blue-600 text-white px-4 py-2 rounded" type="submit">Upload</button>
        </form>
        {message && <p className="mt-4">{message}</p>}
      </main>
    </>
  )
}
