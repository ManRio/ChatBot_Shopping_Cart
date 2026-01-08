# Chatbot conversacional de carrito de la compra (LangGraph + Flask)

## Descripción del proyecto

Este proyecto implementa un **chatbot conversacional de carrito de la compra** que simula el proceso de compra en una tienda online.
El usuario interactúa mediante **lenguaje natural** para consultar productos, gestionar un carrito, aplicar descuentos y finalizar un pedido.

El flujo conversacional está modelado mediante **LangGraph**, utilizando un **grafo de estados explícito**, y la interfaz se ha implementado como una **aplicación web con Flask**.
Como mejora adicional, se ha desarrollado una interfaz visual con HTML, CSS y JavaScript, incluyendo llamadas **AJAX** para mejorar la experiencia de usuario.

El objetivo de la prueba es demostrar:

- Capacidad de abstracción de un problema real.
- Diseño de una solución modular, mantenible y testeable.
- Uso correcto de LangGraph para modelar estados y transiciones.
- Manejo de errores, ambigüedades y entradas fuera de contexto.
- Propuesta y desarrollo de mejoras adicionales.

---

## Tecnologías utilizadas

- **Python 3**
- **Flask** – interfaz web y gestión de sesión
- **LangGraph** – modelado del flujo conversacional
- **HTML / CSS** – interfaz visual
- **JavaScript (Vanilla)** – interacción dinámica y llamadas AJAX
- **Pytest** – tests automatizados

---

## Estructura del proyecto

```text
shopping_bot/
├── app/
│   ├── __init__.py
│   └── flask_app.py
├── conversation/
│   ├── __init__.py
│   ├── graph.py
│   ├── nlu.py
│   └── state.py
├── data/
│   ├── coupons.json
│   └── products.json
├── domain/
│   ├── __init__.py
│   ├── catalog.py
│   ├── coupons.py
│   ├── models.py
│   └── pricing.py
├── static/
│   ├── app.js
│   ├── styles.css
│   └── img/
├── templates/
│   ├── base.html
│   ├── chat.html
│   └── partials/
│       ├── cart_content.html
│       ├── cart_modal.html
│       └── product_modal.html
├── tests/
├── requirements.txt
└── README.md
```

---

## Funcionalidades implementadas

- Consulta del catálogo de productos.
- Gestión completa del carrito (añadir, eliminar, modificar cantidades).
- Visualización del carrito, con subtotales, descuentos y total final.
- Aplicación de cupones de descuento.
- Descuentos automáticos por cantidad y por importe total.
- Flujo de checkout.
- Recogida de datos de envío (nombre y ciudad).
- Cierre explícito de la sesión con limpieza del estado.

## Funcionalidades Adicionales

- Interfaz web con:
  - Tarjetas de Producto.
  - Modal de Carrito.
  - Modal de detalle de producto.
  - Chat flotante persistente
- Uso de AJAX para:
  - Añadir productos al carrito sin recargar la página.
  - Interactuar con el chatbot sin recargar la página.
- Manejo de ambigüedades en lenguaje natural.
- Confirmación de pedido persistente dentro de la sesión.
- Tests automatizados extensivos.

---

## Gestión de estados con LangGraph

El flujo conversacional se modela como un grafo de estados explícito, separando claramente la lógica de dominio de la lógica conversacional.

Estados principales:

- router
- catalog
- add_to_cart
- remove_from_cart
- update_quantity
- show_cart
- apply_coupon
- checkout
- shipping
- confirmation
- exit
- unknown / smalltalk

---

## Decisiones de Diseño

- Estado conversacional tipado mediante TypedDict.
- Parser NLU rule-based, explícito y fácilmente extensible.
- Separación clara entre:
  - Dominio (Carrito, Productos, Precios).
  - Conversación (nodos y transiciones).
- Interrupciones controladas en estados críticos

---

## Ejemplos de interacción

```text
Usuario: ¿Qué productos tenéis?
Bot: [muestra catálogo]

Usuario: Añade 2 camisetas azules
Bot: He añadido 2 camisetas azules a tu carrito.

Usuario: Pon 3 en lugar de 2
Bot: He actualizado la cantidad a 3 unidades.

Usuario: Aplica el cupón VIP20
Bot: He aplicado el cupón VIP20 a tu carrito.

Usuario: Quiero finalizar la compra
Bot: El total es 47,20 €. ¿Cuál es tu nombre y ciudad?

Usuario: Soy Ana de Madrid
Bot: Pedido registrado correctamente.
```

---

### Tests Automatizados

El proyecto incluye una batería de tests automatizados con **pytest**
**Cobertura**

- Dominio:
  - Operaciones del Carrito.
  - Validaciones de Cantidades.
- Lógica de Precios:
  - Descuentos por cantidad (Al superar las 3 uds).
  - Descuento por importe total (Al superar los 100€).
  - Cupones (Porcentaje y fijos)
- NLU:
  - Detección de Intención.
  - Extracción de producto y cantidades.
  - Manejo de frases ambiguas.
- Flujo conversacional:
  - Trancisiones clave del grafo.
  - Estados críticos (Checkout, shipping, exit)

Ejecución de los tests

```text
pytest -q
```

---

## Instalación y ejecución

1. Crear entorno virtual (opcional):
   python -m venv .venv

2. Activar entorno:
   source .venv/bin/activate
   o
   .venv\Scripts\activate

3. Instalar dependencias:
   pip install -r requirements.txt

4. Ejecutar la aplicación:
   python -m app.flask_app

La aplicación estará disponible en http://127.0.0.1:5000

---

## Notas finales

Este proyecto no pretende ser un sistema de producción, sino una **demostración de diseño, razonamiento técnico y calidad de código** dentro del contexto de la prueba técnica.
