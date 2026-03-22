import { useState, type FormEvent } from 'react'

type Status = 'idle' | 'loading' | 'success' | 'error'

export function Contact() {
  const [status, setStatus] = useState<Status>('idle')
  const [errorMsg, setErrorMsg] = useState('')

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setStatus('loading')
    setErrorMsg('')
    const f = e.currentTarget
    const body = {
      fullname: (f.elements.namedItem('fullname') as HTMLInputElement).value,
      email: (f.elements.namedItem('email') as HTMLInputElement).value,
      subject: (f.elements.namedItem('subject') as HTMLInputElement).value,
      message: (f.elements.namedItem('message') as HTMLTextAreaElement).value,
    }
    try {
      const res = await fetch('/api/contact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (res.ok) {
        setStatus('success')
        f.reset()
      } else {
        const json = await res.json().catch(() => ({}))
        setErrorMsg(json.detail ?? 'Something went wrong.')
        setStatus('error')
      }
    } catch {
      setErrorMsg('Network error. Please try again.')
      setStatus('error')
    }
  }

  return (
    <section id="contact" style={{ borderTop: '1px solid rgba(255,255,255,0.05)', background: 'rgba(255,255,255,0.015)' }}>
      <div className="section" style={{ maxWidth: 600 }}>
        <div data-reveal className="section-label">Contact</div>
        <h2 data-reveal data-delay="1" className="section-heading">Let's work together</h2>
        <p data-reveal data-delay="2" style={{ color: '#71717a', fontSize: 15, lineHeight: 1.7, marginBottom: 40, marginTop: -24 }}>
          Have a project in mind or just want to say hello? Send me a message and I'll get back to you.
        </p>

        {status === 'success' ? (
          <div
            data-reveal
            style={{
              padding: '32px',
              borderRadius: 16,
              background: 'rgba(99,102,241,0.07)',
              border: '1px solid rgba(99,102,241,0.2)',
              textAlign: 'center',
            }}
          >
            <div style={{ fontSize: 32, marginBottom: 12 }}>✓</div>
            <h3 style={{ fontSize: 18, fontWeight: 700, color: '#f4f4f5', marginBottom: 8 }}>Message sent!</h3>
            <p style={{ color: '#71717a', fontSize: 14, marginBottom: 20 }}>
              Thanks for reaching out — I'll reply as soon as I can.
            </p>
            <button
              onClick={() => setStatus('idle')}
              className="btn btn-ghost"
              style={{ margin: '0 auto' }}
            >
              Send another message
            </button>
          </div>
        ) : (
          <form data-reveal data-delay="3" onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }} className="contact-row">
              <div>
                <label style={{ display: 'block', fontSize: 11, fontWeight: 700, letterSpacing: '1px', textTransform: 'uppercase', color: '#52525b', marginBottom: 8 }}>
                  Name
                </label>
                <input type="text" name="fullname" required placeholder="Thomas Bonnici" className="input" />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: 11, fontWeight: 700, letterSpacing: '1px', textTransform: 'uppercase', color: '#52525b', marginBottom: 8 }}>
                  Email
                </label>
                <input type="email" name="email" required placeholder="hello@example.com" className="input" />
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: 11, fontWeight: 700, letterSpacing: '1px', textTransform: 'uppercase', color: '#52525b', marginBottom: 8 }}>
                Subject
              </label>
              <input type="text" name="subject" required placeholder="Project enquiry" className="input" />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: 11, fontWeight: 700, letterSpacing: '1px', textTransform: 'uppercase', color: '#52525b', marginBottom: 8 }}>
                Message
              </label>
              <textarea
                name="message"
                required
                rows={5}
                placeholder="Tell me about your project…"
                className="input"
                style={{ resize: 'vertical', minHeight: 120, lineHeight: 1.6 }}
              />
            </div>

            {errorMsg && (
              <div style={{ padding: '10px 14px', borderRadius: 8, background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)', color: '#fca5a5', fontSize: 13 }}>
                {errorMsg}
              </div>
            )}

            <button
              type="submit"
              disabled={status === 'loading'}
              className="btn btn-primary"
              style={{ width: '100%', justifyContent: 'center', padding: '13px', fontSize: 14, opacity: status === 'loading' ? 0.6 : 1 }}
            >
              {status === 'loading' ? 'Sending…' : 'Send message'}
            </button>
          </form>
        )}
      </div>

      <style>{`
        @media (max-width: 480px) {
          .contact-row { grid-template-columns: 1fr !important; }
        }
      `}</style>
    </section>
  )
}
