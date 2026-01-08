from domain.models import Cart, Product, Coupon
from conversation.graph import build_graph

def make_state():
    catalog = [
        Product(id=101, name="Camiseta azul", price=15.99),
        Product(id=402, name="Gorra negra", price=9.99),
    ]
    coupons = [
        Coupon(code="VIP20", type="percent", value=20.0, min_total=0.0),
        Coupon(code="SUPER5", type="fixed", value=5, min_total=0.0),
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
        "order_confirmed": False,
        "last_order_name": None,
        "last_order_city": None,
        "last_order_total": None,
    }

def test_graph_add_to_cart_by_id_adds_one_unit():
    graph = build_graph()
    state = make_state()
    state["last_user_message"] = "pon el producto 402"

    new_state = graph.invoke(state)

    assert 402 in new_state["cart"].items
    assert new_state["cart"].items[402].quantity == 1
    assert new_state["mode"] == "cart_edit"

def test_checkout_moves_to_shipping_when_cart_not_empty():
    graph = build_graph()
    state = make_state()
    state["cart"].add_item(state["catalog"][0], 1)

    state["last_user_message"] = "quiero finalizar la compra"
    new_state = graph.invoke(state)

    assert new_state["mode"] == "shipping"
    assert new_state["shipping_name"] is None
    assert new_state["shipping_city"] is None
    assert "finalizar" in new_state["bot_message"].lower() or "total" in new_state["bot_message"].lower()

def test_shipping_accepts_name_and_city_in_one_sentence_and_goes_confirmation():
    graph = build_graph()
    state = make_state()
    state["cart"].add_item(state["catalog"][0], 1)

    state["last_user_message"] = "finalizar compra"
    state = graph.invoke(state)
    assert state["mode"] == "shipping"

    state["last_user_message"] = "Soy Manuel de Sevilla"
    state = graph.invoke(state)

    assert state["mode"] == "confirmation"
    assert state["shipping_name"] == "Manuel"
    assert state["shipping_city"] == "Sevilla"

def test_confirmation_registers_order_once_and_clears_cart():
    graph = build_graph()
    state = make_state()
    state["cart"].add_item(state["catalog"][0], 2)

    # Ir a shipping
    state["last_user_message"] = "finalizar compra"
    state = graph.invoke(state)
    assert state["mode"] == "shipping"

    # Completar shipping
    state["last_user_message"] = "Soy Ana de Madrid"
    state = graph.invoke(state)
    assert state["mode"] == "confirmation"

    # En confirmation se debe vaciar carrito y marcar order_confirmed
    state = graph.invoke(state)  

    assert state.get("order_confirmed") is True
    assert state["cart"].is_empty()
    assert "pedido" in state["bot_message"].lower()

def test_exit_clears_cart_and_resets_shipping():
    graph = build_graph()
    state = make_state()
    state["cart"].add_item(state["catalog"][0], 2)
    state["shipping_name"] = "X"
    state["shipping_city"] = "Y"

    state["last_user_message"] = "salir"
    new_state = graph.invoke(state)

    assert new_state["cart"].is_empty()
    assert new_state["shipping_name"] is None
    assert new_state["shipping_city"] is None
    assert new_state["mode"] == "catalog"