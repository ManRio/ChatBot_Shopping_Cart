from dataclasses import dataclass, field
from typing import Dict, Optional

@dataclass
class Product:
    id: int
    name: str
    price: float
    category: Optional[str] = None
    description: Optional[str] = None

@dataclass
class CartItem:
    product: Product
    quantity: int

@dataclass
class Coupon:
    code: str
    type: str # ej, 'percent' or 'fixed'
    value: float
    min_total: float=0.0

@dataclass
class Cart:
    items: Dict[int, CartItem] = field(default_factory=dict)
    applied_coupon: Optional[Coupon] = None

    def add_item(self, product: Product, quantity: int) -> None:
        if quantity <= 0:
            raise ValueError("La cantidad de artículos debe ser superior a cero.")
        if product.id in self.items:
            self.items[product.id].quantity += quantity
        else:
            self.items[product.id] = CartItem(product=product, quantity=quantity)
    
    def set_quantity(self, product_id: int, quantity: int) -> None:
        if quantity <= 0:
            self.items.pop(product_id, None)
            return
        if product_id not in self.items:
            raise KeyError("Este producto no está añadido al carrito.")
        self.items[product_id].quantity = quantity
    
    def remove_item(self, product_id: int) -> None:
        self.items.pop(product_id, None)

    def clear(self) -> None:
        self.items.clear()
        self.applied_coupon = None
    
    def is_empty(self) -> bool:
        return len(self.items) == 0
    
@dataclass
class DiscountSummary:
    subtotal: float
    line_discounts: float
    cart_discount: float
    coupon_discount: float
    final_total: float

