import { useState, useEffect } from 'react'
import { useApp } from '../context/AppContext'

const QUEUE_KEY = 'visa_feedback_queue'
const MAX_QUEUE_SIZE = 50

function readQueue() {
  try {
    const raw = localStorage.getItem(QUEUE_KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

// Returns true if the write actually succeeded, so callers can decide whether
// it's safe to tell the user their feedback was saved.
function writeQueue(queue) {
  try {
    // Cap the queue so an offline user submitting repeatedly can't grow it
    // without bound — drop the oldest entries first.
    const capped = queue.length > MAX_QUEUE_SIZE
      ? queue.slice(queue.length - MAX_QUEUE_SIZE)
      : queue
    localStorage.setItem(QUEUE_KEY, JSON.stringify(capped))
    return true
  } catch {
    // Quota exceeded / Safari ITP / serialization error — surface to caller.
    return false
  }
}

// crypto.randomUUID() throws synchronously in non-secure contexts / older
// browsers. Fall back to a timestamp+random id so a submission never
// silently vanishes just because id generation blew up.
function makeClientId() {
  try {
    if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
      return crypto.randomUUID()
    }
  } catch {
    // fall through to fallback id below
  }
  return `fid-${Date.now()}-${Math.random().toString(36).slice(2)}`
}

// Throws on failure. Network errors (no `status`) and 5xx are transient and
// safe to retry; 4xx is a permanent rejection (`isClientError`), so callers
// must not requeue it forever.
async function sendEntry(entry, API_BASE) {
  const res = await fetch(`${API_BASE}/api/feedback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(entry),
  })
  if (!res.ok) {
    const err = new Error(`HTTP ${res.status}`)
    err.status = res.status
    err.isClientError = res.status >= 400 && res.status < 500
    throw err
  }
}

// Only one flush may actively read/write the queue at a time — otherwise the
// mount-time flush and the post-submit flush (or React StrictMode's double
// mount effect) can race on the non-atomic localStorage read-modify-write and
// either resurrect an already-sent entry or silently drop one.
let flushPromise = null

function flushQueue(API_BASE) {
  if (flushPromise) return flushPromise
  flushPromise = (async () => {
    try {
      const queue = readQueue()
      if (queue.length === 0) return
      const remaining = []
      for (const entry of queue) {
        try {
          await sendEntry(entry, API_BASE)
        } catch (err) {
          if (err && err.isClientError) {
            // Permanent rejection (e.g. failed validation) — drop it instead
            // of retrying forever.
            console.warn('Feedback entry rejected by server, dropping:', err)
          } else {
            remaining.push(entry)
          }
        }
      }
      writeQueue(remaining)
    } finally {
      flushPromise = null
    }
  })()
  return flushPromise
}

// FeedbackWidget: kênh feedback riêng biệt (không tái dùng ChatWidget/`/chat`) —
// luôn render trên mọi màn hình, không có logic ẩn theo `screen`.
export default function FeedbackWidget() {
  const { screen, applicationId, sessionId, API_BASE } = useApp()
  const [open, setOpen] = useState(false)
  const [message, setMessage] = useState('')
  const [ack, setAck] = useState(false)
  const [error, setError] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Flush backlog cục bộ (nếu có) ngay khi widget mount
  useEffect(() => {
    flushQueue(API_BASE)
  }, [API_BASE])

  async function submit() {
    const text = message.trim()
    if (!text || isSubmitting) return

    setIsSubmitting(true)
    setError(false)

    const entry = {
      client_id: makeClientId(),
      application_id: applicationId ?? null,
      session_id: sessionId ?? null,
      screen: screen ?? null,
      message: text,
      created_at: new Date().toISOString(),
    }

    let acked = false
    try {
      // Try sending immediately; only a genuine send counts as success here.
      await sendEntry(entry, API_BASE)
      acked = true
    } catch (err) {
      if (err && err.isClientError) {
        // Permanent rejection — don't queue it, don't show a false ack.
        console.warn('Feedback rejected by server (4xx), not retrying:', err)
      } else {
        // Network failure or 5xx — queue for retry. localStorage.setItem is
        // synchronous, so this doesn't add any perceptible delay.
        const queue = readQueue()
        queue.push(entry)
        acked = writeQueue(queue)
      }
    }

    if (acked) {
      setMessage('')
      setAck(true)
      setTimeout(() => setAck(false), 3000)
    } else {
      setError(true)
      setTimeout(() => setError(false), 3000)
    }

    setIsSubmitting(false)
    // Flush lại toàn bộ backlog cũ (không chờ kết quả)
    flushQueue(API_BASE)
  }

  return (
    <>
      {open && (
        <div style={{
          position: 'fixed',
          bottom: '88px',
          left: '20px',
          width: '300px',
          background: 'var(--color-surface, #fff)',
          borderRadius: 'var(--radius-card, 16px)',
          boxShadow: 'var(--shadow-modal, 0 8px 32px rgba(0,0,0,0.18))',
          zIndex: 30,
          overflow: 'hidden',
          border: '1px solid rgba(0,0,0,0.08)',
        }}>
          <div style={{
            padding: '14px 16px',
            borderBottom: '1px solid rgba(0,0,0,0.08)',
            fontWeight: 600,
            fontSize: '15px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}>
            Góp ý / báo lỗi
            <button
              onClick={() => setOpen(false)}
              aria-label="Đóng góp ý"
              style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 18, color: '#6b7280', lineHeight: 1, padding: '0 0 0 8px' }}
            >
              ✕
            </button>
          </div>

          <div style={{ padding: '12px' }}>
            {ack ? (
              <div style={{ background: '#d1fae5', border: '1px solid #6ee7b7', borderRadius: 10, padding: '10px 12px', fontSize: 13, color: '#065f46', fontWeight: 600, textAlign: 'center' }}>
                Đã gửi, cảm ơn bạn!
              </div>
            ) : (
              <>
                {error && (
                  <div style={{ background: '#fee2e2', border: '1px solid #fca5a5', borderRadius: 10, padding: '8px 12px', fontSize: 13, color: '#991b1b', fontWeight: 600, textAlign: 'center', marginBottom: '8px' }}>
                    Gửi không thành công, vui lòng thử lại.
                  </div>
                )}
                <textarea
                  value={message}
                  onChange={e => setMessage(e.target.value)}
                  placeholder="Bạn đang gặp vấn đề gì? Mô tả giúp mình nhé..."
                  rows={4}
                  style={{
                    width: '100%',
                    border: '1px solid rgba(0,0,0,0.15)',
                    borderRadius: '8px',
                    padding: '8px 10px',
                    fontSize: '14px',
                    outline: 'none',
                    background: 'transparent',
                    resize: 'vertical',
                    boxSizing: 'border-box',
                  }}
                />
                <button
                  onClick={submit}
                  disabled={!message.trim() || isSubmitting}
                  style={{
                    marginTop: '8px',
                    width: '100%',
                    background: 'var(--color-cta, #2563eb)',
                    color: '#fff',
                    border: 'none',
                    borderRadius: '8px',
                    padding: '8px 14px',
                    fontSize: '14px',
                    cursor: (!message.trim() || isSubmitting) ? 'not-allowed' : 'pointer',
                    opacity: (!message.trim() || isSubmitting) ? 0.5 : 1,
                  }}
                >
                  {isSubmitting ? 'Đang gửi...' : 'Gửi'}
                </button>
              </>
            )}
          </div>
        </div>
      )}

      <button
        onClick={() => setOpen(o => !o)}
        onKeyDown={e => e.key === 'Enter' && e.preventDefault()}
        aria-label={open ? 'Đóng góp ý' : 'Gửi góp ý'}
        style={{
          position: 'fixed',
          bottom: '20px',
          left: '20px',
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
          zIndex: 30,
          transition: 'transform 0.15s',
        }}
      >
        {open ? '✕' : '🚩'}
      </button>
    </>
  )
}
