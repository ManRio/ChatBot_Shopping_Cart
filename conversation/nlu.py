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
    """Minúsculas + quitar acentos para facilitar matching."""
    text = text.lower().strip()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text


def extract_product_id(text: str) -> Optional[int]:
    """
    Busca patrones tipo:
    - 'producto 103'
    - 'id 103'
    - 'artículo 103'
    - 'producto nº 103'
    - 'del 103'
    """
    m = re.search(
        r"(producto|id|articulo|artículo)\s*(?:n[ºo]\s*)?(?:del\s+|de\s+)?(\d+)",
        text,
        re.IGNORECASE,
    )
    if m:
        return int(m.group(2))

    m2 = re.search(r"\bdel\s+(\d+)\b", text, re.IGNORECASE)
    if m2:
        return int(m2.group(1))

    return None


def extract_quantity(text: str) -> Optional[int]:
    """
    Detecta cantidades típicas:
    - '2 camisetas'
    - 'x3'
    - '3 unidades'
    - 'añade 2 camisetas' (número en mitad del texto)
    """
    # '3 unidades', '3 uds'
    m = re.search(r"\b(\d+)\s*(unidades?|uds?)\b", text, re.IGNORECASE)
    if m:
        return int(m.group(1))

    # 'x3'
    m = re.search(r"\bx\s*(\d+)\b", text, re.IGNORECASE)
    if m:
        return int(m.group(1))

    # número al principio: '2 camisetas'
    m = re.match(r"\s*(\d+)\b", text)
    if m:
        return int(m.group(1))

    # fallback: primer número que aparezca en cualquier parte
    m = re.search(r"\b(\d+)\b", text)
    if m:
        return int(m.group(1))

    return None


def pick_update_quantity(text: str, product_id: Optional[int]) -> Optional[int]:
    """
    Para update_quantity:
    - Caso especial: "pon 3 en lugar de 1 ..." => la cantidad nueva es el PRIMER número (3).
    - Resto: elegimos el último número que no sea el product_id.
    """
    nums = [int(n) for n in re.findall(r"\d+", text)]
    if not nums:
        return None

    # Caso "en lugar de" / "en vez de" => primer número = cantidad NUEVA
    if re.search(r"\ben\s+(lugar|vez)\s+de\b", text):
        if product_id is None:
            return nums[0]
        for n in nums:
            if n != product_id:
                return n
        return None

    # Caso normal: último número distinto del id
    if product_id is None:
        return nums[-1]

    for n in reversed(nums):
        if n != product_id:
            return n

    return None


# -----------------------
# Parsing principal
# -----------------------

def parse_user_message(message: str) -> ParsedIntent:
    """
    Parser rule-based: keywords + regex.
    """
    raw = message
    text = normalize(message)

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

    # 1) SALIR
    if any(k in text for k in exit_keywords):
        return ParsedIntent(intent="exit")

    # 2) SALUDO
    if any(k in text for k in greeting_keywords):
        return ParsedIntent(intent="greeting")

    # 3) AYUDA
    if any(k in text for k in help_keywords):
        return ParsedIntent(intent="help")

    # 4) VER CARRITO
    if any(k in text for k in cart_keywords):
        return ParsedIntent(intent="show_cart")

    # 5) CUPÓN
    if any(k in text for k in coupon_keywords):
        m = re.search(
            r"(?:cupon|cup[oó]n|descuento|promo)\s+([a-zA-Z0-9_-]+)",
            raw,
            re.IGNORECASE,
        )
        code = m.group(1) if m else None
        return ParsedIntent(intent="apply_coupon", coupon_code=code)

    # 6) CHECKOUT
    if any(k in text for k in checkout_keywords):
        return ParsedIntent(intent="checkout")

    # 7) UPDATE (antes que add)
    if any(k in text for k in update_keywords):
        pid = extract_product_id(raw)
        qty = pick_update_quantity(text, pid)
        return ParsedIntent(
            intent="update_quantity",
            product_id=pid,
            quantity=qty,
            product_name=raw if pid is None else None,
        )
    
    # 7.5) Caso especial: "pon X en lugar de Y ..." => update_quantity
    # (aunque "pon" sea keyword de add, aquí prima el patrón de actualización)
    if re.search(r"\ben\s+(lugar|vez)\s+de\b", text) and ("pon" in text):
        pid = extract_product_id(raw)
        qty = pick_update_quantity(text, pid)
        return ParsedIntent(
            intent="update_quantity",
            product_id=pid,
            quantity=qty,
            product_name=raw if pid is None else None,
    )

    # 8) ADD
    if any(k in text for k in add_keywords):
        pid = extract_product_id(raw)
        qty = extract_quantity(text)

        # Caso "pon el producto 402": qty detecta 402 pero es el id.
        if pid is not None and qty == pid:
            qty = None

        return ParsedIntent(
            intent="add_to_cart",
            product_id=pid,
            quantity=qty,
            product_name=raw if pid is None else None,
        )

    # 9) REMOVE
    if any(k in text for k in remove_keywords):
        pid = extract_product_id(raw)
        return ParsedIntent(
            intent="remove_from_cart",
            product_id=pid,
            product_name=raw if pid is None else None,
        )

    # 10) CATÁLOGO
    if any(k in text for k in catalog_keywords):
        return ParsedIntent(intent="show_catalog")

    # 11) SMALLTALK
    if "tiempo" in text or "clima" in text:
        return ParsedIntent(intent="smalltalk")

    # 12) UNKNOWN
    return ParsedIntent(intent="unknown")