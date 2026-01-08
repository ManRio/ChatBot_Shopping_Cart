from typing import Literal, TypedDict, Optional
from domain.models import Cart, Product, Coupon, DiscountSummary

ConversationMode = Literal["catalog", "cart_edit", "confirmation", "shipping", "end"]

class ConversationState(TypedDict, total=False):
    mode: ConversationMode
    cart: Cart
    catalog: list[Product]
    coupons: list[Coupon]
    applied_coupon_code: Optional[str]
    last_user_message: str
    shipping_name: Optional[str]
    shipping_city: Optional[str]
    bot_message: str
    discount_summary: Optional[DiscountSummary]
    chat_history: list[tuple[str, str]]

    last_order_name: Optional[str]
    last_order_city: Optional[str]
    last_order_total: Optional[float]
    order_confirmed: bool