from domain.models import Cart, Product, Coupon
from conversation.graph import build_graph

def make_state(catalog=None, coupons=None):
    if catalog is None:
        catalog = [
            Product(id=101, name="Camiseta azul", price=15.99),
            Product(id=402, name="Gorra negra", price=9.99),
        ]
    if coupons is None:
        coupons = [
            Coupon(code="VIP20", type="percent", value=20.0, min_total=0.0),
            Coupon(code="SUPER5", type="fixed", value=5, min_total=0),
        ]

    return {
        "mode": "catalog",
        "cart": Cart(),
        "catalog": catalog,
        "coupons": coupons,
        "applied_coupon_code": None,
        "last_user_message": "",
        "shipping_name": None,
        "shipping_city": None,
        "bot_message": "",
        "discount_summary": None,
        "chat_history": [],
    }

def test_graph_show_catalog_sets_mode_and_message():
    graph = build_graph()
    state = make_state()
    state["last_user_message"] = "muestra el catálogo"

    new_state = graph.invoke(state)

    assert new_state["mode"] == "catalog"
    assert "table" in new_state["bot_message"].lower()

def test_graph_add_to_cart_by_id_adds_one_unit():
    graph = build_graph()
    state = make_state()
    state["last_user_message"] = "pon el producto 402"

    new_state = graph.invoke(state)

    assert 402 in new_state["cart"].items
    assert new_state["cart"].items[402].quantity == 1
    assert new_state["mode"] == "cart_edit"

def test_graph_checkout_moves_to_shipping_when_cart_not_empty():
    graph = build_graph()
    state = make_state()
    state["cart"].add_item(state["catalog"][0], 1)

    state["last_user_message"] = "quiero finalizar la compra"
    new_state = graph.invoke(state)

    assert new_state["mode"] == "shipping"
    assert "finalizar" in new_state["bot_message"].lower() or "total" in new_state["bot_message"].lower()

def test_graph_exit_clears_cart_and_resets_state():
    graph = build_graph()
    state = make_state()
    state["cart"].add_item(state["catalog"][0], 2)

    state["last_user_message"] = "salir"
    new_state = graph.invoke(state)

    assert new_state["cart"].is_empty()
    assert new_state["mode"] == "catalog"