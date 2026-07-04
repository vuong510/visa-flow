import { useEffect, useState, useRef } from 'react'
import NavHeader from '../components/NavHeader'
import { useApp } from '../context/AppContext'

const POLL_INTERVAL = 5 * 60 * 1000 // 5 minutes

function TimelineNode({ node, isLast }) {
  const isActive = node.state === 'active'
  const isCompleted = node.state === 'completed'

  const dotColor = isCompleted ? '#10b981' : isActive ? '#3b82f6' : '#d1d5db'
  const lineColor = isCompleted ? '#10b981' : '#e5e7eb'

  return (
    <div style={{ display: 'flex', gap: 16 }}>
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 24, flexShrink: 0 }}>
        <div style={{
          width: 24,
          height: 24,
          borderRadius: '50%',
          background: dotColor,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
          animation: isActive ? 'pulse-ring 2s ease-out infinite' : 'none',
          position: 'relative',
          zIndex: 1,
        }}>
          {isCompleted && <span style={{ color: '#fff', fontSize: 12, lineHeight: 1 }}>✓</span>}
          {isActive && <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#fff' }} />}
          {!isActive && !isCompleted && <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#9ca3af' }} />}
        </div>
        {!isLast && (
          <div style={{ width: 2, flex: 1, minHeight: 32, background: lineColor, margin: '4px 0' }} />
        )}
      </div>
      <div style={{ paddingBottom: isLast ? 0 : 28, paddingTop: 2 }}>
        <p style={{
          fontSize: 15,
          fontWeight: isActive ? 700 : 500,
          color: isActive ? 'var(--color-text-primary)' : isCompleted ? 'var(--color-text-primary)' : 'var(--color-text-muted)',
          marginBottom: 2,
        }}>
          {node.label}
        </p>
        <p style={{ fontSize: 12, color: 'var(--color-text-muted)', lineHeight: 1.4 }}>
          {node.sub}
        </p>
      </div>
    </div>
  )
}

export default function StatusTimelineScreen() {
  const { applicationId, API_BASE, navigate, setResultStatus } = useApp()
  const [statusData, setStatusData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [lastRefresh, setLastRefresh] = useState(null)
  const pollRef = useRef(null)

  useEffect(() => {
    fetchStatus()
    pollRef.current = setInterval(fetchStatus, POLL_INTERVAL)
    return () => clearInterval(pollRef.current)
  }, [])

  async function fetchStatus() {
    try {
      const res = await fetch(`${API_BASE}/api/application/${applicationId}/status`)
      if (!res.ok) return
      const data = await res.json()
      setStatusData(data)
      setLastRefresh(new Date())
      if (data.is_terminal) {
        clearInterval(pollRef.current)
        setResultStatus(data.submission_status)
        navigate('result')
      }
    } catch (_) {}
    finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ minHeight: '100dvh', display: 'flex', flexDirection: 'column', background: 'var(--color-background)' }}>
      <NavHeader
        title="Tiến trình hồ sơ"
        showBack={false}
        rightAction={
          <button
            onClick={fetchStatus}
            style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 18, padding: '0 4px', color: 'var(--color-text-muted)' }}
            title="Làm mới"
          >
            ↻
          </button>
        }
      />

      <div style={{ flex: 1, padding: '24px 20px' }}>
        {loading && (
          <div style={{ padding: '0 20px' }}>
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} style={{ display: 'flex', gap: 16, marginBottom: 28 }}>
                <div className="skeleton" style={{ width: 24, height: 24, borderRadius: '50%', flexShrink: 0 }} />
                <div style={{ flex: 1 }}>
                  <div className="skeleton" style={{ width: '50%', height: 14, marginBottom: 6 }} />
                  <div className="skeleton" style={{ width: '75%', height: 12 }} />
                </div>
              </div>
            ))}
          </div>
        )}

        {statusData && (
          <div style={{ background: 'var(--color-surface)', borderRadius: 'var(--radius-card)', padding: 24, boxShadow: 'var(--shadow-card)' }}>
            <h2 style={{ fontSize: 17, fontWeight: 700, marginBottom: 24 }}>Tiến trình hồ sơ</h2>
            {statusData.nodes.map((node, i) => (
              <TimelineNode
                key={node.id}
                node={node}
                isLast={i === statusData.nodes.length - 1}
              />
            ))}
          </div>
        )}

        {lastRefresh && (
          <p style={{ textAlign: 'center', fontSize: 11, color: 'var(--color-text-muted)', marginTop: 16 }}>
            Cập nhật lúc {lastRefresh.toLocaleTimeString('vi-VN')} · Tự động làm mới sau 5 phút
          </p>
        )}
      </div>
    </div>
  )
}
