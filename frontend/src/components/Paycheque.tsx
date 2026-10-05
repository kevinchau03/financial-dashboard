import AppForm from './AppForm'
import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { amount, saveRecord } from '../api'
import Notice from './Notice'
import useNotice from '../hooks/useNotice'

type SavedPaycheque = { id: number; amount: string }

export default function Paycheque() {
  const [saved, setSaved] = useState<SavedPaycheque | null>(null)
  const [value, setValue] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useNotice()
  const pending = useRef(false)
  useEffect(() => {
    const controller = new AbortController()
    async function load() {
      try {
        const response = await fetch('/api/paycheques/latest', { signal: controller.signal })
        if (!response.ok) throw new Error('Unable to load your latest paycheque.')
        const data: SavedPaycheque | null = await response.json()
        if (!controller.signal.aborted) setSaved(data)
      } catch (error) {
        if (!controller.signal.aborted) setError(error instanceof Error ? error.message : 'Unable to load paycheque.')
      } finally { if (!controller.signal.aborted) setLoading(false) }
    }
    void load()
    return () => controller.abort()
  }, [])

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (pending.current) return
    pending.current = true
    setSaving(true)
    setError('')
    try {
      setSaved(await saveRecord<SavedPaycheque>('/api/paycheques', 'POST', { amount: value }))
      setValue('')
      setNotice('Paycheque saved.')
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Unable to save paycheque.')
    } finally { pending.current = false; setSaving(false) }
  }

  return <section className="paycheque-card" aria-label="Paycheque">
    <AppForm onSubmit={submit}>
      <fieldset disabled={loading || saving}>
        <label htmlFor="paycheque-amount">Just got your paycheque?</label>
        <div className="contribution-controls">
          <input id="paycheque-amount" type="number" min="0.01" max="999999999999.99" step="0.01" required value={value} onChange={event => setValue(event.target.value)} placeholder="0.00" />
          <button type="submit">{saving ? 'Saving…' : 'Save paycheque'}</button>
        </div>
      </fieldset>
    </AppForm>
    <p aria-live="polite">{loading ? 'Loading…' : saved ? `Ready to assign: ${amount(saved.amount)}` : 'No paycheque saved yet.'}</p>
    {error && <p role="alert">{error}</p>}
    <Notice message={notice} />
  </section>
}


