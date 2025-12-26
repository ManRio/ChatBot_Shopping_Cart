# Chatbot conversacional de carrito de la compra (LangGraph + Flask)

## Descripción del proyecto

Este proyecto implementa un **chatbot conversacional de carrito de la compra** que simula el proceso de compra en una tienda online.  
El usuario interactúa mediante lenguaje natural para consultar productos, gestionar un carrito, aplicar descuentos y finalizar un pedido.

El flujo conversacional se ha modelado mediante **LangGraph**, utilizando un grafo de estados explícito, y la interfaz se ha implementado como una **aplicación web sencilla con Flask**.

El objetivo principal del proyecto es demostrar la capacidad de:

- Abstraer un problema real.
- Diseñar una solución modular y mantenible en Python.
- Modelar flujos conversacionales con estados.
- Manejar errores y casos fuera de contexto.
- Extender el sistema con funcionalidades adicionales.

---

## Tecnologías utilizadas

- **Python 3**
- **Flask** – interfaz web y gestión de sesión
- **LangGraph** – modelado del flujo conversacional
- **HTML / CSS** – interfaz visual
- **Pytest** – tests automatizados

---

## Estructura del proyecto

```text
shopping_bot/
├── app/
│   ├── flask_app.py
│   └── __init__.py
│
├── conversation/
│   ├── graph.py
│   ├── nlu.py
│   ├── state.py
│   └── __init__.py
│
├── domain/
│   ├── models.py
│   ├── catalog.py
│   ├── coupons.py
│   ├── pricing.py
│   └── __init__.py
│
├── data/
│   ├── products.json
│   └── coupons.json
│
├── templates/
│   ├── base.html
│   └── chat.html
│
├── static/
│   └── styles.css
│
├── tests/
│
├── requirements.txt
└── README.md
```

---

## Funcionalidades implementadas

- Consulta del catálogo de productos.
- Gestión completa del carrito (añadir, eliminar, modificar cantidades).
- Aplicación de cupones de descuento.
- Descuentos por cantidad y por importe total.
- Flujo de checkout con recogida de datos de envío.
- Cierre explícito de la sesión con limpieza del estado.

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
- exit
- unknown / smalltalk

---

## Instalación y ejecución

1. Crear entorno virtual (opcional):

```bash
python -m venv .venv
```

2. Activar entorno:

```bash
source .venv/bin/activate
```

o en Windows:

```bash
.venv\Scripts\activate
```

3. Instalar dependencias:

```bash
pip install -r requirements.txt
```

4. Ejecutar la aplicación:

```bash
python -m app.flask_app
```

La aplicación estará disponible en:

```
http://127.0.0.1:5000
```

---

## Tests automatizados

El proyecto incluye una batería de **tests automatizados con pytest** que cubren las partes más relevantes de la lógica de negocio y del flujo conversacional.

### Cobertura de los tests

Los tests actuales validan, entre otros aspectos:

- **Dominio**

  - Operaciones del carrito (añadir, eliminar, modificar cantidades).
  - Validación de cantidades inválidas.
  - Limpieza del carrito al finalizar la sesión.

- **Lógica de precios**

  - Descuentos por cantidad.
  - Descuento por importe total del carrito.
  - Aplicación de cupones (porcentaje y valor fijo).
  - Casos límite (cupones con mínimo, descuentos que no pueden dejar total negativo).

- **NLU (parseo de intención)**

  - Detección de intención principal.
  - Extracción de identificadores de producto.
  - Extracción de cantidades.
  - Manejo de ambigüedades comunes en lenguaje natural.

- **Flujo conversacional (LangGraph)**
  - Enrutado correcto entre estados.
  - Transiciones clave (catálogo, añadir al carrito, checkout, salida).
  - Actualización del estado conversacional.

### Ejecución de los tests

Desde la raíz del proyecto:

```bash
pytest -q
```

En sistemas Windows, si es necesario:

```bash
python -m pytest -q
```

---

## Notas finales

Este proyecto no pretende ser un sistema de producción, sino una **demostración de diseño, estructuración y razonamiento técnico** ante un problema real de conversación y gestión de estado.
