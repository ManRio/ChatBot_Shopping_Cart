from flask import Flask, render_template, request, session, redirect, url_for
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
        )

if __name__ == "__main__":
    app.run(debug=True)

