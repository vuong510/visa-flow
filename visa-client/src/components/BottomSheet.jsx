import { useEffect } from 'react'

export default function BottomSheet({ open, onClose, title, children }) {
  useEffect(() => {
    if (open) document.body.style.overflow = 'hidden'
    else document.body.style.overflow = ''
    return () => { document.body.style.overflow = '' }
  }, [open])

  if (!open) return null

  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0, zIndex: 100,
        background: 'rgba(0,0,0,0.4)',
        display: 'flex', alignItems: 'flex-end',
        animation: `fadeIn var(--duration-base) var(--ease-default)`,
      }}
    >
      <div
        onClick={e => e.stopPropagation()}
        style={{
          width: '100%', maxWidth: 430, margin: '0 auto',
          background: 'var(--color-surface)',
          borderRadius: '20px 20px 0 0',
          padding: '20px 20px calc(20px + env(safe-area-inset-bottom))',
          animation: `slideUp var(--duration-slow) var(--ease-spring)`,
        }}
      >
        <div style={{
          width: 36, height: 4, background: 'var(--color-border)',
          borderRadius: 2, margin: '0 auto 16px',
        }} />
        {title && (
          <h3 style={{ fontSize: 17, fontWeight: 600, marginBottom: 12, color: 'var(--color-text-primary)' }}>
            {title}
          </h3>
        )}
        {children}
        <button
          onClick={onClose}
          style={{
            marginTop: 20, width: '100%', height: 52,
            background: 'var(--color-cta)', color: '#fff',
            border: 'none', borderRadius: 'var(--radius-button)',
            fontSize: 16, fontWeight: 600, cursor: 'pointer',
          }}
        >
          Đóng
        </button>
      </div>
    </div>
  )
}
