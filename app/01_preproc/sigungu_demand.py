"""
시군구별 차량 환산 수요 산출 모듈 (sigungu_demand.py)

목적:
    배송 실적 데이터에서 시군구(sub_region_code) 단위로 3.5T, 5T 기준
    차량 환산 수요를 산출한다. 각 배송처가 데이터 기간 동안 몇 대 분량의
    차량 부담을 만드는지 파악하는 것이 목적.
    CBM 데이터가 없으므로 적재 기준표의 1본당 적재율(%)을 이용하여
    트럭 환산 대수로 수요를 측정한다.
    3PL 물량도 배송처 수요로 포함한다.

입력:
    - 배송 실적: raw_data/1.업체 공유용_배송 실적_*.csv
    - 적재 기준표: 00_draft/타이어사이즈별_적재기준표.csv
    - Ship-to 매핑: doc/wemeet/shipto_master.csv
    - 시군구 마스터: doc/wemeet/sigungu_master.csv

출력:
    - doc/wemeet/sigungu_demand.csv
    - 컬럼: sub_region_code, sigungu_name, total_qty, shipment_count,
            demand_3_5t, demand_5t, daily_demand_3_5t, daily_demand_5t, delivery_days

사용법:
    from sigungu_demand import generate_sigungu_demand

    df = generate_sigungu_demand()
"""

from pathlib import Path
from typing import Optional

import pandas as pd

APP_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = APP_DIR.parent
RAW_DATA_DIR = PROJECT_DIR / "raw_data"
DB_DIR = APP_DIR / "db"
WEMEET_DIR = PROJECT_DIR / "doc" / "wemeet"


def load_delivery_data() -> pd.DataFrame:
    """배송 실적 로드."""
    path = RAW_DATA_DIR / "1.업체 공유용_배송 실적_2025년 2월 11월_20260317.csv"
    df = pd.read_csv(path, skiprows=3, low_memory=False)
    df["Q'ty_num"] = pd.to_numeric(df[" Q'ty "], errors="coerce")
    df["date"] = pd.to_datetime(df["Actual G/I Date"], errors="coerce")
    return df


def load_loading_standards() -> pd.DataFrame:
    """적재 기준표 로드."""
    df = pd.read_csv(DB_DIR / "타이어사이즈별_적재기준표.csv")
    return df[["사이즈", "3.5T_1본당%", "5T_1본당%"]].dropna(subset=["사이즈"])


def generate_sigungu_demand(
    exclude_region_prefixes: Optional[list] = None,
    output_path: Optional[str] = None,
) -> pd.DataFrame:
    """
    시군구별 3.5T / 5T 차량 환산 수요 산출.

    Args:
        exclude_region_prefixes: 제외할 sub_region_code prefix (예: ["JEJ"])
        output_path: 저장 경로 (None이면 기본 경로)

    Returns:
        시군구별 수요 DataFrame
    """
    # 데이터 로드
    print("데이터 로드 중...")
    delivery = load_delivery_data()
    loading = load_loading_standards()
    shipto = pd.read_csv(WEMEET_DIR / "shipto_master.csv")
    sigungu_master = pd.read_csv(WEMEET_DIR / "sigungu_master.csv")

    if exclude_region_prefixes:
        mask = sigungu_master["sub_region_code"].str.startswith(tuple(exclude_region_prefixes))
        sigungu_master = sigungu_master[~mask]

    # 배송 실적 × 적재 기준표 매칭
    print("적재 기준표 매칭...")
    merged = delivery.merge(loading, left_on="Size", right_on="사이즈", how="left")

    # 환산 대수 계산
    merged["demand_3_5t_row"] = merged["Q'ty_num"] * merged["3.5T_1본당%"] / 100
    merged["demand_5t_row"] = merged["Q'ty_num"] * merged["5T_1본당%"] / 100

    # 매칭 안 된 건 확인
    unmatched = merged["3.5T_1본당%"].isna().sum()
    total = len(merged)
    print(f"적재 기준 매칭: {total - unmatched:,}/{total:,}건 ({(total - unmatched) / total * 100:.1f}%)")
    if unmatched > 0:
        unmatch_sizes = merged[merged["3.5T_1본당%"].isna()]["Size"].value_counts().head(10)
        print(f"미매칭 상위 사이즈: {dict(unmatch_sizes)}")

    # Ship-to party → sub_region_code 매핑
    print("시군구 매핑...")
    shipto_map = shipto[["Ship-to party", "sub_region_code"]].drop_duplicates()
    shipto_map["Ship-to party"] = shipto_map["Ship-to party"].astype(str)
    merged["Ship-to party_str"] = merged["Ship-to party"].astype(str)

    merged = merged.merge(
        shipto_map,
        left_on="Ship-to party_str",
        right_on="Ship-to party",
        how="left",
        suffixes=("", "_mapped"),
    )

    # 제주 제외
    if exclude_region_prefixes:
        for prefix in exclude_region_prefixes:
            merged = merged[
                merged["sub_region_code"].isna() |
                ~merged["sub_region_code"].str.startswith(prefix)
            ]

    # 시군구별 집계
    print("시군구별 집계...")
    valid = merged[merged["sub_region_code"].notna()].copy()

    agg = valid.groupby("sub_region_code").agg(
        total_qty=("Q'ty_num", "sum"),
        shipment_count=("Shipment No.", "nunique"),
        demand_3_5t=("demand_3_5t_row", "sum"),
        demand_5t=("demand_5t_row", "sum"),
        delivery_days=("date", "nunique"),
    ).reset_index()

    # 일평균
    agg["daily_demand_3_5t"] = (agg["demand_3_5t"] / agg["delivery_days"]).round(1)
    agg["daily_demand_5t"] = (agg["demand_5t"] / agg["delivery_days"]).round(1)

    # 반올림
    agg["demand_3_5t"] = agg["demand_3_5t"].round(1)
    agg["demand_5t"] = agg["demand_5t"].round(1)
    agg["total_qty"] = agg["total_qty"].astype(int)

    # 시군구명 매핑
    name_map = sigungu_master[["sub_region_code", "광역도시", "시군구"]].copy()
    name_map["sigungu_name"] = name_map["광역도시"] + " " + name_map["시군구"]

    result = agg.merge(
        name_map[["sub_region_code", "sigungu_name"]],
        on="sub_region_code",
        how="left",
    )

    # 컬럼 순서 정리
    result = result[[
        "sub_region_code", "sigungu_name", "total_qty", "shipment_count",
        "demand_3_5t", "demand_5t", "daily_demand_3_5t", "daily_demand_5t",
        "delivery_days",
    ]].sort_values("demand_3_5t", ascending=False).reset_index(drop=True)

    # 저장
    if output_path is None:
        output_path = WEMEET_DIR / "sigungu_demand.csv"
    result.to_csv(output_path, index=False)
    print(f"\n저장 완료: {output_path} ({len(result)}행)")

    return result


if __name__ == "__main__":
    df = generate_sigungu_demand(exclude_region_prefixes=["JEJ"])
    print(f"\n상위 10개 시군구:")
    print(df.head(10).to_string())
    print(f"\n합계: 3.5T={df['demand_3_5t'].sum():.1f}대, 5T={df['demand_5t'].sum():.1f}대")
