# Source Tree — Visa Flow

Cây thư mục chú giải (multi-part: `api` backend + `client` frontend). Cập nhật 2026-07-14.

```
visa-flow/
├── api/                      # PART: api — FastAPI backend
│   ├── main.py               # Entry point: FastAPI app, CORS mở, mount router /api
│   ├── ai.py                 # TẤT CẢ hàm gọi Claude: eligibility, review vision, chat,
│   │                         #   itinerary, extract ID + generate_checklist (deterministic)
│   ├── form_filler.py        # Điền 2 form PDF MOFA bằng PyMuPDF (XFA widgets, radio theo tọa độ)
│   ├── routers/              # THẾ HỆ HIỆN HÀNH — client đang dùng
│   │   ├── application.py    # CRUD application, profile, eligibility, checklist, documents, submit
│   │   ├── chat.py           # POST /chat → chat_with_haiku (+ nhánh itinerary keyword)
│   │   ├── extract.py        # POST /extract-id → Sonnet vision OCR hộ chiếu/CCCD
│   │   ├── forms.py          # POST /forms/download → ZIP 2 PDF đã điền
│   │   └── admin.py          # Admin verify checklist (Sonnet, KHÔNG auth)
│   └── routes/               # THẾ HỆ CŨ (legacy) — client KHÔNG gọi
│       └── ...               # /api/v1/cases (agents pipeline), policies, cv-jobs
├── agents/                   # Pipeline 6 agent chấm hồ sơ visa Nhật (chỉ gọi từ /api/v1/cases)
│   ├── pipeline.py           # Orchestrator: Gatekeeper→Inspector→(Detective ∥ Navigator)→Analyst
│   ├── gatekeeper.py         # Haiku — sàng lọc đầu vào
│   ├── inspector.py          # Sonnet — soi tài liệu (⚠️ input là MOCK OCR, không đọc file thật)
│   ├── detective.py          # Sonnet — tìm mâu thuẫn hồ sơ
│   ├── navigator.py          # Haiku — lộ trình bổ sung
│   ├── analyst.py            # Sonnet — verdict cuối
│   └── librarian.py          # Sonnet — quản policy_rules (không agent nào tiêu thụ output)
├── core/config.py            # ANTHROPIC_API_KEY, hằng model SONNET/HAIKU
├── db/
│   ├── models.py             # applications, documents (+3 bảng legacy: visa_cases, policy_rules, policy_drafts)
│   └── session.py            # engine + get_db (SQLite mặc định, Postgres option)
├── static/
│   ├── checklists/           # japan.json, china.json — NGUỒN SỰ THẬT checklist (deterministic)
│   │                         #   schema: meta / universal / by_employment / confidence_notes
│   ├── visa_form_blank.pdf   # Form MOFA trắng (input của form_filler)
│   └── schedule_blank.pdf    # Form lịch trình trắng
├── visa-client/              # PART: client — React 19 + Vite 8, KHÔNG router
│   └── src/
│       ├── App.jsx           # switch/case theo state `screen` (9 màn)
│       ├── context/AppContext.jsx  # State toàn cục; chỉ applicationId+sessionId persist localStorage
│       ├── screens/          # 9 màn: landing → destination → profile-questions(Q1-Q6) →
│       │                     #   eligibility → price → form-filling(4 sub-step) → checklist →
│       │                     #   status-timeline → result
│       └── components/       # 10 components (NavHeader, ChatWidget, BottomSheet, DocumentItem,
│                             #   CTAButton, StatusChip, ProgressBar...; PersonalInfoModal = DEAD CODE)
├── uploads/{app_id}/         # File khách upload (⚠️ railway.toml không khai volume)
├── tests/
│   ├── api/                  # pytest (test_checklist, test_chat_format)
│   └── e2e/                  # Playwright (checklist_skip ⚠️ helper lỗi thời, chat_widget)
├── docs/                     # Tài liệu AI-context (bộ này) + chatbot-behavior-spec.md
├── _bmad-output/             # Specs (implementation-artifacts/spec-*.md), planning, deferred-work.md
├── visa_flow.db              # SQLite (commit trong repo)
├── railway.toml              # Deploy Railway (nixpacks)
├── requirements.txt          # FastAPI, SQLAlchemy, anthropic 0.86, PyMuPDF...
├── playwright.config.ts      # E2e config (cần app đang chạy)
├── project-context.md        # Quy ước dự án cho AI (đọc đầu session)
├── CLAUDE.md / TASKS.md      # Session rules + nhật ký việc
└── travel-news.html          # Trang tĩnh lẻ (ngoài flow)
```

## Điểm vào & ranh giới

- **Client → API:** mọi fetch qua `API_BASE` + `/api/*` (routers/). Client KHÔNG gọi `/api/v1/*` (routes/ legacy).
- **2 thế hệ backend song song:** `api/routers/` (sản phẩm hiện hành) vs `api/routes/` + `agents/` (pipeline chấm hồ sơ thế hệ cũ, còn sống nhưng chạy mock OCR).
- **Nguồn sự thật nội dung:** `static/checklists/*.json` nuôi cả endpoint checklist lẫn chat prompt; `docs/chatbot-behavior-spec.md` là hợp đồng hành vi chat.
