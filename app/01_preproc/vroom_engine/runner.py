"""
VROOM 배차 실행 모듈 (runner.py)

목적:
    RDC별로 VROOM 배차를 실행하고, 거리 보정 + 비용 산출 후
    결과를 집계하여 JSON 파일로 저장한다.

입력:
    - 시군구 수요 (app/db/sigungu_demand.csv)
    - 시군구 좌표 (app/db/sigungu_master.csv)
    - RDC 위치 (app/db/rdc_locations.json)
    - RDC-시군구 배정 (assignment 리스트 또는 shipto_master)

출력:
    - app/db/vroom_results/{scenario_id}.json

사용법:
    from vroom_engine.runner import run_vroom_scenario

    result = run_vroom_scenario(
        scenario_id="baseline",
        assignment_map={"GWO_GR": "칠곡RDC", ...},
    )
"""

import json
import math
from pathlib import Path
from typing import Optional

import pandas as pd

from .vroom_client import build_vroom_request, request_vroom, SCALE
from .cost_calculator import calculate_route_cost, load_price_map

APP_DIR = Path(__file__).resolve().parent.parent.parent
DB_DIR = APP_DIR / "db"
RESULTS_DIR = DB_DIR / "vroom_results"


def _load_data():
    """공통 데이터 로드."""
    demand_df = pd.read_csv(DB_DIR / "sigungu_demand.csv")
    sigungu_df = pd.read_csv(DB_DIR / "sigungu_master.csv")
    with open(DB_DIR / "rdc_locations.json", "r", encoding="utf-8") as f:
        rdc_locs = json.load(f)
    return demand_df, sigungu_df, rdc_locs


def _get_current_assignment_map() -> dict:
    """현 상태 시군구→RDC 매핑 (보정 데이터 기준)."""
    shipto = pd.read_csv(DB_DIR / "shipto_master_corrected.csv")
    shipto["Ship-to party"] = shipto["Ship-to party"].astype(str)
    current = (
        shipto.groupby(["sub_region_code", "담당 RDC 명"])["Ship-to party"]
        .nunique().reset_index()
    )
    current.columns = ["sub_region_code", "rdc_name", "count"]
    idx = current.groupby("sub_region_code")["count"].idxmax()
    main = current.loc[idx][["sub_region_code", "rdc_name"]]
    return dict(zip(main["sub_region_code"], main["rdc_name"]))


