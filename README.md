# BundleAI v1.2
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
Demo user: `demo / demo1234` · Admin: `admin / admin123` (**เฉพาะ development**)

## Production / Security (Render)
ตั้ง Environment Variables: `ENV=production`, `DATABASE_URL`, `SECRET_KEY` (สุ่ม >=32 ตัวอักษร), `ADMIN_PASSWORD`
ถ้าไม่ตั้ง `SECRET_KEY`/`ADMIN_PASSWORD` แอปจะไม่ยอม start ใน production และจะไม่สร้างบัญชี demo (เปิดได้ด้วย `SEED_DEMO=1`)
ห้าม commit `.env` (อยู่ใน `.gitignore` แล้ว) สร้างค่าสุ่ม: `python -c "import secrets;print(secrets.token_urlsafe(48))"`

## Test
`cd backend && rm -f /tmp/t.db && DATABASE_URL=sqlite:////tmp/t.db PYTHONPATH=. python ../tests/test_v11.py` และ `test_v12.py`

## Structure
`backend/app/services/bundle_engine.py` (scoring 40/30/20/10), `cart_doctor.py` (duplicate/overlap/over-budget/missing/low-utilization), `seed.py`
