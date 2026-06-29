import StatusChip from './StatusChip'

export default function DocumentItem({ item, docState, onUpload, onDetail }) {
  const status = docState?.uploading
    ? 'uploading'
    : docState?.reviewing
    ? 'reviewing'
    : docState?.status || 'pending'

  const hasFail = status === 'fail' || status === 'needs_clarification'

  return (
    <div style={{ borderBottom: '1px solid var(--color-border)' }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          padding: '14px 0',
          cursor: 'pointer',
        }}
        onClick={() => onDetail(item)}
      >
        <div style={{ flex: 1, minWidth: 0 }}>
          <p style={{ fontSize: 14, fontWeight: 600, marginBottom: 2 }}>{item.name}</p>
          <p style={{ fontSize: 12, color: 'var(--color-text-muted)', lineHeight: 1.4, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {item.description}
          </p>
        </div>
        <StatusChip status={status} />
        {status === 'pending' && (
          <button
            onClick={(e) => { e.stopPropagation(); onUpload(item.id) }}
            style={{
              flexShrink: 0,
              padding: '6px 14px',
              borderRadius: 8,
              border: '1.5px solid var(--color-cta)',
              background: 'transparent',
              color: 'var(--color-cta)',
              fontSize: 13,
              fontWeight: 600,
              cursor: 'pointer',
              whiteSpace: 'nowrap',
            }}
          >
            Tải lên
          </button>
        )}
        {(status === 'fail' || status === 'needs_clarification') && (
          <button
            onClick={(e) => { e.stopPropagation(); onUpload(item.id) }}
            style={{
              flexShrink: 0,
              padding: '6px 12px',
              borderRadius: 8,
              border: '1.5px solid #dc2626',
              background: 'transparent',
              color: '#dc2626',
              fontSize: 13,
              fontWeight: 600,
              cursor: 'pointer',
              whiteSpace: 'nowrap',
            }}
          >
            Tải lại
          </button>
        )}
        {(status === 'pass') && (
          <span style={{ fontSize: 18, flexShrink: 0 }}>✓</span>
        )}
      </div>
      {hasFail && docState?.notes && (
        <div style={{
          margin: '0 0 12px',
          padding: '10px 12px',
          background: '#fef2f2',
          borderRadius: 8,
          fontSize: 13,
          color: '#991b1b',
          lineHeight: 1.5,
        }}>
          {docState.notes}
        </div>
      )}
    </div>
  )
}