def run_vroom_scenario(
    scenario_id: str,
    assignment_map: Optional[dict] = None,
    include_jungbu: bool = False,
    vroom_url: str = "http://localhost:3000",
    save: bool = True,
) -> dict:
    """
    시나리오별 VROOM 배차 실행.

    Args:
        scenario_id: 시나리오 ID (파일명에 사용)
        assignment_map: {sub_region_code: rdc_name} (None이면 현 상태)
        include_jungbu: 중부RDC 포함 여부
        vroom_url: VROOM 서버 주소
        save: 결과 파일 저장 여부

    Returns:
        결과 dict
    """
    demand_df, sigungu_df, rdc_locs = _load_data()

    if assignment_map is None:
        assignment_map = _get_current_assignment_map()

    # 제주 제외
    demand_df = demand_df[~demand_df["sub_region_code"].str.startswith("JEJ")]
    sigungu_df = sigungu_df[~sigungu_df["sub_region_code"].str.startswith("JEJ")]

    # 시군구별 수요 + 좌표 병합
    merged = demand_df.merge(
        sigungu_df[["sub_region_code", "시군구", "광역도시", "lon", "lat"]],
        on="sub_region_code", how="left",
    )
    merged["rdc_name"] = merged["sub_region_code"].map(assignment_map)
    merged = merged[merged["rdc_name"].notna()]

    if not include_jungbu:
        merged = merged[merged["rdc_name"] != "중부RDC"]

    # RDC별 실행
    price_map = load_price_map("3.5T")
    rdc_results = []

    for rdc in rdc_locs:
        rdc_name = rdc["name"]
        if rdc_name == "제주RDC":
            continue
        if not include_jungbu and rdc_name == "중부RDC":
            continue

        rdc_sigungu = merged[merged["rdc_name"] == rdc_name].copy()
        if len(rdc_sigungu) == 0:
            continue

        total_demand = rdc_sigungu["daily_demand_3_5t"].sum()
        vehicle_count = max(1, math.ceil(total_demand))

        # VROOM 요청 구성
        sg_list = []
        for idx, (_, row) in enumerate(rdc_sigungu.iterrows()):
            sg_list.append({
                "id": idx + 1,
                "lon": row["lon"],
                "lat": row["lat"],
                "demand": row["daily_demand_3_5t"],
                "code": row["sub_region_code"],
                "name": f"{row['광역도시']} {row['시군구']}",
            })

        vehicles, jobs = build_vroom_request(
            rdc["lon"], rdc["lat"], vehicle_count, sg_list,
        )

        # job_id → 시군구 매핑 (분할된 job 대응)
        job_to_sg = {}
        for job in jobs:
            job_to_sg[job["id"]] = job.get("_sg_idx", job["id"])

        print(f"  {rdc_name}: 시군구 {len(sg_list)}개, job {len(jobs)}개, 차량 {vehicle_count}대...")

        # VROOM에 보낼 때 _sg_idx 제거 (VROOM이 모르는 필드)
        clean_jobs = [{k: v for k, v in j.items() if k != "_sg_idx"} for j in jobs]
        vroom_resp = request_vroom(vehicles, clean_jobs, vroom_url=vroom_url)

        # 결과 파싱
        unassigned = vroom_resp.get("unassigned", [])
        if unassigned:
            print(f"    ⚠️ unassigned: {len(unassigned)}건")

        routes = []
        rdc_total_cost = 0
        rdc_total_osrm_km = 0
        rdc_total_corrected_km = 0

        for route in vroom_resp.get("routes", []):
            route_km = route["distance"] / 1000  # m → km
            route_duration = route["duration"] / 60  # s → min
            route_delivery = route.get("delivery", [0])[0] / SCALE if route.get("delivery") else 0

            # 방문 시군구 목록 (중복 제거 — 분할 job이 같은 시군구)
            stops = []
            seen = set()
            for step in route["steps"]:
                if step["type"] == "job":
                    job_id = step["id"]
                    sg_idx = job_to_sg.get(job_id, job_id)
                    sg = sg_list[sg_idx - 1]
                    if sg["name"] not in seen:
                        stops.append(sg["name"])
                        seen.add(sg["name"])

            # 비용 산출
            cost_info = calculate_route_cost(rdc_name, route_km, price_map)

            rdc_total_cost += cost_info["cost"]
            rdc_total_osrm_km += route_km
            rdc_total_corrected_km += cost_info["corrected_km"]

            routes.append({
                "vehicle_id": route["vehicle"],
                "stops": stops,
                "stop_count": len(stops),
                "osrm_km": round(route_km, 1),
                "corrected_km": cost_info["corrected_km"],
                "duration_min": round(route_duration, 1),
                "utilization": round(route_delivery, 3),
                "price_range": cost_info["price_range"],
                "cost": cost_info["cost"],
            })

        rdc_results.append({
            "rdc_name": rdc_name,
            "sigungu_count": len(sg_list),
            "vehicle_count": vehicle_count,
            "total_demand": round(total_demand, 1),
            "total_cost": rdc_total_cost,
            "total_osrm_km": round(rdc_total_osrm_km, 1),
            "total_corrected_km": round(rdc_total_corrected_km, 1),
            "unassigned_count": len(unassigned),
            "routes": routes,
        })

        print(f"    → {len(routes)}경로, 비용 {rdc_total_cost:,.0f}원")

    # 전체 집계
    total_cost = sum(r["total_cost"] for r in rdc_results)
    total_vehicles = sum(r["vehicle_count"] for r in rdc_results)
    total_routes = sum(len(r["routes"]) for r in rdc_results)

    result = {
        "scenario_id": scenario_id,
        "total_cost": total_cost,
        "total_vehicles": total_vehicles,
        "total_routes": total_routes,
        "rdc_results": rdc_results,
        "params": {
            "include_jungbu": include_jungbu,
            "truck_type": "3.5T",
            "price_base": "2025년 11월",
        },
    }

    # 저장
    if save:
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        path = RESULTS_DIR / f"{scenario_id}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n저장: {path}")

    print(f"\n총 비용: {total_cost:,.0f}원, 차량: {total_vehicles}대, 경로: {total_routes}개")
    return result


if __name__ == "__main__":
    print("=== 현 상태 (baseline) VROOM 배차 ===")
    result = run_vroom_scenario(scenario_id="baseline")
