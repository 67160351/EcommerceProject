# v1.2
- Profile (ชื่อ/อีเมล/ที่อยู่ + Order History ล่าสุด), หน้า Checkout เติมที่อยู่จาก Profile อัตโนมัติ
- Admin Dashboard: KPI, กราฟยอดขาย 7 วัน, สถานะ Order, สินค้าขายดี, Stock ต่ำ
- Admin จัดการสินค้า (ราคา/stock/เปิด-ปิดขาย/เพิ่มสินค้า) และเปลี่ยนสถานะ Order (ยกเลิกแล้วคืน stock)
- Migration อัตโนมัติสำหรับคอลัมน์ users.full_name/address

# v1.1
- Security: SECRET_KEY/ADMIN_PASSWORD จาก env, production guard, .gitignore, ไม่ส่ง .env ใน zip
- Cart Doctor context (goal+budget) เก็บที่ backend (carts.goal_id/budget) ไม่หายเมื่อ refresh, migration อัตโนมัติสำหรับ DB v1.0
- Product Detail (#product/ID) พร้อม attributes, Search + Filter (ชื่อ/หมวด/ราคา/เรตติ้ง/stock/เรียงลำดับ)
- ข้อความ validation error ชัดขึ้น, จำ Bundle ล่าสุดหลัง refresh
