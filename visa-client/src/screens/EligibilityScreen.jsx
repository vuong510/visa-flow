import { useEffect, useState } from 'react'
import NavHeader from '../components/NavHeader'
import ProgressBar from '../components/ProgressBar'
import BottomActionArea from '../components/BottomActionArea'
import CTAButton from '../components/CTAButton'
import { useApp } from '../context/AppContext'

function SkeletonCard() {
  return (
    <div style={{ padding: '0 20px' }}>
      <div style={{ background: 'var(--color-surface)', borderRadius: 'var(--radius-card)', padding: 24, boxShadow: 'var(--shadow-card)' }}>
        <div style={{ textAlign: 'center', marginBottom: 20 }}>
          <div className="skeleton" style={{ width: 64, height: 64, borderRadius: '50%', margin: '0 auto 16px' }} />
          <div className="skeleton" style={{ width: '70%', height: 22, margin: '0 auto 10px' }} />
          <div className="skeleton" style={{ width: '90%', height: 14, margin: '0 auto 6px' }} />
          <div className="skeleton" style={{ width: '80%', height: 14, margin: '0 auto' }} />
        </div>
        <div style={{ borderTop: '1px solid var(--color-border)', paddingTop: 16, marginTop: 4 }}>
          <div className="skeleton" style={{ width: '50%', height: 12, marginBottom: 8 }} />
          <div className="skeleton" style={{ width: '85%', height: 12, marginBottom: 6 }} />
          <div className="skeleton" style={{ width: '75%', height: 12 }} />
        </div>
      </div>
      <p style={{ textAlign: 'center', marginTop: 16, fontSize: 13, color: 'var(--color-text-muted)' }}>
        AI đang đánh giá hồ sơ của bạn...
      </p>
    </div>
  )
}

function EligibilityCard({ data }) {
  const isPass = data.result === 'eligible'
  const isEdge = data.result === 'edge_case'
  const isFail = data.result === 'not_eligible'

  const iconMap = { eligible: '✅', edge_case: '⚠️', not_eligible: '❌' }
  const colorMap = {
    eligible:   { bg: '#d1fae5', border: '#34d399', headlineColor: '#065f46' },
    edge_case:  { bg: '#fef3c7', border: '#fbbf24', headlineColor: '#92400e' },
    not_eligible: { bg: '#fee2e2', border: '#f87171', headlineColor: '#991b1b' },
  }
  const c = colorMap[data.result] || colorMap.eligible

  return (
    <div style={{
      background: c.bg,
      border: `1.5px solid ${c.border}`,
      borderRadius: 'var(--radius-card)',
      padding: 24,
    }}>
      <div style={{ textAlign: 'center', marginBottom: 16 }}>
        <div style={{ fontSize: 40, marginBottom: 10 }}>{iconMap[data.result]}</div>
        <h2 style={{ fontSize: 20, fontWeight: 700, color: c.headlineColor, lineHeight: 1.3 }}>
          {data.headline}
        </h2>
        {data.reason && (
          <p style={{ fontSize: 13, color: c.headlineColor, marginTop: 8, opacity: 0.85, lineHeight: 1.5 }}>
            {data.reason}
          </p>
        )}
      </div>

      {data.bullets && data.bullets.length > 0 && (
        <ul style={{ paddingLeft: 18, margin: 0, borderTop: `1px solid ${c.border}`, paddingTop: 14 }}>
          {data.bullets.map((b, i) => (
            <li key={i} style={{ fontSize: 13, lineHeight: 1.6, color: c.headlineColor, marginBottom: 4 }}>
              {b}
            </li>
          ))}
        </ul>
      )}

      {data.confidence_label && (
        <p style={{ fontSize: 11, color: c.headlineColor, opacity: 0.7, marginTop: 12, textAlign: 'right' }}>
          {data.confidence_label}
        </p>
      )}
    </div>
  )
}

export default function EligibilityScreen() {
  const { applicationId, API_BASE, navigate, setEligibilityResult } = useApp()
  const [loading, setLoading] = useState(true)
  const [showSkeleton, setShowSkeleton] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    const timer = setTimeout(() => {
      if (loading) setShowSkeleton(true)
    }, 3000)
    runEligibility()
    return () => clearTimeout(timer)
  }, [])

  async function runEligibility() {
    try {
      const res = await fetch(`${API_BASE}/api/application/${applicationId}/eligibility`, {
        method: 'POST',
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setResult(data)
      setEligibilityResult(data.result)
    } catch (e) {
      setError('Không thể kết nối AI. Vui lòng thử lại.')
    } finally {
      setLoading(false)
      setShowSkeleton(false)
    }
  }

  const canContinue = result && result.result !== 'not_eligible'

  return (
    <div style={{ minHeight: '100dvh', display: 'flex', flexDirection: 'column', background: 'var(--color-background)' }}>
      <NavHeader title="Đánh giá hồ sơ" showBack={false} />
      <ProgressBar current={7} total={11} />

      <div style={{ flex: 1, padding: '24px 20px', paddingBottom: canContinue ? 'calc(100px + env(safe-area-inset-bottom))' : 24 }}>
        {loading && showSkeleton && <SkeletonCard />}
        {loading && !showSkeleton && (
          <p style={{ textAlign: 'center', color: 'var(--color-text-muted)', marginTop: 40 }}>
            AI đang đánh giá hồ sơ của bạn...
          </p>
        )}

        {error && (
          <div style={{ background: '#fee2e2', border: '1px solid #f87171', borderRadius: 12, padding: 20, textAlign: 'center' }}>
            <p style={{ color: '#991b1b', marginBottom: 16 }}>{error}</p>
            <CTAButton label="Thử lại" onClick={() => { setError(''); setLoading(true); setShowSkeleton(false); runEligibility() }} />
          </div>
        )}

        {result && !loading && (
          <>
            <EligibilityCard data={result} />
            {result.result === 'not_eligible' && (
              <div style={{ marginTop: 20, padding: 16, background: 'var(--color-surface)', borderRadius: 12, textAlign: 'center' }}>
                <p style={{ fontSize: 13, color: 'var(--color-text-muted)', lineHeight: 1.6 }}>
                  Bạn có thể liên hệ tư vấn viên để được hỗ trợ thêm hoặc điều chỉnh hồ sơ.
                </p>
                <a
                  href="mailto:support@visaflow.vn"
                  style={{ display: 'inline-block', marginTop: 10, fontSize: 13, color: 'var(--color-cta)', fontWeight: 600, textDecoration: 'none' }}
                >
                  Liên hệ tư vấn →
                </a>
              </div>
            )}
          </>
        )}
      </div>

      {canContinue && (
        <BottomActionArea>
          <CTAButton label="Xem chi phí dịch vụ" onClick={() => navigate('price')} />
        </BottomActionArea>
      )}
    </div>
  )
}
