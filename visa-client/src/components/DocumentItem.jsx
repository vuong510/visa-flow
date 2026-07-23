import StatusChip from './StatusChip'

export default function DocumentItem({ item, docState, onUpload, onDetail }) {
  const status = docState?.uploading
    ? 'uploading'
    : docState?.reviewing
    ? 'reviewing'
    : docState?.status || 'pending'

  const isFail = status === 'fail'
  const isClarify = status === 'needs_clarification'
  const hasFail = isFail || isClarify
  const actionLabel = status === 'pending' ? 'Tải lên' : hasFail ? 'Tải lại' : null
  const actionColor = hasFail ? 'var(--color-error)' : 'var(--color-cta)'
  // needs_clarification không chặn gửi hồ sơ (đội tư vấn sẽ xem trực tiếp) — không nên nhìn
  // báo động y hệt fail thật; màu/nhãn khớp đúng bảng màu StatusChip cho từng state.
  const notesStyle = isFail
    ? { background: '#fef2f2', border: '1px solid #fecaca', color: '#991b1b' }
    : { background: '#fef3c7', border: '1px solid #fbbf24', color: '#92400e' }
  const notesLabel = isFail ? '⚠️ Lý do: ' : 'Cần làm rõ: '

  return (
    <div style={{ borderBottom: '1px solid var(--color-border)' }}>
      <div
        style={{ padding: '14px 0', cursor: 'pointer' }}
        onClick={() => onDetail(item)}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <p style={{ fontSize: 14, fontWeight: 600, marginBottom: 2 }}>{item.name}</p>
            <p style={{ fontSize: 12, color: 'var(--color-text-muted)', lineHeight: 1.4, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {item.description}
            </p>
          </div>
          <StatusChip status={status} />
          {status === 'pass' && (
            <span style={{ fontSize: 18, flexShrink: 0 }}>✓</span>
          )}
        </div>
        {actionLabel && (
          <button
            type="button"
            onClick={(e) => { e.stopPropagation(); onUpload(item.id) }}
            style={{
              display: 'inline-block',
              marginTop: 2,
              marginLeft: -6,
              padding: '8px 6px',
              background: 'none',
              border: 'none',
              fontSize: 13,
              fontWeight: 600,
              color: actionColor,
              textDecoration: 'underline',
              cursor: 'pointer',
            }}
          >
            {actionLabel}
          </button>
        )}
      </div>
      {hasFail && docState?.notes && (
        <div style={{
          margin: '0 0 12px',
          padding: '10px 12px',
          borderRadius: 8,
          fontSize: 13,
          lineHeight: 1.5,
          ...notesStyle,
        }}>
          <strong>{notesLabel}</strong>{docState.notes}
        </div>
      )}
    </div>
  )
}
