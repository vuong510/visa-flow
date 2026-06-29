import NavHeader from '../components/NavHeader'
import OptionButton from '../components/OptionButton'
import { useApp } from '../context/AppContext'

export default function DestinationScreen() {
  const { applicationId, updateDestination, navigate } = useApp()

  async function choose(dest) {
    await updateDestination(applicationId, dest)
    navigate('profile-questions')
  }

  return (
    <div style={{ minHeight: '100dvh', display: 'flex', flexDirection: 'column', background: 'var(--color-background)' }}>
      <NavHeader title="Chọn điểm đến" showBack={false} />

      <div style={{ flex: 1, padding: '24px 20px' }}>
        <div style={{
          background: 'var(--color-surface)',
          borderRadius: 'var(--radius-card)',
          padding: 'var(--card-inner)',
          boxShadow: 'var(--shadow-card)',
        }}>
          <h2 style={{ fontSize: 20, fontWeight: 600, marginBottom: 8, lineHeight: 1.35 }}>
            Bạn muốn xin visa đi đâu
          </h2>
          <p style={{ fontSize: 14, color: 'var(--color-text-muted)', marginBottom: 20 }}>
            Chúng tôi hỗ trợ Nhật Bản và Trung Quốc cho công dân Việt Nam
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <OptionButton label="🇯🇵  Nhật Bản" onClick={() => choose('japan')} />
            <OptionButton label="🇨🇳  Trung Quốc" onClick={() => choose('china')} />
          </div>
        </div>
      </div>
    </div>
  )
}
