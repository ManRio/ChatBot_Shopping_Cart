import pytest
from domain.models import Cart, Product

@pytest.fixture
def camiseta_azul():
    return Product(id=101, name="Camiseta Azul", price=15.99, category="Ropa", description="Camiseta básica de algodón azul unisex.")


@pytest.fixture
def gorra_negra():
    return Product(id=402, name="Gorra Negra", price=9.99, category="Accesorios", description="Gorra negra ajustable.")


def test_add_item_accumulates_quantity(camiseta_azul):
    cart = Cart()
    cart.add_item(camiseta_azul, 2)
    cart.add_item(camiseta_azul, 3)

    assert 101 in cart.items
    assert cart.items[101].quantity == 5


def test_remove_item(gorra_negra):
    cart = Cart()
    cart.add_item(gorra_negra, 1)

    cart.remove_item(gorra_negra.id)
    assert cart.is_empty()


def test_set_quantity_updates_and_removes(camiseta_azul):
    cart = Cart()
    cart.add_item(camiseta_azul, 2)

    cart.set_quantity(camiseta_azul.id, 5)
    assert cart.items[camiseta_azul.id].quantity == 5

    cart.set_quantity(camiseta_azul.id, 0)
    assert camiseta_azul.id not in cart.items
    assert cart.is_empty()


def test_add_item_invalid_quantity(camiseta_azul):
    cart = Cart()
    with pytest.raises(ValueError):
        cart.add_item(camiseta_azul, 0)
    with pytest.raises(ValueError):
        cart.add_item(camiseta_azul, -3)


def test_clear_empties_cart_and_removes_coupon(camiseta_azul):
    cart = Cart()
    cart.add_item(camiseta_azul, 1)
    cart.applied_coupon = None  # o un cupón fake si quieres

    cart.clear()
    assert cart.is_empty()
    assert cart.applied_coupon is None