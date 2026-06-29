export default function ProgressBar({ current, total = 10 }) {
  const pct = (current / total) * 100

  return (
    <div>
      <div style={{
        display: 'flex',
        justifyContent: 'flex-end',
        padding: '5px 20px',
        background: 'var(--color-surface)',
        borderBottom: 'none',
      }}>
        <span style={{
          fontSize: 12,
          fontWeight: 500,
          color: 'var(--color-text-muted)',
          lineHeight: 1.45,
        }}>
          Bước {current}/{total}
        </span>
      </div>
      <div style={{ height: 4, background: 'var(--color-border)' }}>
        <div style={{
          height: '100%',
          width: `${pct}%`,
          background: 'var(--color-cta)',
          transition: `width var(--duration-base) var(--ease-default)`,
        }} />
      </div>
    </div>
  )
}
