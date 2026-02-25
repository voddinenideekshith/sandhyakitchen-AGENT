from core.config import settings
print("OPENAI KEY EXISTS:", bool(settings.OPENAI_API_KEY))
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.schemas import OrderCreate
from models.brand import Brand
from models.menu_item import MenuItem
from models.order import Order, OrderItem


async def create_order(db: AsyncSession, order_in: OrderCreate):
    # validate brand exists
    q = select(Brand).where(Brand.slug == order_in.brand_slug)
    res = await db.execute(q)
    brand = res.scalars().first()
    if not brand:
        raise ValueError("Brand not found")

    # validate menu items and compute total
    total = 0.0
    menu_map = {}
    for ci in order_in.items:
        qmi = select(MenuItem).where(MenuItem.id == ci.menu_item_id, MenuItem.brand_id == brand.id)
        rmi = await db.execute(qmi)
        mi = rmi.scalars().first()
        if not mi:
            raise ValueError(f"Menu item {ci.menu_item_id} not found for brand")
        menu_map[ci.menu_item_id] = mi
        total += float(mi.price) * ci.quantity

    # create order and items in transaction
    new_order = Order(brand_id=brand.id, total=round(total, 2), status="pending")
    db.add(new_order)
    await db.flush()

    for ci in order_in.items:
        mi = menu_map[ci.menu_item_id]
        oi = OrderItem(order_id=new_order.id, menu_item_id=mi.id, quantity=ci.quantity, price=mi.price)
        db.add(oi)

    await db.commit()
    await db.refresh(new_order)
    return {"id": new_order.id, "total": float(new_order.total)}
