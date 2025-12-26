import pytest
from conversation.nlu import parse_user_message

@pytest.mark.parametrize(
    "msg,expected",
    [
        ("muestra el catálogo", "show_catalog"),
        ("¿qué productos tenéis?", "show_catalog"),
        ("hola", "greeting"),
        ("ayuda", "help"),
        ("qué llevo en el carrito", "show_cart"),
        ("quiero finalizar la compra", "checkout"),
        ("qué tiempo hace", "smalltalk"),
        ("salir", "exit"),
        ("terminar", "exit"),
    ]
)
def test_intents_basic(msg, expected):
    parsed = parse_user_message(msg).intent == expected

def test_add_to_cart_by_id_without_quantity_defaults_to_1():
    parsed = parse_user_message("pon el producto 402")
    assert parsed.intent == "add_to_cart"
    assert parsed.product_id == 402
    # quantity puede quedar None, y el handler lo convierte a 1
    assert parsed.quantity is None

def test_add_to_cart_with_quantity_and_id():
    parsed = parse_user_message("añade 3 del producto 402")
    assert parsed.intent == "add_to_cart"
    assert parsed.product_id == 402
    assert parsed.quantity == 3


def test_apply_coupon_extracts_code():
    parsed = parse_user_message("aplica el cupón VIP20")
    assert parsed.intent == "apply_coupon"
    assert parsed.coupon_code == "VIP20"


def test_update_quantity_simple():
    parsed = parse_user_message("cambia la camiseta azul a 3")
    assert parsed.intent == "update_quantity"
    assert parsed.quantity == 3