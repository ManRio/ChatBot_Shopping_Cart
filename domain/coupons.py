import json
from pathlib import Path
from .models import Coupon

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "coupons.json"

def load_coupons() -> list[Coupon]:
    with open(DATA_PATH, "r", encoding="utf-8") as file:
        raw = json.load(file)
    return [Coupon(**item) for item in raw]

def find_coupon_by_code(coupons: list[Coupon], code: str) -> Coupon | None:
    code_upper = code.upper()
    return next((coupon for coupon in coupons if coupon.code.upper() == code_upper), None)

