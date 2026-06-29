const VARIANTS = {
  pass:              { label: 'Đạt',              bg: '#d1fae5', color: '#065f46' },
  fail:              { label: 'Không đạt',        bg: '#fee2e2', color: '#991b1b' },
  needs_clarification: { label: 'Cần làm rõ',    bg: '#fef3c7', color: '#92400e' },
  pending:           { label: 'Chờ tải lên',      bg: '#f3f4f6', color: '#6b7280' },
  processing:        { label: 'Đang xử lý...',    bg: '#eff6ff', color: '#1d4ed8' },
  uploading:         { label: 'Đang tải...',      bg: '#eff6ff', color: '#1d4ed8' },
  reviewing:         { label: 'Đang kiểm tra...', bg: '#eff6ff', color: '#1d4ed8' },
}

export default function StatusChip({ status }) {
  const v = VARIANTS[status] || VARIANTS.pending
  return (
    <span style={{
      display: 'inline-flex',
      alignItems: 'center',
      padding: '2px 10px',
      borderRadius: 99,
      fontSize: 12,
      fontWeight: 600,
      background: v.bg,
      color: v.color,
      whiteSpace: 'nowrap',
    }}>
      {v.label}
    </span>
  )
}
