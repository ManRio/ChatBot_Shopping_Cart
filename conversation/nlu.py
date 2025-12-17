from dataclasses import dataclass
from typing import Literal, Optional
import re
import unicodedata


IntentType = Literal[
    "show_catalog",
    "show_cart",
    "add_to_cart",
    "remove_from_cart",
    "update_quantity",
    "checkout",
    "apply_coupon",
    "exit",
    "smalltalk",
    "help",
    "greeting",
    "unknown",
]


@dataclass
class ParsedIntent:
    intent: IntentType
    product_name: Optional[str] = None
    product_id: Optional[int] = None
    quantity: Optional[int] = None
    coupon_code: Optional[str] = None


# -----------------------
# Utilidades de parsing
# -----------------------


def normalize(text: str) -> str:
    """
    Minúsculas + quitar acentos para facilitar matching de palabras clave.
    """
    text = text.lower().strip()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text


def extract_first_int(text: str) -> Optional[int]:
    """
    Devuelve el primer entero encontrado en el texto.
    """
    match = re.search(r"\d+", text)
    if match:
        return int(match.group(0))
    return None


def extract_last_int(text: str) -> Optional[int]:
    """
    Devuelve el último entero encontrado en el texto.
    Útil para frases tipo 'pon 3 en lugar de 1' → 1 y 3 → usamos 3.
    """
    nums = re.findall(r"\d+", text)
    if not nums:
        return None
    return int(nums[-1])


def extract_product_id(text: str) -> Optional[int]:
    """
    Busca patrones tipo 'producto 103', 'id 103', 'articulo 103', etc.
    """
    m = re.search(
        r"(producto|id|articulo|artículo)\s+(?:del\s+|de\s+)?(\d+)",
        text,
        re.IGNORECASE,
    )
    if m:
        return int(m.group(2))
    # Otra variante, añadiendo solo el id
    m2 = re.search(r"\bdel\s+(\d{3})\b", text)
    if m2:
        return int(m2.group(1))

    return None


# -----------------------
# Parsing principal
# -----------------------


def parse_user_message(message: str) -> ParsedIntent:
    """
    Regla simple basada en keywords + regex para mapear un texto
    a una intención de alto nivel + parámetros.
    """
    raw = message
    text = normalize(message)

    # --- Palabras clave / sinónimos por intención ---

    exit_keywords = ["salir", "terminar", "cerrar", "adios", "hasta luego"]
    cart_keywords = ["carrito", "carro", "cesta", "basket"]
    coupon_keywords = ["cupon", "cupones", "descuento", "promo", "promocion"]
    checkout_keywords = [
        "finalizar",
        "pagar",
        "tramitar pedido",
        "terminar compra",
        "confirmar compra",
        "quiero finalizar la compra",
        "realizar el pago",
        "finalizar compra",
    ]
    catalog_keywords = [
        "catalogo",
        "productos",
        "tienda",
        "que teneis",
        "que tienes",
        "muestrame el catalogo",
        "mostrar catalogo",
        "ver catalogo",
        "ver productos",
        "que puedo comprar",
    ]
    add_keywords = [
        "anade",
        "añade",
        "agrega",
        "añadir",
        "meter",
        "mete",
        "pon",
        "incluye",
        "sumar",
        "compra",
        "comprar",
        "agregame",
        "echame",
    ]
    remove_keywords = [
        "quita",
        "quitar",
        "elimina",
        "borra",
        "saca",
        "retira",
        "eliminalo",
        "quitame",
    ]
    update_keywords = [
        "cambia",
        "cambiar",
        "ajusta",
        "ajustar",
        "modifica",
        "modificar",
        "actualiza",
        "actualizar",
        "deja",
    ]
    greeting_keywords = [
        "hola",
        "buenas",
        "buenos dias",
        "buenos días",
        "buenas tardes",
        "buenas noches",
        "hey",
        "que tal",
        "que hay",
    ]
    help_keywords = [
        "ayuda",
        "como funciona",
        "que puedo hacer",
        "que sabes hacer",
        "como te uso",
        "instrucciones",
        "ayudame",
    ]

    # -------------------
    # 1. SALIR
    # -------------------
    if any(k in text for k in exit_keywords):
        return ParsedIntent(intent="exit")

    # -------------------
    # 2. SALUDO
    # -------------------
    if any(k in text for k in greeting_keywords):
        return ParsedIntent(intent="greeting")

    # -------------------
    # 3. AYUDA
    # -------------------
    if any(k in text for k in help_keywords):
        return ParsedIntent(intent="help")

    # -------------------
    # 4. VER CARRITO
    # -------------------
    if any(k in text for k in cart_keywords):
        return ParsedIntent(intent="show_cart")

    # -------------------
    # 5. APLICAR CUPÓN
    # -------------------
    if any(k in text for k in coupon_keywords):
        m = re.search(r"(?:cupon|cup[oó]n|descuento|promo)\s+([a-zA-Z0-9_-]+)", raw, re.IGNORECASE)
        code = m.group(1) if m else None
        return ParsedIntent(intent="apply_coupon", coupon_code=code)

    # -------------------
    # 6. FINALIZAR COMPRA
    # -------------------
    if any(k in text for k in checkout_keywords):
        return ParsedIntent(intent="checkout")

    # -------------------
    # 7. ACTUALIZAR CANTIDAD (ANTES que añadir)
    # -------------------
    if any(k in text for k in update_keywords):
        new_qty = extract_last_int(text)
        product_id = extract_product_id(raw)
        return ParsedIntent(
            intent="update_quantity",
            quantity=new_qty,
            product_id=product_id,
            product_name=raw,
        )

    # -------------------
    # 8. AÑADIR AL CARRITO
    # -------------------
    if any(k in text for k in add_keywords):
        qty = extract_first_int(text)
        product_id = extract_product_id(raw)
        return ParsedIntent(
            intent="add_to_cart",
            quantity=qty,
            product_id=product_id,
            product_name=raw,
        )

    # -------------------
    # 9. ELIMINAR DEL CARRITO
    # -------------------
    if any(k in text for k in remove_keywords):
        product_id = extract_product_id(raw)
        return ParsedIntent(
            intent="remove_from_cart",
            product_id=product_id,
            product_name=raw,
        )

    # -------------------
    # 10. VER CATÁLOGO (DESPUÉS de add/update/remove)
    # -------------------
    if any(k in text for k in catalog_keywords):
        return ParsedIntent(intent="show_catalog")

    # -------------------
    # 11. SMALLTALK simple
    # -------------------
    if "tiempo" in text or "clima" in text:
        return ParsedIntent(intent="smalltalk")

    # -------------------
    # 12. SIN MATCH CLARO
    # -------------------
    return ParsedIntent(intent="unknown")