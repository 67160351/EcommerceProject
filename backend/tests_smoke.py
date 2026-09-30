from fastapi.testclient import TestClient
import os; os.environ["DATABASE_URL"]="sqlite:////tmp/t.db"
from app.main import app
with TestClient(app) as c:
    h={"Authorization":"Bearer "+c.post("/auth/login",json={"username":"demo","password":"demo1234"}).json()["token"]}
    g=c.get("/goals").json()[0]["id"]
    b=c.post("/bundles/generate",json={"goal_id":g,"budget":3000},headers=h).json(); print(b["total"],b["remaining"],[i["name"] for i in b["items"]])
    print(c.post("/bundles/generate",json={"goal_id":g,"budget":500},headers=h).json())
    it=b["items"][0]; alt=it["alternatives"][0]["id"]
    b=c.post(f"/bundles/{b['id']}/replace",json={"old_product_id":it["id"],"new_product_id":alt},headers=h).json(); print(b["total"])
    c.post(f"/cart/bundle/{b['id']}",headers=h)
    bt=[i for i in b["items"] if "Bottle" in i["name"] or "Flask" in i["name"]][0]
    c.post("/cart/items",json={"product_id":bt["id"]},headers=h)
    a=c.post("/cart/analyze",json={"goal_id":g,"budget":3000},headers=h).json(); print([i["message"] for i in a["issues"]])
    print(c.post("/orders",json={"address":"Bangkok 10110"},headers=h).json()["total"], len(c.get("/orders",headers=h).json()))
