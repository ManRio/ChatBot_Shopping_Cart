import json
from pathlib import Path
from .models import Product

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "products.json"

def load_catalog() -> list[Product]:
    with open(DATA_PATH, "r", encoding="utf-8") as file:
        raw = json.load(file)
    return [Product(**item) for item in raw]

def find_product_by_id(catalog: list[Product], product_id: int) -> Product | None:
    return next((p for p in catalog if p.id == product_id), None)

def find_product_by_name(catalog: list[Product], name: str) -> Product | None:
    name_lower = name.lower()
    return next(
        (p for p in catalog if p.name.lower() in name_lower or name_lower in p.name.lower()),
        None,
    )