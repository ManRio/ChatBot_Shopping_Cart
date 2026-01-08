from langgraph.graph import StateGraph, END
from .state import ConversationState
from .nlu import parse_user_message
from domain.catalog import find_product_by_id, find_product_by_name
from domain.coupons import find_coupon_by_code
from domain.pricing import calculate_totals

import re


def router_node(state: ConversationState) -> ConversationState:
    # Nodo de entrada, no modifica el estado.
    return state


def handle_catalog(state: ConversationState) -> ConversationState:
    """
    Muestra el catálogo en forma de tabla HTML.
    """
    rows = []
    for p in state["catalog"]:
        rows.append(
            "<tr>"
            f"<td>{p.id}</td>"
            f"<td>{p.name}</td>"
            f"<td>{p.price:.2f} €</td>"
            "</tr>"
        )

    html = (
        "<p>Estos son algunos de nuestros productos, ¿deseas añadir alguno?</p>"
        "<table class='catalog-table'>"
        "<thead><tr><th>ID producto</th><th>Nombre</th><th>Precio</th></tr></thead>"
        "<tbody>"
        + "".join(rows)
        + "</tbody></table>"
    )

    state["bot_message"] = html
    state["mode"] = "catalog"
    return state


def _resolve_product_from_intent(state: ConversationState, intent) -> tuple[object | None, str]:
    """
    Utilidad interna para no repetir lógica: dados el estado y un ParsedIntent,
    intenta resolver el producto (por id o por nombre aproximado).
    Devuelve (product, error_message).
    """
    catalog = state["catalog"]
    product = None

    if intent.product_id:
        product = find_product_by_id(catalog, intent.product_id)

    if product is None and intent.product_name:
        product = find_product_by_name(catalog, intent.product_name)

    if product is None:
        return None, (
            "No encuentro ese producto. Puedes usar el id (por ejemplo 101) "
            "o pedirme que te muestre el catálogo."
        )

    return product, ""


def handle_add_to_cart(state: ConversationState) -> ConversationState:
    intent = parse_user_message(state["last_user_message"])
    product, error = _resolve_product_from_intent(state, intent)

    if product is None:
        state["bot_message"] = f"<p>{error}</p>"
        return state

    quantity = intent.quantity or 1
    if quantity <= 0:
        state["bot_message"] = (
            "<p>No puedo añadir cantidades negativas o iguales a cero; "
            "la cantidad debe ser al menos 1.</p>"
        )
        return state

    try:
        state["cart"].add_item(product, quantity)
    except ValueError as e:
        state["bot_message"] = f"<p>{e}</p>"
        return state

    state["mode"] = "cart_edit"
    state["bot_message"] = (
        f"<p>He añadido <strong>{quantity}</strong> unidad(es) de "
        f"<strong>{product.name}</strong> a tu carrito.</p>"
    )
    return state


def handle_remove_from_cart(state: ConversationState) -> ConversationState:
    intent = parse_user_message(state["last_user_message"])
    product, error = _resolve_product_from_intent(state, intent)

    if product is None:
        state["bot_message"] = (
            "<p>No entiendo qué producto quieres eliminar del carrito. "
            "Dímelo por su nombre o su id.</p>"
        )
        return state

    if product.id not in state["cart"].items:
        state["bot_message"] = (
            f"<p><strong>{product.name}</strong> no está en tu carrito. "
            "Puedes pedirme que te muestre el carrito para revisarlo.</p>"
        )
        return state

    state["cart"].remove_item(product.id)
    state["mode"] = "cart_edit"
    state["bot_message"] = (
        f"<p>He eliminado <strong>{product.name}</strong> de tu carrito.</p>"
    )
    return state


