"""
VROOM API 클라이언트 (vroom_client.py)

목적:
    VROOM 서버에 배차 요청을 보내고 결과를 반환한다.
    차량(vehicles)과 작업(jobs)을 구성하여 배차 최적화를 수행.

입력:
    - vehicles: RDC 위치, capacity
    - jobs: 시군구 위치, demand

출력:
    - VROOM 응답 JSON (routes, unassigned 등)

사용법:
    from vroom_engine.vroom_client import request_vroom
    result = request_vroom(vehicles, jobs, vroom_url="http://localhost:3000")
"""

import requests

DEFAULT_VROOM_URL = "http://localhost:3000"

# VROOM은 정수 기반 — demand/capacity 스케일링
SCALE = 1000


def request_vroom(
    vehicles: list[dict],
    jobs: list[dict],
    vroom_url: str = DEFAULT_VROOM_URL,
) -> dict:
    """
    VROOM API 호출.

    Args:
        vehicles: [{"id": 1, "start": [lon, lat], "capacity": [1000]}]
        jobs: [{"id": 1, "location": [lon, lat], "delivery": [425]}]
        vroom_url: VROOM 서버 주소

    Returns:
        VROOM 응답 dict
    """
    payload = {
        "vehicles": vehicles,
        "jobs": jobs,
    }
    resp = requests.post(vroom_url, json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json()


def build_vroom_request(
    rdc_lon: float,
    rdc_lat: float,
    vehicle_count: int,
    sigungu_list: list[dict],
) -> tuple[list[dict], list[dict]]:
    """
    단일 RDC에 대한 VROOM vehicles/jobs 구성.

    Args:
        rdc_lon, rdc_lat: RDC 좌표
        vehicle_count: 차량 수
        sigungu_list: [{"id": int, "lon": float, "lat": float, "demand": float, "code": str, "name": str}]

    Returns:
        (vehicles, jobs)
    """
    vehicles = []
    for v in range(vehicle_count):
        vehicles.append({
            "id": v + 1,
            "start": [rdc_lon, rdc_lat],
            "end": [rdc_lon, rdc_lat],
            "capacity": [SCALE],  # 만적 100% = 1000
        })

    jobs = []
    job_id = 1
    for sg in sigungu_list:
        total_scaled = max(1, int(round(sg["demand"] * SCALE)))

        # capacity(1000) 초과 시 여러 job으로 분할
        remaining = total_scaled
        while remaining > 0:
            chunk = min(remaining, SCALE)
            jobs.append({
                "id": job_id,
                "location": [sg["lon"], sg["lat"]],
                "delivery": [chunk],
                "_sg_idx": sg["id"],  # 원본 시군구 참조용 (VROOM은 무시)
            })
            remaining -= chunk
            job_id += 1

    return vehicles, jobs
