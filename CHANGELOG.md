# v1.1
- Security: SECRET_KEY/ADMIN_PASSWORD จาก env, production guard, .gitignore, ไม่ส่ง .env ใน zip
- Cart Doctor context (goal+budget) เก็บที่ backend (carts.goal_id/budget) ไม่หายเมื่อ refresh, migration อัตโนมัติสำหรับ DB v1.0
- Product Detail (#product/ID) พร้อม attributes, Search + Filter (ชื่อ/หมวด/ราคา/เรตติ้ง/stock/เรียงลำดับ)
- ข้อความ validation error ชัดขึ้น, จำ Bundle ล่าสุดหลัง refresh
