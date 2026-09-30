import os, hashlib, hmac, time, jwt
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from .database import Base, engine, get_db, SessionLocal
from .models import *
from .services import bundle_engine as be, cart_doctor
from .seed import seed, seed_attributes
from sqlalchemy import inspect, text

SECRET = os.getenv("SECRET_KEY", "dev-secret-change-me")
if os.getenv("ENV") == "production" and (len(SECRET) < 32 or SECRET.startswith(("dev-", "change-me")) or not os.getenv("ADMIN_PASSWORD")):
    raise RuntimeError("Production ต้องตั้ง SECRET_KEY (>=32 ตัวอักษร, ไม่ใช่ค่า default) และ ADMIN_PASSWORD")
app = FastAPI(title="BundleAI", version="1.0")

def hash_pw(pw, salt=None):
    salt = salt or os.urandom(8).hex()
    return salt + "$" + hashlib.pbkdf2_hmac("sha256", pw.encode(), salt.encode(), 100_000).hex()
def check_pw(pw, stored):
    return hmac.compare_digest(hash_pw(pw, stored.split("$")[0]), stored)

@app.on_event("startup")
def startup():
    Base.metadata.create_all(engine)
    cols = {c["name"] for c in inspect(engine).get_columns("carts")}  # lightweight migration for v1.0 databases
    with engine.begin() as conn:
        for n, t in (("goal_id", "INTEGER"), ("budget", "FLOAT")):
            if n not in cols: conn.execute(text(f"ALTER TABLE carts ADD COLUMN {n} {t}"))
    with SessionLocal() as db: seed(db, hash_pw); seed_attributes(db)

def current_user(authorization: str = Header(None), db: Session = Depends(get_db)) -> User:
    try:
        uid = jwt.decode(authorization.split()[1], SECRET, algorithms=["HS256"])["sub"]
        u = db.get(User, int(uid))
    except Exception: u = None
    if not u: raise HTTPException(401, "กรุณาเข้าสู่ระบบ")
    return u
def admin_user(u: User = Depends(current_user)):
    if not u.is_admin: raise HTTPException(403, "ต้องเป็นผู้ดูแลระบบ")
    return u

# ---------- schemas ----------
class RegisterIn(BaseModel): username: str = Field(min_length=3, max_length=30); email: str = Field(min_length=5, max_length=100); password: str = Field(min_length=6, max_length=100)
class LoginIn(BaseModel): username: str; password: str
class GenIn(BaseModel): goal_id: int; budget: float
class ReplaceIn(BaseModel): old_product_id: int; new_product_id: int
class CartAdd(BaseModel): product_id: int; quantity: int = Field(1, ge=1, le=99)
class CartQty(BaseModel): quantity: int = Field(ge=1, le=99)
class AnalyzeIn(BaseModel): goal_id: Optional[int] = None; budget: Optional[float] = None
class CheckoutIn(BaseModel): address: str = Field(min_length=5, max_length=300)
class ProductIn(BaseModel): category_id: int; name: str; price: float = Field(gt=0); stock: int = Field(ge=0); description: str = ""; active: bool = True

def prod_out(p): return dict(id=p.id, name=p.name, price=p.price, stock=p.stock, rating=p.rating, description=p.description,
                             category_id=p.category_id, category=p.category.name if p.category else None, active=p.active)

# ---------- auth ----------
def token(u): return jwt.encode({"sub": str(u.id), "exp": int(time.time()) + 86400}, SECRET, algorithm="HS256")
@app.post("/auth/register")
def register(d: RegisterIn, db: Session = Depends(get_db)):
    if db.query(User).filter((User.username == d.username) | (User.email == d.email)).first(): raise HTTPException(409, "ชื่อผู้ใช้หรืออีเมลถูกใช้แล้ว")
    u = User(username=d.username, email=d.email, password_hash=hash_pw(d.password)); db.add(u); db.commit()
    return dict(token=token(u), username=u.username, is_admin=False)
