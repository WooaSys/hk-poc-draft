"""
시군구 간 OSRM 비용행렬 생성 모듈 (sigungu_matrix.py)

목적:
    로컬 OSRM route API를 이용하여 시군구 간 상호 거리(km)와 소요시간(분)을 산출한다.
    권역 연결성 분석, 고립/경계 시군구 판별, 자연스러운 권역 형태 검증,
    경로 최적화 시뮬레이션의 기초 데이터로 사용된다.

입력:
    - 시군구 위치: doc/wemeet/sigungu_master.csv (시청/구청 대표좌표)

출력:
    - doc/wemeet/sigungu_matrix.csv
    - 컬럼: from_code, from_name, to_code, to_name, duration_min, distance_km

사용법:
    from sigungu_matrix import generate_sigungu_matrix

    # 기본 사용 (제주 제외)
    df = generate_sigungu_matrix(exclude_region_prefixes=["JEJ"])
"""

from pathlib import Path
from typing import Optional

import pandas as pd
import requests

APP_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = APP_DIR.parent
WEMEET_DIR = PROJECT_DIR / "doc" / "wemeet"

DEFAULT_OSRM_URL = "http://localhost:5002"


def load_sigungu_master(exclude_prefixes: Optional[list] = None) -> pd.DataFrame:
    """시군구 마스터 로드."""
    df = pd.read_csv(WEMEET_DIR / "sigungu_master.csv")
    if exclude_prefixes:
        mask = df["sub_region_code"].str.startswith(tuple(exclude_prefixes))
        df = df[~mask]
    return df.reset_index(drop=True)


def query_osrm_route(
    origin_lon: float, origin_lat: float,
    dest_lon: float, dest_lat: float,
    osrm_url: str = DEFAULT_OSRM_URL,
) -> dict:
    """OSRM route API 단건 호출."""
    url = f"{osrm_url}/route/v1/driving/{origin_lon},{origin_lat};{dest_lon},{dest_lat}"
    resp = requests.get(url, params={"overview": "false"}, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    if data["code"] != "Ok" or not data["routes"]:
        return {"duration": None, "distance": None}

    route = data["routes"][0]
    return {"duration": route["duration"], "distance": route["distance"]}


def generate_sigungu_matrix(
    osrm_url: str = DEFAULT_OSRM_URL,
    exclude_region_prefixes: Optional[list] = None,
    output_path: Optional[str] = None,
) -> pd.DataFrame:
    """
    시군구 간 비용행렬 생성.

    Args:
        osrm_url: OSRM 서버 주소
        exclude_region_prefixes: 제외할 sub_region_code prefix (예: ["JEJ"])
        output_path: 저장 경로 (None이면 기본 경로)

    Returns:
        비용행렬 DataFrame
    """
    sg_df = load_sigungu_master(exclude_prefixes=exclude_region_prefixes)
    n = len(sg_df)
    total = n * (n - 1)
    print(f"시군구 {n}개 → {total}쌍 조회")

    codes = sg_df["sub_region_code"].tolist()
    names = (sg_df["광역도시"] + " " + sg_df["시군구"]).tolist()
    lons = sg_df["lon"].tolist()
    lats = sg_df["lat"].tolist()

    rows = []
    count = 0
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            count += 1
            if count % 1000 == 0:
                print(f"  진행: {count}/{total}")

            result = query_osrm_route(
                lons[i], lats[i], lons[j], lats[j],
                osrm_url=osrm_url,
            )
            rows.append({
                "from_code": codes[i],
                "from_name": names[i],
                "to_code": codes[j],
                "to_name": names[j],
                "duration_min": round(result["duration"] / 60, 1) if result["duration"] else None,
                "distance_km": round(result["distance"] / 1000, 1) if result["distance"] else None,
            })

    df = pd.DataFrame(rows)

    if output_path is None:
        output_path = WEMEET_DIR / "sigungu_matrix.csv"
    df.to_csv(output_path, index=False)
    print(f"\n저장 완료: {output_path} ({len(df)}행)")

    return df


if __name__ == "__main__":
    df = generate_sigungu_matrix(exclude_region_prefixes=["JEJ"])
    print(f"\n샘플:")
    print(df.head(10).to_string())
