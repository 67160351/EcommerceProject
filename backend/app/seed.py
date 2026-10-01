import os
from .models import *
DATA = {  # category: [(name, price, stock, rating, popularity)]
 "Running Shoes": [("Starter Runner",1290,20,4.0,.6),("Road Runner Pro",1990,15,4.5,.9),("Elite Carbon Runner",2990,5,4.8,.5)],
 "Running Socks": [("Basic Run Socks",190,50,4.0,.5),("Cushion Run Socks",290,40,4.6,.8)],
 "Running Bottle": [("Handheld Bottle 500ml",390,30,4.3,.7),("Soft Flask 350ml",450,10,4.4,.4)],
 "Running Belt": [("Slim Running Belt",290,25,4.2,.6),("Zip Running Belt",390,20,4.4,.5)],
 "Sports Cap": [("Dry-Fit Cap",250,25,4.1,.5),("Visor Cap",190,25,4.0,.4)],
 "Tent": [("2P Dome Tent",1990,10,4.3,.8),("3P Family Tent",3200,6,4.5,.6)],
 "Sleeping Bag": [("Lite Sleeping Bag",690,20,4.2,.7),("Warm Sleeping Bag",1190,12,4.6,.6)],
 "Camping Mat": [("Foam Mat",350,30,4.0,.6),("Self-Inflating Mat",890,12,4.5,.5)],
 "Headlamp": [("LED Headlamp",350,40,4.4,.8),("Rechargeable Headlamp",590,20,4.6,.6)],
 "Mouse": [("Basic Gaming Mouse",590,30,4.2,.7),("Pro Gaming Mouse",1490,10,4.7,.8)],
 "Keyboard": [("Mechanical Keyboard",1290,20,4.4,.8),("Membrane Keyboard",590,30,3.9,.5)],
 "Headset": [("Gaming Headset",990,15,4.3,.7),("Budget Headset",490,25,3.9,.5)],
 "Mousepad": [("XL Mousepad",290,40,4.3,.6),("Standard Mousepad",150,50,4.0,.5)],
}
GOALS = {
 "เริ่มวิ่ง (Start Running)": [("Running Shoes","essential","ปกป้องเท้าและลดแรงกระแทก"),("Running Socks","recommended","ลดการเสียดสีและตุ่มพอง"),
   ("Running Bottle","recommended","ดื่มน้ำระหว่างวิ่ง"),("Running Belt","recommended","เก็บมือถือ/กุญแจ"),("Sports Cap","optional","กันแดด")],
 "แคมป์ปิ้ง (Camping)": [("Tent","essential","ที่พักหลัก"),("Sleeping Bag","essential","ความอบอุ่นตอนนอน"),
   ("Camping Mat","recommended","กันความเย็นจากพื้น"),("Headlamp","recommended","แสงสว่างตอนกลางคืน")],
 "เริ่มเล่นเกม (Gaming)": [("Mouse","essential","ควบคุมเกม"),("Keyboard","essential","พิมพ์/ควบคุมเกม"),
   ("Headset","recommended","เสียงและการสื่อสาร"),("Mousepad","optional","เมาส์ลื่นและแม่นยำขึ้น")],
}
ATTR = {"Running Shoes":{"Type":"Road running","Cushioning":"Medium"},"Running Socks":{"Material":"Polyester blend"},
 "Running Bottle":{"Capacity":"350-500 ml"},"Running Belt":{"Fits":"Phone up to 6.7 in"},"Tent":{"Season":"3-season","Waterproof":"3000 mm"},
 "Sleeping Bag":{"Comfort temp":"10-15 C"},"Mouse":{"Connection":"USB"},"Keyboard":{"Layout":"Full size"},"Headset":{"Connection":"3.5 mm / USB"}}
def seed_attributes(db):
    if db.query(ProductAttribute).count(): return
    for p in db.query(Product).all():
        for k, v in ATTR.get(p.category.name, {}).items(): db.add(ProductAttribute(product_id=p.id, key=k, value=v))
    db.commit()
def seed(db, hash_fn):
    if db.query(Category).count(): return
    cats = {}
    for c, prods in DATA.items():
        cat = Category(name=c); db.add(cat); db.flush(); cats[c] = cat.id
        for n, pr, st, ra, po in prods:
            db.add(Product(category_id=cat.id, name=n, price=pr, stock=st, rating=ra, popularity=po, description=f"{n} - {c}"))
    for g, reqs in GOALS.items():
        goal = Goal(name=g); db.add(goal); db.flush()
        for c, pri, why in reqs: db.add(GoalRequirement(goal_id=goal.id, category_id=cats[c], priority=pri, reason=why))
    prod = os.getenv("ENV") == "production"
    db.add(User(username="admin", email="admin@bundleai.local", password_hash=hash_fn(os.getenv("ADMIN_PASSWORD") or "admin123"), is_admin=True))
    if os.getenv("SEED_DEMO", "0" if prod else "1") == "1":
        db.add(User(username="demo", email="demo@bundleai.local", password_hash=hash_fn(os.getenv("DEMO_PASSWORD") or "demo1234")))
    db.commit()