@app.post("/auth/login")
def login(d: LoginIn, db: Session = Depends(get_db)):
    u = db.query(User).filter_by(username=d.username).first()
    if not u or not check_pw(d.password, u.password_hash): raise HTTPException(401, "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
    return dict(token=token(u), username=u.username, is_admin=u.is_admin)

# ---------- catalog ----------
@app.get("/categories")
def categories(db: Session = Depends(get_db)): return [dict(id=c.id, name=c.name) for c in db.query(Category)]
@app.get("/goals")
def goals(db: Session = Depends(get_db)): return [dict(id=g.id, name=g.name) for g in db.query(Goal)]
@app.get("/products")
def products(q: str = "", category_id: Optional[int] = None, min_price: Optional[float] = None, max_price: Optional[float] = None,
             in_stock: bool = False, min_rating: Optional[float] = None, sort: str = "", db: Session = Depends(get_db)):
    qs = db.query(Product).filter_by(active=True)
    if category_id: qs = qs.filter_by(category_id=category_id)
    if q: qs = qs.filter(Product.name.ilike(f"%{q.strip()}%") | Product.description.ilike(f"%{q.strip()}%"))
    if min_price is not None: qs = qs.filter(Product.price >= min_price)
    if max_price is not None: qs = qs.filter(Product.price <= max_price)
    if in_stock: qs = qs.filter(Product.stock > 0)
    if min_rating is not None: qs = qs.filter(Product.rating >= min_rating)
    order = {"price_asc": Product.price.asc(), "price_desc": Product.price.desc(), "rating": Product.rating.desc()}.get(sort, Product.id.asc())
    return [prod_out(p) for p in qs.order_by(order)]
@app.get("/products/{pid}")
def product(pid: int, db: Session = Depends(get_db)):
    p = db.get(Product, pid)
    if not p or not p.active: raise HTTPException(404, "ไม่พบสินค้า")
    attrs = db.query(ProductAttribute).filter_by(product_id=pid).all()
    return dict(prod_out(p), attributes=[dict(key=a.key, value=a.value) for a in attrs])

# ---------- bundles ----------
def bundle_out(db, b):
    total = sum(i.product.price for i in b.items)
    b.total = total; db.commit()
    ids = [i.product_id for i in b.items]
    return dict(id=b.id, goal_id=b.goal_id, budget=b.budget, total=total, remaining=b.budget - total,
        percent_used=round(total / b.budget * 100, 1), over_budget=total > b.budget,
        items=[dict(**prod_out(i.product), role=i.role, reason=i.reason,
                    alternatives=[prod_out(a) for a in be.alternatives(db, i.product, ids)]) for i in
               sorted(b.items, key=lambda x: be.ORDER.index(x.role))])
def own_bundle(db, bid, u):
    b = db.get(Bundle, bid)
    if not b or b.user_id != u.id: raise HTTPException(404, "ไม่พบ Bundle")
    return b
@app.post("/bundles/generate")
def generate(d: GenIn, u: User = Depends(current_user), db: Session = Depends(get_db)):
    if not db.get(Goal, d.goal_id): raise HTTPException(404, "ไม่พบ Goal")
    try: picks = be.generate(db, d.goal_id, d.budget)
    except be.BundleError as e: raise HTTPException(422, str(e))
    b = Bundle(user_id=u.id, goal_id=d.goal_id, budget=d.budget)
    b.items = [BundleItem(product_id=p["product"].id, role=p["role"], reason=p["reason"]) for p in picks]
    db.add(b); db.commit()
    return bundle_out(db, b)
@app.get("/bundles/{bid}")
def get_bundle(bid: int, u: User = Depends(current_user), db: Session = Depends(get_db)): return bundle_out(db, own_bundle(db, bid, u))
@app.post("/bundles/{bid}/replace")
def replace(bid: int, d: ReplaceIn, u: User = Depends(current_user), db: Session = Depends(get_db)):
    b = own_bundle(db, bid, u)
    item = next((i for i in b.items if i.product_id == d.old_product_id), None)
    new = db.get(Product, d.new_product_id)
    if not item or not new or not new.active or new.stock < 1 or new.category_id != item.product.category_id:
        raise HTTPException(400, "เปลี่ยนสินค้าไม่ได้ (ต้องเป็นหมวดเดียวกันและมี stock)")
    item.product_id = new.id; db.commit(); db.refresh(b)
    return bundle_out(db, b)

# ---------- cart ----------
def get_cart(db, u):
    c = db.query(Cart).filter_by(user_id=u.id).first()
    if not c: c = Cart(user_id=u.id); db.add(c); db.commit()
    return c
def cart_out(c):
    return dict(goal_id=c.goal_id, goal=c.goal.name if c.goal else None, budget=c.budget,
                items=[dict(id=i.id, product=prod_out(i.product), quantity=i.quantity, subtotal=i.quantity * i.product.price) for i in c.items],
                total=sum(i.quantity * i.product.price for i in c.items))
def add_to_cart(c, p, qty):
    if not p or not p.active or p.stock < 1: raise HTTPException(400, "สินค้าไม่พร้อมขาย")
    ex = next((i for i in c.items if i.product_id == p.id), None)
    if ex: ex.quantity = min(ex.quantity + qty, p.stock)
    else: c.items.append(CartItem(product_id=p.id, quantity=min(qty, p.stock)))
@app.get("/cart")
def cart(u: User = Depends(current_user), db: Session = Depends(get_db)): return cart_out(get_cart(db, u))
@app.post("/cart/items")
def cart_add(d: CartAdd, u: User = Depends(current_user), db: Session = Depends(get_db)):
    c = get_cart(db, u); add_to_cart(c, db.get(Product, d.product_id), d.quantity); db.commit(); db.refresh(c); return cart_out(c)
@app.post("/cart/bundle/{bid}")
def cart_add_bundle(bid: int, u: User = Depends(current_user), db: Session = Depends(get_db)):
    b = own_bundle(db, bid, u); c = get_cart(db, u)
    for i in b.items: add_to_cart(c, i.product, 1)
    c.goal_id, c.budget = b.goal_id, b.budget  # persist Cart Doctor context on the backend
    db.commit(); db.refresh(c); return cart_out(c)
@app.put("/cart/items/{iid}")
def cart_qty(iid: int, d: CartQty, u: User = Depends(current_user), db: Session = Depends(get_db)):
    c = get_cart(db, u); i = next((x for x in c.items if x.id == iid), None)
    if not i: raise HTTPException(404, "ไม่พบรายการ")
    i.quantity = min(d.quantity, i.product.stock); db.commit(); db.refresh(c); return cart_out(c)
@app.delete("/cart/items/{iid}")
def cart_del(iid: int, u: User = Depends(current_user), db: Session = Depends(get_db)):
    c = get_cart(db, u); i = next((x for x in c.items if x.id == iid), None)
    if not i: raise HTTPException(404, "ไม่พบรายการ")
    c.items.remove(i); db.commit(); db.refresh(c); return cart_out(c)
@app.post("/cart/analyze")
def analyze(d: AnalyzeIn, u: User = Depends(current_user), db: Session = Depends(get_db)):
    c = get_cart(db, u)
    return cart_doctor.analyze(db, c, d.goal_id or c.goal_id, d.budget or c.budget)

# ---------- orders ----------
def order_out(o): return dict(id=o.id, total=o.total, status=o.status, address=o.address, created_at=str(o.created_at),
    items=[dict(name=i.product.name, quantity=i.quantity, price=i.price) for i in o.items])
@app.post("/orders")
def checkout(d: CheckoutIn, u: User = Depends(current_user), db: Session = Depends(get_db)):
    c = get_cart(db, u)
    if not c.items: raise HTTPException(400, "ตะกร้าว่าง")
    for i in c.items:  # validate on backend, never trust frontend
        if not i.product.active or i.product.stock < i.quantity:
            raise HTTPException(409, f"{i.product.name} ไม่พร้อมขายตามจำนวน กรุณาแก้ตะกร้า")
    o = Order(user_id=u.id, address=d.address, total=sum(i.quantity * i.product.price for i in c.items))
    for i in c.items:
        o.items.append(OrderItem(product_id=i.product_id, quantity=i.quantity, price=i.product.price)); i.product.stock -= i.quantity
    db.add(o); c.items.clear(); c.goal_id = c.budget = None; db.commit()
    return order_out(o)
@app.get("/orders")
def orders(u: User = Depends(current_user), db: Session = Depends(get_db)):
    return [order_out(o) for o in db.query(Order).filter_by(user_id=u.id).order_by(Order.id.desc())]
@app.get("/orders/{oid}")
def order(oid: int, u: User = Depends(current_user), db: Session = Depends(get_db)):
    o = db.get(Order, oid)
    if not o or o.user_id != u.id: raise HTTPException(404, "ไม่พบ Order")
    return order_out(o)

# ---------- admin ----------
@app.post("/admin/products")
def admin_add(d: ProductIn, _=Depends(admin_user), db: Session = Depends(get_db)):
    p = Product(**d.model_dump()); db.add(p); db.commit(); return prod_out(p)
@app.put("/admin/products/{pid}")
def admin_edit(pid: int, d: ProductIn, _=Depends(admin_user), db: Session = Depends(get_db)):
    p = db.get(Product, pid)
    if not p: raise HTTPException(404, "ไม่พบสินค้า")
    for k, v in d.model_dump().items(): setattr(p, k, v)
    db.commit(); return prod_out(p)
@app.get("/admin/orders")
def admin_orders(_=Depends(admin_user), db: Session = Depends(get_db)): return [dict(order_out(o), user_id=o.user_id) for o in db.query(Order).order_by(Order.id.desc())]

FRONT = os.getenv("FRONTEND_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
if os.path.isdir(FRONT): app.mount("/", StaticFiles(directory=FRONT, html=True), name="frontend")
