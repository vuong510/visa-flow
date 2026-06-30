import { useState, useRef, useEffect } from 'react'
import { useApp } from '../context/AppContext'

export default function ChatWidget() {
  const { destination, screen, profile, applicationId, API_BASE } = useApp()
  const [open, setOpen] = useState(false)
  const [input, setInput] = useState('')
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    if (open && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [history, open])

  async function send() {
    const text = input.trim()
    if (!text || loading) return

    const userMsg = { role: 'user', content: text }
    const nextHistory = [...history, userMsg]
    setHistory(nextHistory)
    setInput('')
    setLoading(true)

    try {
      const res = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          history,
          context: { destination, screen, profile, applicationId },
        }),
      })
      const data = await res.json()
      setHistory([...nextHistory, { role: 'assistant', content: data.reply }])
    } catch {
      setHistory([...nextHistory, { role: 'assistant', content: 'Có lỗi xảy ra, thử lại nhé.' }])
    } finally {
      setLoading(false)
    }
  }

  function handleKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  return (
    <>
      {open && (
        <div style={{
          position: 'fixed',
          bottom: '88px',
          right: '20px',
          width: '320px',
          maxHeight: '480px',
          background: 'var(--color-surface, #fff)',
          borderRadius: 'var(--radius-card, 16px)',
          boxShadow: 'var(--shadow-modal, 0 8px 32px rgba(0,0,0,0.18))',
          display: 'flex',
          flexDirection: 'column',
          zIndex: 20,
          overflow: 'hidden',
          border: '1px solid rgba(0,0,0,0.08)',
        }}>
          <div style={{
            padding: '14px 16px',
            borderBottom: '1px solid rgba(0,0,0,0.08)',
            fontWeight: 600,
            fontSize: '15px',
          }}>
            Hỏi về visa
          </div>

          <div style={{
            flex: 1,
            overflowY: 'auto',
            padding: '12px',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
            minHeight: 0,
          }}>
            {history.length === 0 && (
              <div style={{ color: '#888', fontSize: '13px', textAlign: 'center', marginTop: '24px' }}>
                Hỏi tôi bất cứ điều gì về visa nhé!
              </div>
            )}
            {history.map((msg, i) => (
              <div key={i} style={{
                display: 'flex',
                justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
              }}>
                <div style={{
                  maxWidth: '80%',
                  padding: '8px 12px',
                  borderRadius: '12px',
                  fontSize: '14px',
                  lineHeight: '1.5',
                  background: msg.role === 'user'
                    ? 'var(--color-cta, #2563eb)'
                    : 'var(--color-surface-alt, #f3f4f6)',
                  color: msg.role === 'user' ? '#fff' : 'inherit',
                  border: msg.role === 'assistant' ? '1px solid rgba(0,0,0,0.08)' : 'none',
                }}>
                  {msg.content}
                </div>
              </div>
            ))}
            {loading && (
              <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                <div style={{
                  padding: '8px 12px',
                  borderRadius: '12px',
                  fontSize: '14px',
                  background: 'var(--color-surface-alt, #f3f4f6)',
                  border: '1px solid rgba(0,0,0,0.08)',
                  color: '#888',
                }}>
                  Đang trả lời...
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          <div style={{
            padding: '10px 12px',
            borderTop: '1px solid rgba(0,0,0,0.08)',
            display: 'flex',
            gap: '8px',
          }}>
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKey}
              placeholder="Nhập câu hỏi..."
              disabled={loading}
              style={{
                flex: 1,
                border: '1px solid rgba(0,0,0,0.15)',
                borderRadius: '8px',
                padding: '8px 10px',
                fontSize: '14px',
                outline: 'none',
                background: 'transparent',
              }}
            />
            <button
              onClick={send}
              disabled={loading || !input.trim()}
              style={{
                background: 'var(--color-cta, #2563eb)',
                color: '#fff',
                border: 'none',
                borderRadius: '8px',
                padding: '8px 14px',
                fontSize: '14px',
                cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
                opacity: loading || !input.trim() ? 0.5 : 1,
              }}
            >
              Gửi
            </button>
          </div>
        </div>
      )}

      <button
        onClick={() => setOpen(o => !o)}
        aria-label={open ? 'Đóng chat' : 'Mở chat'}
        style={{
          position: 'fixed',
          bottom: '90px',
          right: '20px',
          width: '56px',
          height: '56px',
          borderRadius: '50%',
          background: 'var(--color-cta, #2563eb)',
          color: '#fff',
          border: 'none',
          cursor: 'pointer',
          fontSize: '24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 4px 16px rgba(0,0,0,0.2)',
          zIndex: 20,
          transition: 'transform 0.15s',
        }}
      >
        {open ? '✕' : '💬'}
      </button>
    </>
  )
}
