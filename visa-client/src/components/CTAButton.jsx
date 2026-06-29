export default function CTAButton({ label, onClick, disabled, loading, secondary }) {
  if (secondary) {
    return (
      <button
        onClick={disabled || loading ? undefined : onClick}
        disabled={disabled}
        style={{
          background: 'none', border: 'none', cursor: disabled ? 'not-allowed' : 'pointer',
          color: 'var(--color-cta)', fontSize: 16, fontWeight: 500,
          padding: '8px 0', width: '100%', fontFamily: 'inherit',
        }}
      >
        {label}
      </button>
    )
  }

  return (
    <button
      onClick={disabled || loading ? undefined : onClick}
      disabled={disabled || loading}
      aria-busy={loading}
      style={{
        width: '100%', height: 52,
        background: disabled ? 'var(--color-border)' : 'var(--color-cta)',
        color: disabled ? 'var(--color-text-muted)' : '#fff',
        border: 'none', borderRadius: 'var(--radius-button)',
        fontSize: 16, fontWeight: 600, cursor: disabled ? 'not-allowed' : 'pointer',
        fontFamily: 'inherit',
        transition: `background var(--duration-fast) var(--ease-default)`,
        display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
      }}
      onMouseDown={e => { if (!disabled && !loading) e.currentTarget.style.background = 'var(--color-cta-pressed)' }}
      onMouseUp={e => { if (!disabled && !loading) e.currentTarget.style.background = 'var(--color-cta)' }}
      onMouseLeave={e => { if (!disabled && !loading) e.currentTarget.style.background = 'var(--color-cta)' }}
    >
      {loading ? (
        <span style={{
          width: 20, height: 20, border: '2px solid rgba(255,255,255,0.4)',
          borderTopColor: '#fff', borderRadius: '50%',
          animation: 'spin 0.7s linear infinite',
          display: 'inline-block',
        }} />
      ) : label}
    </button>
  )
}
