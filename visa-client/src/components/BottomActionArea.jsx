export default function BottomActionArea({ children }) {
  return (
    <div style={{
      position: 'fixed',
      bottom: 0,
      left: '50%',
      transform: 'translateX(-50%)',
      width: '100%',
      maxWidth: 430,
      background: 'var(--color-surface)',
      borderTop: '1px solid var(--color-border)',
      padding: `16px 20px calc(16px + env(safe-area-inset-bottom))`,
      zIndex: 20,
      display: 'flex',
      flexDirection: 'column',
      gap: 8,
    }}>
      {children}
    </div>
  )
}
