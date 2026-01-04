from flask import Flask, render_template, request, session, redirect, url_for, jsonify, render_template_string
import uuid
import logging
import os

from domain.models import Cart
from domain.catalog import load_catalog
from domain.coupons import load_coupons
from conversation.state import ConversationState
from conversation.graph import build_graph
from domain.pricing import calculate_totals

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static"),
)
app.secret_key = "clave_super_secreta_123"

graph = build_graph()
catalog = load_catalog()
coupons = load_coupons()

SESSION_STATES: dict[str, ConversationState] = {}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_or_create_session_id() -> str:
    sid = session.get("session_id")
    if not sid:
        sid = str(uuid.uuid4())
        session["session_id"] = sid
    return sid

def get_state() -> ConversationState:
    sid = get_or_create_session_id()
    if sid not in SESSION_STATES:
        initial_state: ConversationState = {
            "mode": "catalog",
            "cart": Cart(),
            "catalog": catalog,
            "coupons": coupons,
            "applied_coupon_code": None,
            "last_user_message": "",
            "shipping_name": None,
            "shipping_city": None,
            "bot_message": "¡Hola! Bienvenido a nuestra tienda. Soy tu asistente de compras. Preguntame por nuestro catálogo o dime que porductos quieres que añada a tu carrito.",
            "discount_summary": None,
            "chat_history": [
                ("bot", "¡Hola! Bienvenido a nuestra tienda. Soy tu asistente de compras. Preguntame por nuestro catálogo o dime que porductos quieres que añada a tu carrito."),
            ],
        }
        SESSION_STATES[sid] = initial_state
    return SESSION_STATES[sid]

@app.post("/cart/clear")
def clear_cart():
    state = get_state()
    state["cart"].clear()
    state["discount_summary"] = None
    state["applied_coupon_code"] = None

    state["bot_message"] = "El carrito ha sido vaciado. ¿Quieres que te muestre el catálogo?."
    state["chat_history"].append(("bot", state["bot_message"]))

    sid = get_or_create_session_id()
    SESSION_STATES[sid] = state
    return redirect(url_for("chat"))

@app.post("/cart/add/<int:product_id>")
def add_to_cart(product_id: int):
    state = get_state()

    # buscar producto en catálogo
    product = next((p for p in state["catalog"] if p.id == product_id), None)
    if product is None:
        state["bot_message"] = "No encuentro ese producto en el catálogo."
        state["chat_history"].append(("bot", state["bot_message"]))
        return redirect(url_for("chat"))

    # cantidad
    qty_raw = request.form.get("quantity", "1").strip()
    try:
        qty = int(qty_raw)
    except ValueError:
        qty = 1
    if qty <= 0:
        qty = 1

    # añadir
    try:
        state["cart"].add_item(product, qty)
    except ValueError as e:
        state["bot_message"] = str(e)
        state["chat_history"].append(("bot", state["bot_message"]))
        return redirect(url_for("chat"))

    # recalcular totales
    if not state["cart"].is_empty():
        state["discount_summary"] = calculate_totals(state["cart"])
    else:
        state["discount_summary"] = None

    state["bot_message"] = f"He añadido {qty} unidad(es) de <strong>{product.name}</strong> a tu carrito."
    state["chat_history"].append(("bot", state["bot_message"]))

    sid = get_or_create_session_id()
    SESSION_STATES[sid] = state
    return redirect(url_for("chat"))

@app.post("/api/cart/add/<int:product_id>")
def api_add_to_cart(product_id: int):
    state = get_state()

    # Cantidad desde el form
    try:
        quantity = int(request.form.get("quantity", "1"))
    except ValueError:
        return jsonify({"ok": False, "error": "Cantidad inválida"}), 400

    if quantity <= 0:
        return jsonify({"ok": False, "error": "La cantidad debe ser >= 1"}), 400

    # Buscar producto
    product = next((p for p in state["catalog"] if p.id == product_id), None)
    if not product:
        return jsonify({"ok": False, "error": "Producto no encontrado"}), 404

    # Añadir
    state["cart"].add_item(product, quantity)

    # Recalcular totales
    if not state["cart"].is_empty():
        state["discount_summary"] = calculate_totals(state["cart"])
    else:
        state["discount_summary"] = None

    # Persistir estado
    sid = get_or_create_session_id()
    SESSION_STATES[sid] = state

    # Badge: total de unidades en el carrito
    total_units = sum(item.quantity for item in state["cart"].items.values())

    # Renderizar HTML del carrito (partial)
    cart_html = render_template(
        "partials/cart_content.html",
        cart=state["cart"],
        discount_summary=state["discount_summary"],
    )

    return jsonify({
        "ok": True,
        "product_id": product_id,
        "added_quantity": quantity,
        "total_units": total_units,
        "line_items": len(state["cart"].items),
        "final_total": state["discount_summary"].final_total if state["discount_summary"] else 0.0,
        "cart_html": cart_html,
    })

@app.post("/api/chat")
def api_chat():
    state = get_state()

    message = (request.form.get("message") or "").strip()
    if not message:
        return jsonify({"ok": False, "error": "Mensaje vacío"}), 400

    # Añadir mensaje usuario al historial
    state["last_user_message"] = message
    state["chat_history"].append(("user", message))

    # Ejecutar grafo
    new_state = graph.invoke(state)

    # Totales
    if not new_state["cart"].is_empty():
        new_state["discount_summary"] = calculate_totals(new_state["cart"])
    else:
        new_state["discount_summary"] = None

    # Añadir mensaje bot
    bot_msg = new_state.get("bot_message") or ""
    if bot_msg:
        new_state["chat_history"].append(("bot", bot_msg))

    # Persistir
    sid = get_or_create_session_id()
    SESSION_STATES[sid] = new_state

    # Badge = total unidades
    total_units = sum(i.quantity for i in new_state["cart"].items.values())

    # Renderizar HTML del carrito (partial)
    cart_html = render_template(
        "partials/cart_content.html",
        cart=new_state["cart"],
        discount_summary=new_state["discount_summary"],
    )

    # Devolver solo los dos últimos mensajes para append (usuario + bot)
    last_messages = new_state["chat_history"][-2:] if len(new_state["chat_history"]) >= 2 else new_state["chat_history"]

    return jsonify({
        "ok": True,
        "last_messages": last_messages,
        "total_units": total_units,
        "cart_html": cart_html,
    })

@app.route("/", methods=["GET", "POST"])
def chat():
    state = get_state()

    if request.method == "POST":
        user_message = request.form.get("message", "").strip()
        logger.debug("user_message=%r", user_message)
        
        if user_message:
            state["last_user_message"] = user_message
            state["chat_history"].append(("user", user_message))

            new_state = graph.invoke(state)

            if not new_state["cart"].is_empty():
                new_state["discount_summary"] = calculate_totals(new_state["cart"])
            else:
                new_state["discount_summary"] = None
        
            if new_state.get("bot_message"):
                new_state["chat_history"].append(("bot", new_state["bot_message"]))
        
            sid = get_or_create_session_id()
            SESSION_STATES[sid] = new_state
            state = new_state
        
        else:
            state["bot_message"] = "No he recibido ningun mensaje. Escribe algún texto para continuar."
            state["chat_history"].append(("bot", state["bot_message"]))
            
    return render_template(
        "chat.html",
        chat_history=state["chat_history"],
        cart=state["cart"],
        discount_summary=state["discount_summary"],
        applied_coupon=state["cart"].applied_coupon,
        catalog=state["catalog"],
        )

if __name__ == "__main__":
    app.run(debug=True)