def handle_update_quantity(state: ConversationState) -> ConversationState:
    """
    Actualiza la cantidad de un producto en el carrito.
    Soporta frases tipo:
    - 'cambia la camiseta azul a 3'
    - 'pon 3 en la camiseta azul'
    - 'pon 3 en lugar de 1'
    """
    intent = parse_user_message(state["last_user_message"])

    if intent.quantity is None:
        state["bot_message"] = (
            "<p>No he entendido la cantidad nueva. Dime, por ejemplo: "
            "<em>'pon 3 camisetas azules'</em> o <em>'cambia la camiseta azul a 2'</em>.</p>"
        )
        return state

    product, error = _resolve_product_from_intent(state, intent)
    if product is None:
        state["bot_message"] = (
            f"<p>{error or 'No he podido identificar el producto cuya cantidad quieres cambiar.'}</p>"
        )
        return state

    if product.id not in state["cart"].items:
        state["bot_message"] = (
            f"<p><strong>{product.name}</strong> no está en tu carrito. "
            "Primero añádelo y luego podré cambiar la cantidad.</p>"
        )
        return state

    # Si la cantidad nueva es <= 0, interpretamos que se quiere eliminar
    if intent.quantity <= 0:
        state["cart"].remove_item(product.id)
        state["mode"] = "cart_edit"
        state["bot_message"] = (
            f"<p>He eliminado <strong>{product.name}</strong> del carrito "
            f"porque la cantidad nueva es {intent.quantity}.</p>"
        )
        return state

    try:
        state["cart"].set_quantity(product.id, intent.quantity)
    except (KeyError, ValueError) as e:
        state["bot_message"] = f"<p>{e}</p>"
        return state

    state["mode"] = "cart_edit"
    state["bot_message"] = (
        f"<p>He actualizado la cantidad de <strong>{product.name}</strong> "
        f"a <strong>{intent.quantity}</strong> unidad(es).</p>"
    )
    return state


def handle_show_cart(state: ConversationState) -> ConversationState:
    """
    Muestra el carrito como tabla HTML con totales y descuentos.
    """
    cart = state["cart"]
    if cart.is_empty():
        state["bot_message"] = (
            "<p>Tu carrito está vacío. "
            "Si quieres, puedo <strong>mostrarte el catálogo</strong> para que añadas productos.</p>"
        )
        return state

    summary = calculate_totals(cart)
    state["discount_summary"] = summary

    rows = []
    for item in cart.items.values():
        line_total = item.product.price * item.quantity
        rows.append(
            "<tr>"
            f"<td>{item.product.name}</td>"
            f"<td>{item.quantity}</td>"
            f"<td>{item.product.price:.2f} €</td>"
            f"<td>{line_total:.2f} €</td>"
            "</tr>"
        )

    html = (
        "<p>Hasta ahora esto es lo que llevas añadido al carrito:</p>"
        "<table class='cart-table'>"
        "<thead>"
        "<tr><th>Producto</th><th>Cantidad</th><th>Precio unidad</th><th>Subtotal</th></tr>"
        "</thead>"
        "<tbody>"
        + "".join(rows)
        + "</tbody></table>"
        "<div class='cart-totals'>"
        f"<p><strong>Descuento por cantidades:</strong> -{summary.line_discounts:.2f} €</p>"
        f"<p><strong>Descuento por total:</strong> -{summary.cart_discount:.2f} €</p>"
    )

    if cart.applied_coupon:
        html += (
            f"<p><strong>Cupón aplicado ({cart.applied_coupon.code}):</strong> "
            f"-{summary.coupon_discount:.2f} €</p>"
        )

    html += f"<p><strong>Total final:</strong> {summary.final_total:.2f} €</p></div>"

    state["bot_message"] = html
    state["mode"] = "cart_edit"
    return state


def handle_checkout(state: ConversationState) -> ConversationState:
    cart = state["cart"]
    if cart.is_empty():
        state["bot_message"] = (
            "<p>Tu carrito está vacío. Añade algún producto antes de finalizar.</p>"
        )
        state["mode"] = "catalog"
        return state

    summary = calculate_totals(cart)
    state["discount_summary"] = summary

    state["bot_message"] = (
        f"<p>Vamos a finalizar tu compra. El total es "
        f"<strong>{summary.final_total:.2f} €</strong>.</p>"
        "<p>Puedes decirme tu <strong>nombre y ciudad de envío en una sola frase</strong>, "
        "por ejemplo: <em>'Soy Ana de Madrid'</em>, "
        "o bien decírmelo <strong>por partes</strong> empezando por tu nombre.</p>"
    )
    state["mode"] = "shipping"
    state["shipping_name"] = None
    state["shipping_city"] = None
    return state

def _is_valid_human_field(value: str) -> bool:
    v = (value or "").strip()
    return len(v) >= 2 and not v.isdigit()
    # Comprobamos que tenga al menos 2 caracteres y no sea solo dígitos.

