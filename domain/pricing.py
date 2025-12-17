from math import floor
from .models import Cart, DiscountSummary, Coupon

def calculate_line_discount(cart: Cart) -> float:
    """
    Descuento por cantidades:
    - Por cada grupo de 3 uds del mismo producto,
    La tercera tiene un 25% de descuento.
    """
    total_discount = 0.0
    for item in cart.items.values():
        qty = item.quantity
        price = item.product.price
        group_of_three = floor(qty / 3)
        total_discount += group_of_three * price * 0.25
    return total_discount

def calculate_cart_discount(subtotal_after_line_discount: float) -> float:
    """
    Si el subtotal tras los descuentos por cantidad supera los 100€,
    se aplica un 10% de descuento adicional.
    """
    if subtotal_after_line_discount > 100:
        return subtotal_after_line_discount * 0.10
    return 0.0

def calculate_coupon_discount(total_after_cart_discount: float, coupon:  Coupon | None) -> float:
    """
    Se aplica el cupón de descuento si existe y cumple los requisitos.
    """
    if coupon is None:
        return 0.0
    if total_after_cart_discount < coupon.min_total:
        return 0.0
    if coupon.type == 'percent':
        return total_after_cart_discount * (coupon.value / 100)
    if coupon.type == 'fixed':
        return min(coupon.value, total_after_cart_discount)
    return 0.0

def calculate_totals(cart: Cart) -> DiscountSummary:
    # Subtotal sin descuentos
    base_total = sum(item.product.price * item.quantity for item in cart.items.values())

    # Descuentos por cantidades
    line_discount = calculate_line_discount(cart)
    after_line = base_total - line_discount

    # Descuento por total del carrito
    cart_discount = calculate_cart_discount(after_line)
    after_cart = after_line - cart_discount

    # Descuento por cupón
    coupon_discount = calculate_coupon_discount(after_cart, cart.applied_coupon)

    # Total final (No puede ser negativo)
    final_total = max(after_cart - coupon_discount, 0.0)

    return DiscountSummary(
        subtotal=base_total,
        line_discounts=line_discount,
        cart_discount=cart_discount,
        coupon_discount=coupon_discount,
        final_total=final_total,
    )