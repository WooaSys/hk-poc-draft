"""
자연권역 생성 모듈 (natural_territory.py)

목적:
    각 시군구를 소요시간(duration) 기준 가장 가까운 RDC에 배정한 자연권역을 생성한다.
    자연권역은 최종 배정안이 아니라 현재 권역 구조의 왜곡을 판단하고
    재분배 방향을 설정하기 위한 기준선(reference layer)이다.
    OR-Tools를 사용하지 않고 argmin 기반 단순 할당으로 생성한다.

입력:
    - app/db/cost_matrix.csv (RDC×시군구 비용행렬, duration_rank 포함)
    - app/db/sigungu_demand.csv (시군구별 수요)
    - app/db/shipto_master.csv (현재 RDC 배정)

출력:
    - 자연권역 DataFrame (시군구별 natural RDC, current RDC, 수요, gap)
    - RDC별 Natural Load vs Current Load 비교

사용법:
    from natural_territory import generate_natural_territory

    df, load_summary = generate_natural_territory()
    df, load_summary = generate_natural_territory(include_jungbu=False)
"""

from pathlib import Path
from typing import Optional

import pandas as pd

APP_DIR = Path(__file__).resolve().parent.parent
DB_DIR = APP_DIR / "db"


def generate_natural_territory(
    include_jungbu: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    자연권역 생성.

    Args:
        include_jungbu: 중부RDC 포함 여부

    Returns:
        (territory_df, load_summary_df)
        - territory_df: 시군구별 자연권역 + 현재 배정 비교
        - load_summary_df: RDC별 Natural Load vs Current Load
    """
    cost = pd.read_csv(DB_DIR / "cost_matrix.csv")
    demand = pd.read_csv(DB_DIR / "sigungu_demand.csv")
    shipto = pd.read_csv(DB_DIR / "shipto_master.csv")

    # 중부RDC 제외 옵션
    if not include_jungbu:
        cost = cost[cost["rdc_name"] != "중부RDC"]

    # --- 자연권역: duration_rank=1 ---
    # 중부 제외 시 rank 재계산
    if not include_jungbu:
        cost["duration_rank"] = (
            cost.groupby("sub_region_code")["duration_min"]
            .rank(method="min")
            .astype("Int64")
        )

    natural = cost[cost["duration_rank"] == 1][[
        "sub_region_code", "sigungu_name",
        "rdc_code", "rdc_name", "duration_min", "distance_km",
    ]].copy()
    natural.columns = [
        "sub_region_code", "sigungu_name",
        "natural_rdc_code", "natural_rdc_name", "natural_time", "natural_distance",
    ]

    # --- 현재 RDC: 시군구별 수요 기준 최다 RDC ---
    shipto["Ship-to party"] = shipto["Ship-to party"].astype(str)

    # 시군구별 RDC별 배송지 수
    current_rdc = (
        shipto.groupby(["sub_region_code", "담당 RDC 명"])["Ship-to party"]
        .nunique()
        .reset_index()
    )
    current_rdc.columns = ["sub_region_code", "current_rdc_name", "shipto_count"]

    # 시군구별 최다 RDC
    idx = current_rdc.groupby("sub_region_code")["shipto_count"].idxmax()
    current_main = current_rdc.loc[idx][["sub_region_code", "current_rdc_name"]]

    # 현재 RDC의 시간 가져오기
    current_with_time = current_main.merge(
        cost[["sub_region_code", "rdc_name", "duration_min"]],
        left_on=["sub_region_code", "current_rdc_name"],
        right_on=["sub_region_code", "rdc_name"],
        how="left",
    )[["sub_region_code", "current_rdc_name", "duration_min"]]
    current_with_time.columns = ["sub_region_code", "current_rdc_name", "current_time"]

    # --- 병합 ---
    result = natural.merge(demand[["sub_region_code", "demand_3_5t", "demand_5t"]], on="sub_region_code", how="left")
    result = result.merge(current_with_time, on="sub_region_code", how="left")

    # gap 계산 (양수 = 현재가 더 먼 배정)
    result["time_gap"] = (result["current_time"] - result["natural_time"]).round(1)

    result = result.sort_values("demand_3_5t", ascending=False).reset_index(drop=True)

    # --- RDC별 Natural Load vs Current Load ---
    natural_load = result.groupby("natural_rdc_name").agg(
        natural_load_3_5t=("demand_3_5t", "sum"),
        natural_load_5t=("demand_5t", "sum"),
        natural_sigungu_count=("sub_region_code", "count"),
    ).reset_index().rename(columns={"natural_rdc_name": "rdc_name"})

    current_load = result.groupby("current_rdc_name").agg(
        current_load_3_5t=("demand_3_5t", "sum"),
        current_load_5t=("demand_5t", "sum"),
        current_sigungu_count=("sub_region_code", "count"),
    ).reset_index().rename(columns={"current_rdc_name": "rdc_name"})

    load_summary = natural_load.merge(current_load, on="rdc_name", how="outer").fillna(0)
    load_summary["gap_3_5t"] = (load_summary["current_load_3_5t"] - load_summary["natural_load_3_5t"]).round(1)
    load_summary = load_summary.sort_values("current_load_3_5t", ascending=False).reset_index(drop=True)

    return result, load_summary


if __name__ == "__main__":
    print("=== 중부RDC 포함 ===")
    df, load = generate_natural_territory(include_jungbu=True)
    print(f"시군구: {len(df)}개")
    print(f"\nRDC별 Natural vs Current Load (3.5T):")
    print(load[["rdc_name", "natural_load_3_5t", "current_load_3_5t", "gap_3_5t",
                "natural_sigungu_count", "current_sigungu_count"]].to_string())

    print("\n\n=== 중부RDC 제외 ===")
    df2, load2 = generate_natural_territory(include_jungbu=False)
    print(f"\nRDC별 Natural vs Current Load (3.5T):")
    print(load2[["rdc_name", "natural_load_3_5t", "current_load_3_5t", "gap_3_5t",
                 "natural_sigungu_count", "current_sigungu_count"]].to_string())