def _try_parse_name_city(text: str) -> tuple[str | None, str | None]:
    """
    Extrae (nombre, ciudad) de frases tipo:
      - "Soy Manuel de Sevilla"
      - "Me llamo Manuel de Sevilla"
      - "Soy Manuel y vivo en Sevilla"
      - "Manuel de Sevilla" (fallback)
    """
    t = text.strip()

    patterns = [
        r"^(?:soy|me llamo)\s+(.+?)\s*(?:,)?\s+de\s+(.+)$",
        r"^(?:soy|me llamo)\s+(.+?)\s+y\s+vivo\s+en\s+(.+)$",
        r"^(.+?)\s+de\s+(.+)$",
    ]

    for pat in patterns:
        m = re.search(pat, t, re.IGNORECASE)
        if m:
            name = m.group(1).strip()
            city = m.group(2).strip()
            return name, city

    return None, None


def handle_shipping(state: ConversationState) -> ConversationState:
    text = state["last_user_message"].strip()

    # 1) Intento: el usuario da nombre+ciudad en una sola frase
    #    Solo tiene sentido si aún falta alguno de los dos datos.
    if state["shipping_name"] is None or state["shipping_city"] is None:
        name, city = _try_parse_name_city(text)
        if name and city and _is_valid_human_field(name) and _is_valid_human_field(city):
            state["shipping_name"] = name
            state["shipping_city"] = city
            state["mode"] = "confirmation"
            return state

    # 2) Si no se pudo parsear, vamos por partes (nombre -> ciudad)
    if state["shipping_name"] is None:
        if not _is_valid_human_field(text):
            state["bot_message"] = (
                "Necesito un nombre válido (por ejemplo: <strong>Ana</strong>). ¿Cuál es tu nombre?"
            )
            return state

        # Evitar guardar "soy X de Y" como nombre si el parser falló por algún motivo
        cleaned = re.sub(r"^(?:soy|me llamo)\s+", "", text, flags=re.IGNORECASE).strip()
        if " de " in cleaned.lower():
            state["bot_message"] = (
                "Puedo recogerlo en una sola frase (por ejemplo: <em>“Soy Ana de Madrid”</em>) "
                "o por partes. Para hacerlo por partes, dime solo tu <strong>nombre</strong>."
            )
            return state

        state["shipping_name"] = cleaned
        state["bot_message"] = "Perfecto. ¿En qué <strong>ciudad</strong> vives?"
        return state

    if state["shipping_city"] is None:
        if not _is_valid_human_field(text):
            state["bot_message"] = (
                "Necesito una ciudad válida (por ejemplo: <strong>Madrid</strong>). ¿En qué ciudad vives?"
            )
            return state

        state["shipping_city"] = text
        state["mode"] = "confirmation"
        return state

    return state


def handle_apply_coupon(state: ConversationState) -> ConversationState:
    intent = parse_user_message(state["last_user_message"])
    if not intent.coupon_code:
        state["bot_message"] = (
            "<p>Indícame el <strong>código</strong> del cupón (por ejemplo: <code>VIP20</code>).</p>"
        )
        return state

    coupon = find_coupon_by_code(state["coupons"], intent.coupon_code)
    if coupon is None:
        state["bot_message"] = (
            "<p>Ese cupón no es válido. Si quieres, puedo mostrarte el catálogo o tu carrito.</p>"
        )
        return state

    # Subtotal actual para feedback
    summary = calculate_totals(state["cart"])
    current_total = summary.final_total

    if current_total < coupon.min_total:
        state["bot_message"] = (
            f"<p>El cupón <strong>{coupon.code}</strong> requiere un mínimo de "
            f"<strong>{coupon.min_total:.2f}€</strong>. Ahora tu total es "
            f"<strong>{current_total:.2f}€</strong>.</p>"
        )
        return state

    previous = state["cart"].applied_coupon.code if state["cart"].applied_coupon else None
    state["cart"].applied_coupon = coupon
    state["applied_coupon_code"] = coupon.code

    if previous and previous.upper() != coupon.code.upper():
        state["bot_message"] = (
            f"<p>He aplicado el cupón <strong>{coupon.code}</strong> y he sustituido "
            f"el cupón anterior (<strong>{previous}</strong>).</p>"
        )
    else:
        state["bot_message"] = f"<p>He aplicado el cupón <strong>{coupon.code}</strong> a tu carrito.</p>"

    state["mode"] = "cart_edit"
    return state


