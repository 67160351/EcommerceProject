"""Rule-based bundle engine. Score = GoalMatch*40% + BudgetFit*30% + Rating*20% + Popularity*10% (tunable)."""
from ..models import Product, GoalRequirement
W = dict(goal=0.4, budget=0.3, rating=0.2, pop=0.1)
ORDER = ["essential", "recommended", "optional"]

class BundleError(Exception): pass

def score(p, target):
    budget_fit = max(0.0, 1 - abs(p.price - target) / max(target, 1)) if target else 0
    return W["goal"] * 1.0 + W["budget"] * budget_fit + W["rating"] * (p.rating / 5) + W["pop"] * p.popularity

def candidates(db, category_id, exclude=()):
    return [p for p in db.query(Product).filter_by(category_id=category_id, active=True).all()
            if p.stock > 0 and p.id not in exclude]

def generate(db, goal_id, budget):
    if budget is None or budget <= 0: raise BundleError("งบประมาณต้องมากกว่า 0")
    reqs = db.query(GoalRequirement).filter_by(goal_id=goal_id).all()
    if not reqs: raise BundleError("Goal นี้ยังไม่มี Requirement กรุณาแจ้งผู้ดูแล")
    reqs.sort(key=lambda r: ORDER.index(r.priority))
    cands = {r.id: candidates(db, r.category_id) for r in reqs}
    ess = [r for r in reqs if r.priority == "essential"]
    for r in ess:
        if not cands[r.id]: raise BundleError("สินค้า Essential หมด stock: ไม่มีสินค้าให้เลือกในหมวดนี้")
    min_ess = {r.id: min(p.price for p in cands[r.id]) for r in ess}
    if sum(min_ess.values()) > budget:
        raise BundleError(f"งบต่ำเกินไป: ต้องใช้อย่างน้อย ฿{sum(min_ess.values()):,.0f} สำหรับสินค้า Essential")
    remaining, chosen, n_ess = budget, [], len(ess)
    for r in reqs:
        reserve = sum(v for k, v in min_ess.items() if k != r.id and r.priority == "essential"
                      and k not in [c[0].id for c in chosen])
        cap = remaining - reserve
        share = budget / max(len(reqs), 1)
        opts = [p for p in cands[r.id] if p.price <= cap]
        if not opts: continue
        best = max(opts, key=lambda p: score(p, min(share, cap)))
        chosen.append((r, best)); remaining -= best.price
    return [dict(product=p, role=r.priority, reason=r.reason) for r, p in chosen]

def alternatives(db, product, exclude=()):
    return sorted(candidates(db, product.category_id, exclude), key=lambda p: p.price)
