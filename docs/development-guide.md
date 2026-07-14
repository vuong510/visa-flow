# Development Guide — Visa Flow

## Yêu cầu

- Python 3.14 (venv có sẵn tại `./venv`), Node 18+ (npm), `ANTHROPIC_API_KEY` trong env/.env
- Playwright + Chromium nếu chạy e2e (`npx playwright install chromium`)

## Chạy local

```bash
# Backend (từ repo root)
source venv/bin/activate
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend
cd visa-client && npm run dev -- --port 5173
```

Client đọc `API_BASE` từ AppContext — mặc định trỏ backend local.

## Lệnh thường dùng

| Việc | Lệnh | Ghi chú |
|---|---|---|
| Lint FE | `cd visa-client && npm run lint` | oxlint; 2 warning pre-existing ở ChecklistScreen (:77, :117) |
| Build FE | `cd visa-client && npm run build` | dist/ ĐƯỢC commit theo convention repo |
| Test API | `python3 -m pytest tests/api -q` | pytest cài ở system python, KHÔNG có trong venv |
| Test e2e | `npx playwright test tests/e2e/` | Cần backend+frontend đang chạy + API key (flow đi qua eligibility AI). ⚠️ `checklist_skip.spec.ts` helper `completeFlowToChecklist` lỗi thời so với UI thật (mong nhập ngày ngay sau destination; thực tế là Q3 trong profile-questions) — khả năng cao fail toàn suite |
| Compile check BE | `python3 -m py_compile api/ai.py` | dùng khi sửa prompt |

## Quy ước dự án (từ `project-context.md` + `CLAUDE.md`)

- Đầu session AI: đọc `CLAUDE.md` + `TASKS.md`; cuối session update `TASKS.md`
- Model routing: Haiku cho chat/eligibility/itinerary, Sonnet cho vision (OCR, document review)
- KHÔNG đổi PDF form logic khi chưa test (`form_filler.py` đầy workaround XFA)
- Mọi copy tiếng Việt theo `~/docs/vi-ux-style-guide.md`; facts visa theo chị Yến (domain authority)
- BottomSheet: conditional render + `open={true}` cùng nhau; điều hướng bằng `navigate(screenName)` qua AppContext
- Checklist item hỗ trợ `optional: true`; sửa nội dung checklist = sửa `static/checklists/*.json` (không sửa code)
- BMad workflow: spec trong `_bmad-output/implementation-artifacts/`, việc treo trong `deferred-work.md`

## Bẫy đã biết khi dev

- `venv` thiếu pytest — dùng system `python3 -m pytest`
- React StrictMode dev có thể double-POST `/eligibility`
- Reload browser = mất screen state (chỉ applicationId/sessionId persist) — test flow phải đi lại từ đầu
- `ChatWidget.jsx:6` return trước useState (vi phạm Rules of Hooks tiềm ẩn khi vào/ra màn price)
