import { useState } from 'react'
import { useApp } from '../context/AppContext'
import NavHeader from '../components/NavHeader'
import ProgressBar from '../components/ProgressBar'
import OptionButton from '../components/OptionButton'
import CTAButton from '../components/CTAButton'
import BottomActionArea from '../components/BottomActionArea'

const TOTAL_STEPS = 10

const EMPLOYMENT_OPTIONS = [
  { value: 'employee',       label: 'Nhân viên / Công ty' },
  { value: 'student',        label: 'Sinh viên' },
  { value: 'business_owner', label: 'Chủ doanh nghiệp' },
  { value: 'freelancer',     label: 'Freelancer / Tự kinh doanh' },
  { value: 'homemaker',      label: 'Nội trợ' },
  { value: 'retired',        label: 'Đã nghỉ hưu' },
]

const INCOME_OPTIONS = [
  { value: 'under_10m', label: 'Dưới 10 triệu đồng/tháng' },
  { value: '10_20m',    label: '10 – 20 triệu đồng/tháng' },
  { value: '20_40m',    label: '20 – 40 triệu đồng/tháng' },
  { value: 'over_40m',  label: 'Trên 40 triệu đồng/tháng' },
]

const DENIAL_COUNTRY_OPTIONS = [
  { value: 'japan', label: 'Nhật Bản' },
  { value: 'china', label: 'Trung Quốc' },
  { value: 'other', label: 'Quốc gia khác' },
]

const cardStyle = {
  background: 'var(--color-surface)',
  borderRadius: 'var(--radius-card)',
  padding: 'var(--card-inner)',
  boxShadow: 'var(--shadow-card)',
}

const h2Style = {
  fontSize: 20,
  fontWeight: 600,
  lineHeight: 1.35,
  marginBottom: 8,
  color: 'var(--color-text-primary)',
}

const captionStyle = {
  fontSize: 12,
  fontWeight: 400,
  lineHeight: 1.45,
  color: 'var(--color-text-muted)',
  marginBottom: 20,
}

const inputStyle = {
  width: '100%',
  height: 48,
  padding: '0 12px',
  borderRadius: 'var(--radius-input)',
  border: '1px solid var(--color-border)',
  fontSize: 15,
  fontFamily: 'inherit',
  background: 'var(--color-surface)',
  color: 'var(--color-text-primary)',
  marginTop: 6,
  boxSizing: 'border-box',
}

const inputErrorStyle = {
  ...inputStyle,
  border: '1px solid var(--color-error)',
}

const labelStyle = {
  fontSize: 14,
  fontWeight: 500,
  color: 'var(--color-text-secondary)',
  display: 'block',
}

function InlineError({ text }) {
  return (
    <p
      role="alert"
      aria-live="assertive"
      style={{
        marginTop: 8,
        fontSize: 13,
        color: 'var(--color-error)',
        lineHeight: 1.45,
      }}
    >
      {text}
    </p>
  )
}

