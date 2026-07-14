# Deployment Guide — Visa Flow

## Hạ tầng

- **Platform:** Railway (nixpacks) — cấu hình `railway.toml`
- **Runtime:** uvicorn serve FastAPI; frontend build sẵn trong `visa-client/dist/` (dist ĐƯỢC commit — build trước khi commit là một phần của quy trình)
- **DB:** SQLite `visa_flow.db` (file, commit trong repo); có option Postgres qua `psycopg2-binary` + env
- **File khách upload:** `uploads/{app_id}/` trên filesystem

## Env cần thiết

| Biến | Vai trò |
|---|---|
| `ANTHROPIC_API_KEY` | Bắt buộc — mọi AI surface chết nếu thiếu |
| DB URL (nếu Postgres) | Thay SQLite mặc định |

## Quy trình release hiện tại

1. Sửa code → `npm run build` (FE) → commit kèm `dist/`
2. Push `main` → Railway auto-deploy
3. Không có CI/CD pipeline, không chạy test tự động trước deploy

## ⚠️ Rủi ro vận hành đã biết

1. **`railway.toml` không khai volume** → `visa_flow.db` + `uploads/` nằm trên filesystem ephemeral: **redeploy có thể mất sạch dữ liệu khách và file upload**. Cần mount Railway volume cho 2 đường dẫn này trước khi chạy khách thật.
2. **Không auth/ownership** (IDOR toàn cục) — xem `integration-architecture.md`.
3. **CORS mở hoàn toàn** — chấp nhận được cho demo, không cho production.
4. **Admin endpoints không auth** (`api/routers/admin.py` — verify checklist bằng Sonnet).
5. Demo payment không gate — ai cũng qua được màn price.