def handle_smalltalk(state: ConversationState) -> ConversationState:
    state["bot_message"] = (
        "<p>Soy un asistente de tienda online. No sé el tiempo que hace, "
        "pero sí puedo ayudarte con tu compra.</p>"
        "<p>Puedo mostrarte el catálogo, añadir o quitar productos, aplicar cupones "
        "y ayudarte a finalizar el pedido.</p>"
    )
    return state


def handle_greeting(state: ConversationState) -> ConversationState:
    state["bot_message"] = (
        "<p>¡Hola! Soy tu asistente de compras.</p>"
        "<p>Puedo mostrarte el catálogo, añadir artículos al carrito, aplicar cupones "
        "y ayudarte a finalizar la compra.</p>"
        "<p>Por ejemplo, puedes decirme <em>'muestra el catálogo'</em> o "
        "<em>'añade 2 camisetas azules'</em>.</p>"
    )
    return state


def handle_help(state: ConversationState) -> ConversationState:
    state["bot_message"] = (
        "<p>Puedo ayudarte con estas cosas:</p>"
        "<ul>"
        "<li><strong>Ver catálogo:</strong> "
        "<em>'muestra el catálogo'</em>, <em>'qué productos tenéis'</em></li>"
        "<li><strong>Añadir producto:</strong> "
        "<em>'añade 2 camisetas azules'</em>, <em>'pon 1 producto 101'</em></li>"
        "<li><strong>Quitar producto:</strong> "
        "<em>'quita la camiseta azul'</em>, <em>'elimina producto 101'</em></li>"
        "<li><strong>Ver carrito:</strong> "
        "<em>'qué llevo en el carrito'</em>, <em>'mostrar carrito'</em></li>"
        "<li><strong>Cambiar cantidades:</strong> "
        "<em>'cambia la camiseta azul a 3'</em>, <em>'pon 2 en lugar de 1'</em></li>"
        "<li><strong>Aplicar cupón:</strong> "
        "<em>'aplica el cupón BIENVENIDA10'</em></li>"
        "<li><strong>Finalizar compra:</strong> "
        "<em>'quiero finalizar la compra'</em></li>"
        "<li><strong>Salir:</strong> <em>'salir'</em>, <em>'terminar'</em></li>"
        "</ul>"
    )
    return state


def handle_unknown(state: ConversationState) -> ConversationState:
    state["bot_message"] = (
        "<p>No he entendido bien tu petición.</p>"
        "<p>Puedes pedirme que te muestre el catálogo, que añada o quite productos, "
        "que cambie cantidades en tu carrito o que te muestre el total.</p>"
        "<p>Si necesitas más detalles, puedes escribir <strong>'ayuda'</strong>.</p>"
    )
    return state

def handle_confirmation(state: ConversationState) -> ConversationState:
    """
    - Al entrar por primera vez, “cierra” el pedido:
      guarda resumen del último pedido, vacía carrito y deja mensaje final.
    - En siguientes mensajes, no vuelve a cerrar nada; solo guía al usuario.
    """
    # Si aún no se ha “confirmado” formalmente el pedido, lo hacemos ahora
    if not state.get("order_confirmed", False):
        # Capturar totales antes de vaciar
        summary = calculate_totals(state["cart"]) if not state["cart"].is_empty() else None
        total = summary.final_total if summary else 0.0

        name = state.get("shipping_name") or "cliente"
        city = state.get("shipping_city") or "tu ciudad"

        state["last_order_name"] = name
        state["last_order_city"] = city
        state["last_order_total"] = total
        state["order_confirmed"] = True

        # Vaciar carrito + cupón (pedido ya “registrado”)
        state["cart"].clear()
        state["applied_coupon_code"] = None
        state["discount_summary"] = None

        state["bot_message"] = (
            "<p><strong>Pedido registrado correctamente.</strong></p>"
            f"<p>Envío a nombre de <strong>{name}</strong> en <strong>{city}</strong>.</p>"
            f"<p>Total pagado: <strong>{total:.2f} €</strong>.</p>"
            "<p>Puedes seguir comprando (pídeme el <strong>catálogo</strong>) o escribir <strong>'salir'</strong> para terminar.</p>"
        )
        state["mode"] = "confirmation"
        return state

    # Si ya estaba confirmado, no rehacemos nada:
    name = state.get("last_order_name") or "cliente"
    city = state.get("last_order_city") or "tu ciudad"
    total = state.get("last_order_total")

    total_txt = f"<p>Total del último pedido: <strong>{total:.2f} €</strong>.</p>" if total is not None else ""
    state["bot_message"] = (
        "<p>Tu pedido ya está confirmado.</p>"
        f"<p>Último envío: <strong>{name}</strong> en <strong>{city}</strong>.</p>"
        f"{total_txt}"
        "<p>Si quieres, puedo mostrarte el <strong>catálogo</strong> para seguir comprando o puedes escribir <strong>'salir'</strong>.</p>"
    )
    state["mode"] = "confirmation"
    return state