export default function ProfileQuestionsScreen() {
  const { profile, setProfile, navigate, applicationId, destination, API_BASE } = useApp()

  const [currentQ, setCurrentQ] = useState(1)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  // Q3: travel dates
  const [departure, setDeparture] = useState(profile.travel_dates?.departure || '')
  const [returnDate, setReturnDate] = useState(profile.travel_dates?.return || '')

  // Q4: prior denial
  const [denialAnswer, setDenialAnswer] = useState(
    profile.prior_denial === true ? 'yes' : profile.prior_denial === false ? 'no' : ''
  )
  const [denialDate, setDenialDate] = useState(profile.denial_date || '')
  const [denialCountry, setDenialCountry] = useState(profile.denial_country || '')

  // Q5: passport expiry
  const [passportExpiry, setPassportExpiry] = useState(profile.passport_expiry || '')

  const today = new Date().toISOString().split('T')[0]
  const tomorrow = new Date(Date.now() + 86400000).toISOString().split('T')[0]

  function goBack() {
    setError('')
    if (currentQ === 1) {
      navigate('destination')
    } else {
      setCurrentQ(q => q - 1)
    }
  }

  function advanceTo(next) {
    setError('')
    setCurrentQ(next)
  }

  // Q1 auto-advance
  function chooseEmployment(value) {
    setProfile(p => ({ ...p, employment_type: value }))
    advanceTo(2)
  }

  // Q2 auto-advance
  function choosePriorStamps(value) {
    setProfile(p => ({ ...p, has_prior_stamps: value === 'yes' }))
    advanceTo(3)
  }

  // Q3 continue
  function submitTravelDates() {
    if (!departure) { setError('Vui lòng chọn ngày khởi hành'); return }
    if (!returnDate) { setError('Vui lòng chọn ngày về'); return }
    if (departure <= today) { setError('Ngày khởi hành phải là ngày trong tương lai'); return }
    if (returnDate < departure) { setError('Ngày về phải sau ngày khởi hành'); return }
    setProfile(p => ({ ...p, travel_dates: { departure, return: returnDate } }))
    advanceTo(4)
  }

  // Q4 choice
  function chooseDenial(value) {
    setError('')
    setDenialAnswer(value)
    if (value === 'no') {
      setProfile(p => ({ ...p, prior_denial: false, denial_date: null, denial_country: null }))
      advanceTo(5)
    }
  }

  // Q4 continue (when "Có" selected)
  function submitDenialFollowup() {
    if (!denialDate) { setError('Vui lòng nhập ngày bị từ chối'); return }
    if (denialDate >= today) { setError('Ngày bị từ chối phải là ngày trong quá khứ'); return }
    if (!denialCountry) { setError('Vui lòng chọn quốc gia'); return }
    setProfile(p => ({ ...p, prior_denial: true, denial_date: denialDate, denial_country: denialCountry }))
    advanceTo(5)
  }

  // Q5 continue
  function submitPassportExpiry() {
    if (!passportExpiry) { setError('Vui lòng nhập ngày hết hạn hộ chiếu'); return }
    if (passportExpiry <= today) { setError('Hộ chiếu đã hết hạn. Vui lòng gia hạn trước khi xin visa'); return }
    setProfile(p => ({ ...p, passport_expiry: passportExpiry }))
    advanceTo(6)
  }

  // Q6 auto-advance + submit profile
  async function chooseIncome(value) {
    setSubmitting(true)
    setError('')
    const updatedProfile = { ...profile, income_range: value }
    setProfile(updatedProfile)
    try {
      const res = await fetch(`${API_BASE}/api/application/${applicationId}/profile`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          profile_json: { ...updatedProfile, destination },
          travel_dates: updatedProfile.travel_dates,
        }),
      })
      if (!res.ok) throw new Error('server error')
      navigate('eligibility-loading')
    } catch {
      setError('Không thể lưu hồ sơ. Vui lòng thử lại.')
      setSubmitting(false)
    }
  }

  // ── Question renderers ──────────────────────────────────────────

  function renderQ1() {
    return (
      <div style={cardStyle}>
        <h2 style={h2Style}>Loại hình công việc của bạn là gì</h2>
        <p style={captionStyle}>
          Câu trả lời này ảnh hưởng đến đánh giá hồ sơ của bạn.
        </p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {EMPLOYMENT_OPTIONS.map(opt => (
            <OptionButton
              key={opt.value}
              label={opt.label}
              selected={profile.employment_type === opt.value}
              onClick={() => chooseEmployment(opt.value)}
            />
          ))}
        </div>
      </div>
    )
  }

  function renderQ2() {
    return (
      <div style={cardStyle}>
        <h2 style={h2Style}>Bạn đã từng đến Nhật Bản hoặc Trung Quốc chưa</h2>
        <p style={{ ...captionStyle, marginBottom: 20 }}>
          Hộ chiếu có dấu nhập cảnh trước đây là tín hiệu tích cực cho hồ sơ.
        </p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <OptionButton
            label="Có, tôi đã từng đến"
            selected={profile.has_prior_stamps === true}
            onClick={() => choosePriorStamps('yes')}
          />
          <OptionButton
            label="Chưa, đây là lần đầu"
            selected={profile.has_prior_stamps === false}
            onClick={() => choosePriorStamps('no')}
          />
        </div>
      </div>
    )
  }

  function renderQ3() {
    return (
      <div style={cardStyle}>
        <h2 style={h2Style}>Bạn dự định đi khi nào</h2>
        <p style={captionStyle}>
          Chúng tôi sẽ kiểm tra tính khả thi về thời gian chuẩn bị hồ sơ.
        </p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div>
            <label htmlFor="departure-date" style={labelStyle}>Ngày khởi hành</label>
            <input
              id="departure-date"
              type="date"
              value={departure}
              min={tomorrow}
              onChange={e => { setDeparture(e.target.value); setError('') }}
              style={error && !departure ? inputErrorStyle : inputStyle}
            />
          </div>
          <div>
            <label htmlFor="return-date" style={labelStyle}>Ngày về</label>
            <input
              id="return-date"
              type="date"
              value={returnDate}
              min={departure || tomorrow}
              onChange={e => { setReturnDate(e.target.value); setError('') }}
              style={error && !returnDate ? inputErrorStyle : inputStyle}
            />
          </div>
          {error && <InlineError text={error} />}
        </div>
      </div>
    )
  }

  function renderQ4() {
    const showFollowup = denialAnswer === 'yes'

    return (
      <div style={cardStyle}>
        <h2 style={h2Style}>Bạn đã từng bị từ chối visa không</h2>
        <p style={captionStyle}>
          Câu trả lời này ảnh hưởng đến đánh giá hồ sơ của bạn.
        </p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <OptionButton
            label="Có"
            selected={denialAnswer === 'yes'}
            onClick={() => chooseDenial('yes')}
          />
          <OptionButton
            label="Không"
            selected={denialAnswer === 'no'}
            onClick={() => chooseDenial('no')}
          />
        </div>

        {showFollowup && (
          <div style={{ marginTop: 20, display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div style={{ height: 1, background: 'var(--color-border)' }} />
            <div>
              <label htmlFor="denial-date" style={labelStyle}>Ngày bị từ chối</label>
              <input
                id="denial-date"
                type="date"
                value={denialDate}
                max={today}
                onChange={e => { setDenialDate(e.target.value); setError('') }}
                style={inputStyle}
              />
            </div>
            <div>
              <label htmlFor="denial-country" style={labelStyle}>Quốc gia từ chối</label>
              <select
                id="denial-country"
                value={denialCountry}
                onChange={e => { setDenialCountry(e.target.value); setError('') }}
                style={{
                  ...inputStyle,
                  paddingRight: 32,
                  cursor: 'pointer',
                }}
              >
                <option value="">Chọn quốc gia...</option>
                {DENIAL_COUNTRY_OPTIONS.map(opt => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>
            {error && <InlineError text={error} />}
          </div>
        )}
      </div>
    )
  }

  function renderQ5() {
    return (
      <div style={cardStyle}>
        <h2 style={h2Style}>Hộ chiếu của bạn hết hạn khi nào</h2>
        <p style={captionStyle}>
          Hộ chiếu cần còn hạn ít nhất 6 tháng tính từ ngày khởi hành.
        </p>
        <div>
          <label htmlFor="passport-expiry" style={labelStyle}>Ngày hết hạn</label>
          <input
            id="passport-expiry"
            type="date"
            value={passportExpiry}
            min={tomorrow}
            onChange={e => { setPassportExpiry(e.target.value); setError('') }}
            style={error ? inputErrorStyle : inputStyle}
          />
          {error && <InlineError text={error} />}
        </div>
      </div>
    )
  }

  function renderQ6() {
    return (
      <div style={cardStyle}>
        <h2 style={h2Style}>Thu nhập hàng tháng của bạn khoảng bao nhiêu</h2>
        <p style={{
          fontSize: 13,
          lineHeight: 1.55,
          color: 'var(--color-text-muted)',
          marginBottom: 20,
          fontStyle: 'normal',
        }}>
          Thông tin này giúp chúng tôi đánh giá hồ sơ theo kinh nghiệm thực tế. Chúng tôi không tư vấn về số dư ngân hàng tối thiểu vì Đại sứ quán không công bố ngưỡng chính thức.
        </p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {INCOME_OPTIONS.map(opt => (
            <OptionButton
              key={opt.value}
              label={opt.label}
              selected={profile.income_range === opt.value}
              onClick={() => !submitting && chooseIncome(opt.value)}
              disabled={submitting}
            />
          ))}
        </div>
        {error && <InlineError text={error} />}
      </div>
    )
  }

  // ── Screen layout ───────────────────────────────────────────────

  const needsBottomCTA =
    currentQ === 3 ||
    (currentQ === 4 && denialAnswer === 'yes') ||
    currentQ === 5 ||
    (currentQ === 6 && submitting)

  const questionContent = {
    1: renderQ1(),
    2: renderQ2(),
    3: renderQ3(),
    4: renderQ4(),
    5: renderQ5(),
    6: renderQ6(),
  }

  return (
    <div style={{
      minHeight: '100dvh',
      display: 'flex',
      flexDirection: 'column',
      background: 'var(--color-background)',
    }}>
      <NavHeader title="Hồ sơ của bạn" onBack={goBack} showBack />
      <ProgressBar current={currentQ} total={TOTAL_STEPS} />

      <div style={{
        flex: 1,
        padding: `24px 20px ${needsBottomCTA ? '120px' : '24px'}`,
      }}>
        {questionContent[currentQ]}
      </div>

      {currentQ === 3 && (
        <BottomActionArea>
          <CTAButton label="Tiếp tục" onClick={submitTravelDates} />
        </BottomActionArea>
      )}

      {currentQ === 4 && denialAnswer === 'yes' && (
        <BottomActionArea>
          <CTAButton label="Tiếp tục" onClick={submitDenialFollowup} />
        </BottomActionArea>
      )}

      {currentQ === 5 && (
        <BottomActionArea>
          <CTAButton label="Tiếp tục" onClick={submitPassportExpiry} />
        </BottomActionArea>
      )}

      {currentQ === 6 && submitting && (
        <BottomActionArea>
          <CTAButton label="Tiếp tục" loading disabled />
        </BottomActionArea>
      )}
    </div>
  )
}
