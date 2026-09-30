# BundleAI v1.0
Goal → Budget → Bundle → Cart Doctor → Checkout (FastAPI + SQLAlchemy/PostgreSQL + HTML/JS)

## Run with Docker (PostgreSQL)
```
cp .env.example .env
docker compose up --build
```
เปิด http://localhost:8000 (API docs: /docs)

## Run locally (SQLite, ไม่ต้องใช้ Docker)
```
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload      # เปิด http://localhost:8000
```
Demo user: `demo / demo1234` · Admin: `admin / admin123` (เปลี่ยนก่อน deploy จริง)

## Smoke test
`cd backend && rm -f /tmp/t.db && PYTHONPATH=. python tests_smoke.py`

## Demo flow
Home → เริ่มวิ่ง + งบ 3000 → Bundle → เปลี่ยนรองเท้า → Add Bundle → เพิ่มขวดน้ำซ้ำใน Catalog → Cart Doctor แจ้ง Duplicate → ทำตามคำแนะนำ → Checkout → Orders

## Structure
`backend/app/services/bundle_engine.py` (scoring 40/30/20/10), `cart_doctor.py` (duplicate/overlap/over-budget/missing/low-utilization), `seed.py`
