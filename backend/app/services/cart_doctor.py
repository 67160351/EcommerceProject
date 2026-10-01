from ..models import GoalRequirement, Product

def analyze(db, cart, goal_id=None, budget=None):
    issues, items = [], cart.items
    total = sum(i.product.price * i.quantity for i in items)
    for i in items:
        if i.quantity > 1:
            saving = i.product.price * (i.quantity - 1)
            issues.append(dict(type="duplicate", severity="warn",
                message=f"พบสินค้าซ้ำ: {i.product.name} จำนวน {i.quantity} ชิ้น หากลดเหลือ 1 ชิ้น จะประหยัด ฿{saving:,.0f}",
                action=dict(kind="set_quantity", item_id=i.id, quantity=1), saving=saving))
    reqs = db.query(GoalRequirement).filter_by(goal_id=goal_id).all() if goal_id else []
    req_cats = {r.category_id: r for r in reqs}
    by_cat = {}
    for i in items: by_cat.setdefault(i.product.category_id, []).append(i)
    for cid, lst in by_cat.items():
        if len(lst) > 1 and (not reqs or cid in req_cats):
            keep = min(lst, key=lambda x: x.product.price); drop = [x for x in lst if x is not keep]
            saving = sum(x.product.price * x.quantity for x in drop)
            issues.append(dict(type="overlap", severity="warn",
                message=f"สินค้ามีหน้าที่ใกล้เคียงกัน ({lst[0].product.category.name}): {', '.join(x.product.name for x in lst)} เลือกเพียง 1 รายการ (เก็บ {keep.product.name} ประหยัด ฿{saving:,.0f})",
                action=dict(kind="remove_items", item_ids=[x.id for x in drop]), saving=saving))
    if reqs:
        for r in reqs:
            if r.priority == "essential" and r.category_id not in by_cat:
                opts = [p for p in db.query(Product).filter_by(category_id=r.category_id, active=True).all() if p.stock > 0]
                if opts:
                    p = min(opts, key=lambda x: x.price)
                    issues.append(dict(type="missing_essential", severity="error",
                        message=f"ขาดสินค้า Essential: แนะนำ {p.name} (฿{p.price:,.0f})",
                        action=dict(kind="add_product", product_id=p.id), saving=-p.price))
        rel = [i for i in items if i.product.category_id not in req_cats]
        for i in rel:
            issues.append(dict(type="low_utilization", severity="info",
                message=f"{i.product.name} ไม่เกี่ยวข้องกับ Goal นี้โดยตรง อาจไม่จำเป็น (ประหยัด ฿{i.product.price*i.quantity:,.0f})",
                action=dict(kind="remove_items", item_ids=[i.id]), saving=i.product.price * i.quantity))
    if budget and total > budget:
        issues.append(dict(type="over_budget", severity="error",
            message=f"ยอดรวม ฿{total:,.0f} เกินงบ ฿{budget:,.0f} อยู่ ฿{total-budget:,.0f}", action=None, saving=total - budget))
    return dict(total=total, budget=budget, remaining=(budget - total) if budget else None, issues=issues)
