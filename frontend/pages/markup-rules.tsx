import { useEffect, useState } from 'react'
import Navbar from '../components/Navbar'
import { useTranslations } from 'next-intl'

interface Rule {
  id: string
  provider: string
  model: string
  markup: number
  effective_date: string
}

export default function MarkupRules() {
  const [rules, setRules] = useState<Rule[]>([])
  const [form, setForm] = useState({ provider: '', model: '', markup: '', effective_date: '' })
  const t = useTranslations()

  async function load() {
    const res = await fetch('/markup-rules')
    if (res.ok) setRules(await res.json())
  }

  useEffect(() => { load() }, [])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    await fetch('/markup-rules', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        provider: form.provider,
        model: form.model,
        markup: parseFloat(form.markup),
        effective_date: form.effective_date,
      }),
    })
    setForm({ provider: '', model: '', markup: '', effective_date: '' })
    load()
  }

  async function remove(id: string) {
    await fetch(`/markup-rules/${id}`, { method: 'DELETE' })
    load()
  }

  return (
    <>
      <Navbar />
      <main className="container mx-auto px-4 py-8">
        <h2 className="text-2xl font-bold mb-4">{t('markup.title')}</h2>
        <form onSubmit={handleSubmit} className="space-x-2 mb-4">
          <input className="border p-1" placeholder={t('markup.provider')} value={form.provider} onChange={e => setForm({ ...form, provider: e.target.value })} />
          <input className="border p-1" placeholder={t('markup.model')} value={form.model} onChange={e => setForm({ ...form, model: e.target.value })} />
          <input className="border p-1" placeholder={t('markup.markup')} value={form.markup} onChange={e => setForm({ ...form, markup: e.target.value })} />
          <input className="border p-1" placeholder={t('markup.effective')} value={form.effective_date} onChange={e => setForm({ ...form, effective_date: e.target.value })} />
          <button className="bg-blue-600 text-white px-2 py-1 rounded" type="submit">{t('markup.add')}</button>
        </form>
        <ul className="space-y-2">
          {rules.map(r => (
            <li key={r.id} className="p-2 bg-white rounded shadow flex justify-between">
              <span>{r.provider} {r.model} {r.markup}</span>
              <button className="text-red-600" onClick={() => remove(r.id)}>{t('markup.delete')}</button>
            </li>
          ))}
        </ul>
      </main>
    </>
  )
}
