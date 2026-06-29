export default function OptionButton({ label, selected, onClick, disabled }) {
  return (
    <button
      onClick={disabled ? undefined : onClick}
      aria-pressed={selected}
      disabled={disabled}
      style={{
        width: '100%', minHeight: 56, textAlign: 'left',
        padding: '0 16px', display: 'flex', alignItems: 'center',
        justifyContent: 'space-between',
        background: disabled
          ? 'var(--color-background)'
          : selected ? 'rgba(37,99,235,0.06)' : 'var(--color-surface)',
        border: selected ? '2px solid var(--color-cta)' : '1px solid var(--color-border)',
        borderRadius: 'var(--radius-button)',
        color: disabled
          ? 'var(--color-text-muted)'
          : selected ? 'var(--color-cta)' : 'var(--color-text-primary)',
        fontSize: 16, fontWeight: 400, cursor: disabled ? 'not-allowed' : 'pointer',
        boxShadow: selected ? 'var(--shadow-card-raised)' : 'none',
        transition: `all var(--duration-fast) var(--ease-default)`,
        fontFamily: 'inherit',
      }}
      onMouseDown={e => { if (!disabled) e.currentTarget.style.transform = 'scale(0.98)' }}
      onMouseUp={e => { e.currentTarget.style.transform = 'scale(1)' }}
      onMouseLeave={e => { e.currentTarget.style.transform = 'scale(1)' }}
    >
      <span>{label}</span>
      {selected && <span aria-hidden="true" style={{ color: 'var(--color-cta)', fontSize: 18 }}>✓</span>}
    </button>
  )
}
