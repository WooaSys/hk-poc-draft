"""
비용 산출 모듈 (cost_calculator.py)

목적:
    VROOM 배차 결과의 거리에 보정계수를 적용하고,
    단가표 기준 배송 비용을 산출한다.

입력:
    - VROOM 경로별 거리 (km)
    - 거리 보정계수 (OSRM 거리 구간별)
    - 배송 단가표 (app/db/delivery_price_202511.csv)

출력:
    - 경로별/RDC별 배송 비용

사용법:
    from vroom_engine.cost_calculator import apply_distance_correction, calculate_route_cost
"""

from pathlib import Path

import pandas as pd

APP_DIR = Path(__file__).resolve().parent.parent.parent
DB_DIR = APP_DIR / "db"

# 거리 구간별 보정계수 (28_거리보정계수.md 기반)
DISTANCE_CORRECTION = [
    (30, 1.82),
    (60, 1.52),
    (90, 1.25),
    (120, 1.25),
    (150, 1.22),
    (200, 1.31),
    (300, 1.29),
    (float("inf"), 1.29),  # 300km 이상
]

# 단가표 거리구간
PRICE_BINS = [
    (10, "1~10 km"), (20, "11~20 km"), (30, "21~30 km"),
    (40, "31~40 km"), (50, "41~50 km"), (60, "51~60 km"),
    (70, "61~70 km"), (80, "71~80 km"), (90, "81~90 km"),
    (100, "91~100 km"), (120, "101~120 km"), (140, "121~140 km"),
    (160, "141~160 km"), (180, "161~180 km"), (200, "181~200 km"),
    (230, "201~230 km"), (260, "231~260 km"), (290, "261~290 km"),
    (320, "291~320 km"), (350, "321~350 km"),
]


def apply_distance_correction(osrm_km: float) -> float:
    """OSRM 거리에 보정계수 적용."""
    for upper, factor in DISTANCE_CORRECTION:
        if osrm_km <= upper:
            return osrm_km * factor
    return osrm_km * 1.29


def distance_to_price_range(km: float) -> str:
    """보정된 거리를 단가표 거리구간으로 변환."""
    for upper, label in PRICE_BINS:
        if km <= upper:
            return label
    return "321~350 km"


def load_price_map(truck_type: str = "3.5T") -> dict:
    """단가표를 {(rdc_name, distance_range): price} 딕셔너리로 로드."""
    df = pd.read_csv(DB_DIR / "delivery_price_202511.csv")
    df = df[df["truck_type"] == truck_type]
    return {(row["rdc_name"], row["distance_range"]): row["price"] for _, row in df.iterrows()}


def calculate_route_cost(
    rdc_name: str,
    route_distance_km: float,
    price_map: dict | None = None,
    truck_type: str = "3.5T",
) -> dict:
    """
    단일 경로의 비용 산출.

    Args:
        rdc_name: RDC 이름
        route_distance_km: VROOM이 산출한 경로 거리 (km)
        price_map: 단가 딕셔너리 (None이면 로드)
        truck_type: 트럭 톤수

    Returns:
        {"osrm_km": float, "corrected_km": float, "price_range": str, "cost": int}
    """
    if price_map is None:
        price_map = load_price_map(truck_type)

    corrected_km = apply_distance_correction(route_distance_km)
    price_range = distance_to_price_range(corrected_km)
    cost = price_map.get((rdc_name, price_range), 0)

    return {
        "osrm_km": round(route_distance_km, 1),
        "corrected_km": round(corrected_km, 1),
        "price_range": price_range,
        "cost": cost,
    }
