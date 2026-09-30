"""cd backend && rm -f /tmp/t.db && DATABASE_URL=sqlite:////tmp/t.db PYTHONPATH=. python ../tests/test_v11.py"""
from fastapi.testclient import TestClient
from app.main import app
with TestClient(app) as c:
    h = {"Authorization": "Bearer " + c.post("/auth/login", json={"username": "demo", "password": "demo1234"}).json()["token"]}
    g = c.get("/goals").json()[0]["id"]
    # TASK 05 search/filter
    assert {p["category"] for p in c.get("/products?q=running").json()} >= {"Running Shoes"}
    assert all(p["price"] <= 500 for p in c.get("/products?max_price=500").json())
    assert c.get("/products?sort=price_desc").json()[0]["price"] >= c.get("/products?sort=price_asc").json()[0]["price"]
    # TASK 04 product detail
    d = c.get("/products/1").json(); assert d["attributes"] and c.get("/products/9999").status_code == 404
    # TASK 03 persisted context
    b = c.post("/bundles/generate", json={"goal_id": g, "budget": 3000}, headers=h).json()
    c.post(f"/cart/bundle/{b['id']}", headers=h)
    assert c.get("/cart", headers=h).json()["budget"] == 3000
    c.post("/cart/items", json={"product_id": 1, "quantity": 1}, headers=h)
    a = c.post("/cart/analyze", json={}, headers=h).json()  # no body context -> uses stored
    assert a["budget"] == 3000 and any(i["type"] in ("duplicate", "over_budget", "overlap") for i in a["issues"]), a
    c.post("/orders", json={"address": "Bangkok 10110"}, headers=h)
    assert c.get("/cart", headers=h).json()["budget"] is None
    print("ALL OK")