def handle_exit(state: ConversationState) -> ConversationState:
    state["cart"].clear()
    state["applied_coupon_code"] = None
    state["shipping_name"] = None
    state["shipping_city"] = None
    state["last_user_message"] = ""
    state["mode"] = "catalog"
    state["bot_message"] = (
        "<p><strong>Sesión finalizada.</strong> He vaciado tu carrito.</p>"
        "<p>Gracias por tu visita.</p>"
    )
    return state


def build_graph():
    graph = StateGraph(ConversationState)

    graph.add_node("router", router_node)
    graph.add_node("catalog", handle_catalog)
    graph.add_node("add_to_cart", handle_add_to_cart)
    graph.add_node("remove_from_cart", handle_remove_from_cart)
    graph.add_node("update_quantity", handle_update_quantity)
    graph.add_node("show_cart", handle_show_cart)
    graph.add_node("checkout", handle_checkout)
    graph.add_node("shipping", handle_shipping)
    graph.add_node("confirmation", handle_confirmation)
    graph.add_node("apply_coupon", handle_apply_coupon)
    graph.add_node("smalltalk", handle_smalltalk)
    graph.add_node("greeting", handle_greeting)
    graph.add_node("help", handle_help)
    graph.add_node("unknown", handle_unknown)
    graph.add_node("exit", handle_exit)

    graph.set_entry_point("router")

    def route_decision(state: ConversationState) -> str:
        parsed = parse_user_message(state["last_user_message"])

        # 1) SHIPPING: permitir exit/help incluso durante shipping
        if state["mode"] == "shipping":
            if parsed.intent in ("exit", "help"):
                return parsed.intent
            return "shipping"

        # 2) CONFIRMATION: permitir salir/ayuda/catálogo/carrito
        if state["mode"] == "confirmation":
            if parsed.intent in ("exit", "help", "show_catalog", "show_cart"):
                return {
                    "exit": "exit",
                    "help": "help",
                    "show_catalog": "catalog",
                    "show_cart": "show_cart",
                }[parsed.intent]
            return "confirmation"

        # 3) Ruteo normal por intención
        intent = parsed.intent

        if intent == "show_catalog":
            return "catalog"
        if intent == "add_to_cart":
            return "add_to_cart"
        if intent == "remove_from_cart":
            return "remove_from_cart"
        if intent == "update_quantity":
            return "update_quantity"
        if intent == "show_cart":
            return "show_cart"
        if intent == "checkout":
            return "checkout"
        if intent == "apply_coupon":
            return "apply_coupon"
        if intent == "smalltalk":
            return "smalltalk"
        if intent == "greeting":
            return "greeting"
        if intent == "help":
            return "help"
        if intent == "exit":
            return "exit"

        return "unknown"

    graph.add_conditional_edges(
        "router",
        route_decision,
        {
            "catalog": "catalog",
            "add_to_cart": "add_to_cart",
            "remove_from_cart": "remove_from_cart",
            "update_quantity": "update_quantity",
            "show_cart": "show_cart",
            "checkout": "checkout",
            "apply_coupon": "apply_coupon",
            "smalltalk": "smalltalk",
            "greeting": "greeting",
            "help": "help",
            "shipping": "shipping",
            "confirmation": "confirmation",
            "exit": "exit",
            "unknown": "unknown",
            END: END,
        },
    )

    graph.add_edge("exit", END)

    return graph.compile()