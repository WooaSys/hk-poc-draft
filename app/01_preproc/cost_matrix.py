"""
OSRM 비용행렬 생성 모듈 (cost_matrix.py)

목적:
    로컬 OSRM 서버를 이용하여 RDC ↔ 시군구 간 실제 도로 거리(km)와 소요시간(분)을 산출하고,
    시군구 기준으로 RDC 순위(rank)를 매긴 비용행렬 CSV를 생성한다.
    권역 재배치 최적화의 기초 데이터로 사용된다.

입력:
    - RDC 위치: app/db/rdc_locations.json
    - 시군구 위치: doc/wemeet/sigungu_master.csv (시청/구청 대표좌표)

출력:
    - doc/wemeet/cost_matrix.csv
    - 컬럼: rdc_code, rdc_name, sub_region_code, sigungu_name,
            duration_min, distance_km, duration_rank, distance_rank

사용법:
    from cost_matrix import generate_cost_matrix

    # 기본 사용 (제주 제외)
    df = generate_cost_matrix(
        exclude_rdc=["제주RDC"],
        exclude_region_prefixes=["JEJ"],
    )

    # OSRM 서버 주소 변경
    df = generate_cost_matrix(osrm_url="http://localhost:5002")

    # 특정 RDC만
    df = generate_cost_matrix(rdc_filter=["평택RDC", "칠곡RDC"])
"""

import json
import time
from pathlib import Path
from typing import Optional

import pandas as pd
import requests

# 기본 경로
APP_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = APP_DIR.parent
DB_DIR = APP_DIR / "db"
WEMEET_DIR = PROJECT_DIR / "doc" / "wemeet"

DEFAULT_OSRM_URL = "http://localhost:5002"


def load_rdc_locations(exclude_names: Optional[list] = None) -> pd.DataFrame:
    """RDC 위치 로드."""
    with open(DB_DIR / "rdc_locations.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    if exclude_names:
        df = df[~df["name"].isin(exclude_names)]
    return df.reset_index(drop=True)


def load_sigungu_master(exclude_prefixes: Optional[list] = None) -> pd.DataFrame:
    """시군구 마스터 로드."""
    df = pd.read_csv(WEMEET_DIR / "sigungu_master.csv")
    if exclude_prefixes:
        mask = df["sub_region_code"].str.startswith(tuple(exclude_prefixes))
        df = df[~mask]
    return df.reset_index(drop=True)


def query_osrm_route(
    origin_lon: float,
    origin_lat: float,
    dest_lon: float,
    dest_lat: float,
    osrm_url: str = DEFAULT_OSRM_URL,
) -> dict:
    """OSRM route API 단건 호출. duration(초), distance(m) 반환."""
    url = f"{osrm_url}/route/v1/driving/{origin_lon},{origin_lat};{dest_lon},{dest_lat}"
    params = {"overview": "false"}
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    if data["code"] != "Ok" or not data["routes"]:
        return {"duration": None, "distance": None}

    route = data["routes"][0]
    return {
        "duration": route["duration"],
        "distance": route["distance"],
    }


def generate_cost_matrix(
    osrm_url: str = DEFAULT_OSRM_URL,
    rdc_filter: Optional[list] = None,
    exclude_rdc: Optional[list] = None,
    exclude_region_prefixes: Optional[list] = None,
    output_path: Optional[str] = None,
) -> pd.DataFrame:
    """
    RDC × 시군구 비용행렬 생성.

    Args:
        osrm_url: OSRM 서버 주소
        rdc_filter: 포함할 RDC 이름 리스트 (None이면 전체)
        exclude_rdc: 제외할 RDC 이름 리스트
        exclude_region_prefixes: 제외할 sub_region_code prefix (예: ["JEJ"])
        output_path: 저장 경로 (None이면 기본 경로)

    Returns:
        비용행렬 DataFrame
    """
    # 데이터 로드
    rdc_df = load_rdc_locations(exclude_names=exclude_rdc)
    if rdc_filter:
        rdc_df = rdc_df[rdc_df["name"].isin(rdc_filter)]

    sigungu_df = load_sigungu_master(exclude_prefixes=exclude_region_prefixes)

    total = len(rdc_df) * len(sigungu_df)
    print(f"RDC {len(rdc_df)}개 × 시군구 {len(sigungu_df)}개 = {total}건 조회")

    # OSRM 조회
    rows = []
    count = 0
    for _, rdc in rdc_df.iterrows():
        for _, sg in sigungu_df.iterrows():
            count += 1
            if count % 100 == 0:
                print(f"  진행: {count}/{total}")

            result = query_osrm_route(
                rdc["lon"], rdc["lat"],
                sg["lon"], sg["lat"],
                osrm_url=osrm_url,
            )

            rows.append({
                "rdc_code": rdc["plant_code"],
                "rdc_name": rdc["name"],
                "sub_region_code": sg["sub_region_code"],
                "sigungu_name": f"{sg['광역도시']} {sg['시군구']}",
                "duration_min": round(result["duration"] / 60, 1) if result["duration"] else None,
                "distance_km": round(result["distance"] / 1000, 1) if result["distance"] else None,
            })

    df = pd.DataFrame(rows)

    # 시군구 기준 rank 부여
    df["duration_rank"] = (
        df.groupby("sub_region_code")["duration_min"]
        .rank(method="min")
        .astype("Int64")
    )
    df["distance_rank"] = (
        df.groupby("sub_region_code")["distance_km"]
        .rank(method="min")
        .astype("Int64")
    )

    # 저장
    if output_path is None:
        output_path = WEMEET_DIR / "cost_matrix.csv"
    df.to_csv(output_path, index=False)
    print(f"\n저장 완료: {output_path} ({len(df)}행)")

    return df


if __name__ == "__main__":
    df = generate_cost_matrix(
        exclude_rdc=["제주RDC"],
        exclude_region_prefixes=["JEJ"],
    )
    print(f"\n샘플:")
    print(df.head(10).to_string())
