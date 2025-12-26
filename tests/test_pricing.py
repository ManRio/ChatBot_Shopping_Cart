from domain.models import Cart, Product, Coupon
from domain.pricing import calculate_totals

def test_quantity_discount_applies_and_cart_discount_applies_over_100():
    cart = Cart()
    p = Product(id=1, name="Producto A", price=100.0)
    cart.add_item(p, 3)  # 300

    summary = calculate_totals(cart)

    assert summary.subtotal == 300.0
    assert summary.line_discounts == 25.0  # 25% de 100 por cada bloque de 3
    # after_line = 275 -> descuento 10% por total
    assert summary.cart_discount == 27.5
    assert summary.coupon_discount == 0.0
    assert summary.final_total == 247.5


def test_coupon_respects_min_total():
    cart = Cart()
    p = Product(id=2, name="Producto B", price=20.0)
    cart.add_item(p, 2)  # 40

    cart.applied_coupon = Coupon(code="VIP20", type="percent", value=20, min_total=100)
    summary = calculate_totals(cart)

    assert summary.coupon_discount == 0.0


def test_fixed_coupon_cannot_exceed_total():
    cart = Cart()
    p = Product(id=3, name="Producto C", price=10.0)
    cart.add_item(p, 1)  # 10

    cart.applied_coupon = Coupon(code="SUPER5", type="fixed", value=50, min_total=0)
    summary = calculate_totals(cart)

    # cupón fijo se limita al total after_cart
    assert summary.coupon_discount == 10.0
    assert summary.final_total == 0.0