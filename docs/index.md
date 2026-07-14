# Project Documentation Index — Visa Flow

> **Điểm vào chính cho AI-assisted work.** Sinh bởi deep scan 2026-07-14, mục tiêu: đủ context để thiết kế eval plan cho toàn sản phẩm.

## Project Overview

- **Type:** multi-part (2 phần: `api` backend + `client` web)
- **Primary Language:** Python (FastAPI) + JavaScript (React 19)
- **Architecture:** REST API + SPA không router; AI qua Anthropic SDK (Haiku + Sonnet)

## Quick Reference

### api (backend)
- **Tech:** Python 3.14, FastAPI 0.135, SQLAlchemy 2.0 (SQLite), anthropic 0.86, PyMuPDF
- **Entry:** `api/main.py` · **AI:** `api/ai.py` (8 surfaces) · **Legacy:** `api/routes/` + `agents/` (pipeline 6 agent, mock OCR)
- **Root:** `api/`, `agents/`, `db/`, `core/`, `static/`

### client (web)
- **Tech:** React 19.2 + Vite 8, switch/case screen state (không router), CSS inline + tokens
- **Entry:** `visa-client/src/App.jsx` · **State:** `context/AppContext.jsx` · 9 screens, 10 components
- **Root:** `visa-client/`

## Generated Documentation

**Đọc theo thứ tự này nếu mới vào project:**

1. [Project Overview](./project-overview.md) — sản phẩm là gì, 8 AI surfaces, phát hiện trọng yếu
2. [Source Tree Analysis](./source-tree-analysis.md) — cây thư mục chú giải, ranh giới 2 thế hệ backend
3. [Integration Architecture](./integration-architecture.md) — flow client↔api từng bước, luồng dữ liệu chéo
4. [Architecture — api](./architecture-api.md) — backend chi tiết: từng AI surface, agents pipeline, form filler
5. [Architecture — client](./architecture-client.md) — frontend: user flow thật (9 màn), AppContext, ChatWidget
6. [API Contracts — api](./api-contracts-api.md) — 31 endpoints (8 gọi LLM), request/response
7. [Data Models — api](./data-models-api.md) — 5 tables, shape các JSON column, lifecycle Application
8. [Component Inventory — client](./component-inventory-client.md) — screens + components + tokens
9. [Development Guide](./development-guide.md) — chạy local, test, quy ước, bẫy đã biết
10. [Deployment Guide](./deployment-guide.md) — Railway, rủi ro volume/IDOR

## Tài liệu chuyên đề có sẵn (không sinh bởi scan này)

- [Chatbot Behavior Spec](./chatbot-behavior-spec.md) — hợp đồng hành vi chat Thu Diễm: persona, FACTS, 10 guardrails, regression seeds → **input trực tiếp cho eval plan phần chat**
- [project-context.md](../project-context.md) — quy ước dev cho AI (đọc đầu mỗi session)
- [TASKS.md](../TASKS.md) — nhật ký việc theo session
- [deferred-work.md](../_bmad-output/implementation-artifacts/deferred-work.md) — việc treo/rủi ro đã biết
- Specs từng story: `_bmad-output/implementation-artifacts/spec-*.md`

## Getting Started (cho eval plan design)

1. Đọc `project-overview.md` (5 phút) → nắm 8 AI surfaces và các phát hiện trọng yếu
2. Phần chat: `chatbot-behavior-spec.md` đã là behavior contract hoàn chỉnh (kèm gợi ý chiều đo)
3. Các surface còn lại: `architecture-api.md` mô tả input/output/prompt từng surface — ground truth để viết expected behaviors
4. `integration-architecture.md` mục "Luồng dữ liệu chéo" liệt kê các bề mặt injection/consistency cần eval
5. Eval asset tái dùng được: `~/japan-visa-bot/tests/personas.json` (format script + expected_topics + should_NOT_contain), `tests/api/test_chat_format.py`, `static/checklists/*.json` (ground truth nội dung)
