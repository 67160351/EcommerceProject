"""cd backend && rm -f /tmp/t.db && DATABASE_URL=sqlite:////tmp/t.db PYTHONPATH=. python ../tests/test_v12.py"""
from fastapi.testclient import TestClient
from app.main import app
def H(c, u, p): return {"Authorization": "Bearer " + c.post("/auth/login", json={"username": u, "password": p}).json()["token"]}
with TestClient(app) as c:
    u, a = H(c, "demo", "demo1234"), H(c, "admin", "admin123")
    assert c.get("/admin/stats", headers=u).status_code == 403
    r = c.put("/profile", json={"full_name": "Demo User", "email": "demo@bundleai.local", "address": "Bangkok 10110"}, headers=u).json()
    assert r["address"] == "Bangkok 10110" and c.get("/profile", headers=u).json()["full_name"] == "Demo User"
    c.post("/cart/items", json={"product_id": 1, "quantity": 2}, headers=u)
    o = c.post("/orders", json={"address": "Bangkok 10110"}, headers=u).json()
    s = c.get("/admin/stats", headers=a).json()
    assert s["total_orders"] == 1 and s["total_sales"] == o["total"] and s["total_customers"] >= 1 and len(s["sales_by_day"]) == 7 and s["top_products"][0]["quantity"] == 2
    stock = lambda: c.get("/products/1").json()["stock"]; before = stock()
    assert c.put(f"/admin/orders/{o['id']}/status", json={"status": "cancelled"}, headers=a).status_code == 200 and stock() == before + 2
    assert c.get("/admin/stats", headers=a).json()["total_sales"] == 0
    assert c.put(f"/admin/orders/{o['id']}/status", json={"status": "bogus"}, headers=a).status_code == 400
    p = c.post("/admin/products", json={"category_id": 1, "name": "Test", "price": 100, "stock": 3}, headers=a).json()
    assert any(x["id"] == p["id"] for x in c.get("/admin/stats", headers=a).json()["low_stock"])
    print("ALL OK")
