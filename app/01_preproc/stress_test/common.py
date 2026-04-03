"""
Capacity Stress Test 공통 모듈 (common.py)

목적:
    데이터 로드, 시나리오 생성, 결과 포맷 등 solver와 무관한 공통 로직을 제공한다.
    SCIP/CP-SAT 엔진이 동일한 입력/출력 구조를 사용하도록 보장한다.

입력:
    - app/db/sigungu_demand.csv
    - app/db/cost_matrix.csv
    - app/db/shipto_master_corrected.csv (보정 데이터)

출력:
    - ProblemData, Scenario, ScenarioResult 데이터 클래스
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import pandas as pd

APP_DIR = Path(__file__).resolve().parent.parent.parent
DB_DIR = APP_DIR / "db"


# --- 데이터 클래스 ---

@dataclass
class ProblemData:
    """최적화 문제 입력 데이터."""
    sigungu_codes: list[str]       # 시군구 코드 리스트
    sigungu_names: list[str]       # 시군구명 리스트
    rdc_codes: list[str]           # RDC 코드 리스트
    rdc_names: list[str]           # RDC명 리스트
    demand: list[float]            # 시군구별 수요 (d_i)
    cost: list[list[float]]        # 비용행렬 [i][j] = RDC j → 시군구 i 이동시간
    distance: list[list[float]]    # 거리행렬 [i][j] = RDC j → 시군구 i 거리(km)
    current_rdc_idx: list[int]     # 시군구별 현재 담당 RDC 인덱스
    adjacency: list[list[int]]     # 인접 시군구 인덱스 리스트 [i] = [k1, k2, ...]
    fixed_assignment: dict         # 고정 배정 {시군구 인덱스: RDC 인덱스} (재배치 제외)
    n_sigungu: int = 0
    n_rdc: int = 0


@dataclass
class Scenario:
    """시나리오 정의."""
    scenario_id: str
    capacity: list[float]          # RDC별 capacity


@dataclass
class ScenarioResult:
    """시나리오 실행 결과."""
    scenario_id: str
    solver_type: str
    status: str                    # optimal / feasible / infeasible
    total_cost: float              # 수요가중 이동시간 합
    total_distance: float          # 수요가중 이동거리 합
    cost_increase_pct: float       # Baseline 대비 시간 증가율
    distance_increase_pct: float   # Baseline 대비 거리 증가율
    assignment: list[int]          # 시군구별 배정 RDC 인덱스
    rdc_summary: pd.DataFrame = field(default_factory=pd.DataFrame)
    sigungu_detail: pd.DataFrame = field(default_factory=pd.DataFrame)
    moved_detail: pd.DataFrame = field(default_factory=pd.DataFrame)
    runtime_sec: float = 0.0


# --- 데이터 로드 ---

def load_problem_data(
    include_jungbu: bool = True,
    demand_col: str = "daily_demand_3_5t",
    adjacency_threshold: float = 60.0,
) -> ProblemData:
    """
    최적화 문제 입력 데이터 로드.

    Args:
        include_jungbu: 중부RDC 포함 여부
        demand_col: 수요 컬럼명 (daily_demand_3_5t 또는 daily_demand_5t)
    """
    demand_df = pd.read_csv(DB_DIR / "sigungu_demand.csv")
    cost_df = pd.read_csv(DB_DIR / "cost_matrix.csv")
    shipto_df = pd.read_csv(DB_DIR / "shipto_master_corrected.csv")

    # 제주 제외
    demand_df = demand_df[~demand_df["sub_region_code"].str.startswith("JEJ")]
    cost_df = cost_df[~cost_df["sub_region_code"].str.startswith("JEJ")]
    cost_df = cost_df[cost_df["rdc_name"] != "제주RDC"]

    # 중부RDC 제외 옵션
    if not include_jungbu:
        cost_df = cost_df[cost_df["rdc_name"] != "중부RDC"]

    # 시군구/RDC 리스트
    sigungu_codes = sorted(demand_df["sub_region_code"].unique())
    rdc_names_list = sorted(cost_df["rdc_name"].unique())
    rdc_codes_list = []
    for rn in rdc_names_list:
        rc = cost_df[cost_df["rdc_name"] == rn]["rdc_code"].iloc[0]
        rdc_codes_list.append(rc)

    n_s = len(sigungu_codes)
    n_r = len(rdc_names_list)

    # 수요 벡터
    demand_map = dict(zip(demand_df["sub_region_code"], demand_df[demand_col]))
    demand = [demand_map.get(sc, 0.0) for sc in sigungu_codes]

    # 시군구명
    name_map = dict(zip(demand_df["sub_region_code"], demand_df["sigungu_name"]))
    sigungu_names = [name_map.get(sc, sc) for sc in sigungu_codes]

    # 비용행렬 [i][j] (시간)
    cost_pivot = cost_df.pivot_table(
        index="sub_region_code", columns="rdc_name", values="duration_min",
    )
    cost_matrix = []
    for sc in sigungu_codes:
        row = []
        for rn in rdc_names_list:
            val = cost_pivot.loc[sc, rn] if sc in cost_pivot.index and rn in cost_pivot.columns else 9999.0
            row.append(float(val))
        cost_matrix.append(row)

    # 거리행렬 [i][j] (km)
    dist_pivot = cost_df.pivot_table(
        index="sub_region_code", columns="rdc_name", values="distance_km",
    )
    dist_matrix = []
    for sc in sigungu_codes:
        row = []
        for rn in rdc_names_list:
            val = dist_pivot.loc[sc, rn] if sc in dist_pivot.index and rn in dist_pivot.columns else 9999.0
            row.append(float(val))
        dist_matrix.append(row)

    # 현재 담당 RDC (시군구별 최다 배송지 RDC)
    shipto_df["Ship-to party"] = shipto_df["Ship-to party"].astype(str)
    current_rdc_map = (
        shipto_df.groupby(["sub_region_code", "담당 RDC 명"])["Ship-to party"]
        .nunique().reset_index()
    )
    current_rdc_map.columns = ["sub_region_code", "rdc_name", "count"]
    idx = current_rdc_map.groupby("sub_region_code")["count"].idxmax()
    current_main = dict(zip(
        current_rdc_map.loc[idx, "sub_region_code"],
        current_rdc_map.loc[idx, "rdc_name"],
    ))

    rdc_name_to_idx = {rn: j for j, rn in enumerate(rdc_names_list)}
    current_rdc_idx = []
    for sc in sigungu_codes:
        crn = current_main.get(sc, rdc_names_list[0])
        current_rdc_idx.append(rdc_name_to_idx.get(crn, 0))

    # 인접 리스트 생성 (shapefile 폴리곤 경계 공유 기반)
    import geopandas as gpd
    CITY_CODE_MAP = {
        "11": "서울특별시", "21": "부산광역시", "22": "대구광역시", "23": "인천광역시",
        "24": "광주광역시", "25": "대전광역시", "26": "울산광역시", "29": "세종특별자치시",
        "31": "경기도", "32": "강원도", "33": "충청북도", "34": "충청남도",
        "35": "전라북도", "36": "전라남도", "37": "경상북도", "38": "경상남도", "39": "제주특별자치도",
    }
    shp_path = Path(__file__).resolve().parent.parent.parent.parent / "raw_data" / "map" / "BND_SIGUNGU_PG.shp"
    adjacency = [[] for _ in range(n_s)]

    if shp_path.exists():
        gdf = gpd.read_file(shp_path)
        gdf["광역도시_shp"] = gdf["SIGUNGU_CD"].str[:2].map(CITY_CODE_MAP)

        # sigungu_master와 매핑하여 sub_region_code 부여
        sg_master = pd.read_csv(DB_DIR / "sigungu_master.csv")
        gdf = gdf.merge(
            sg_master[["광역도시", "시군구", "sub_region_code"]],
            left_on=["광역도시_shp", "SIGUNGU_NM"],
            right_on=["광역도시", "시군구"],
            how="left",
        )
        gdf = gdf[gdf["sub_region_code"].notna()]

        code_to_idx = {sc: i for i, sc in enumerate(sigungu_codes)}

        for idx_a, row_a in gdf.iterrows():
            sc_a = row_a["sub_region_code"]
            i = code_to_idx.get(sc_a)
            if i is None:
                continue
            for idx_b, row_b in gdf.iterrows():
                if idx_a >= idx_b:
                    continue
                sc_b = row_b["sub_region_code"]
                k = code_to_idx.get(sc_b)
                if k is None:
                    continue
                if row_a.geometry.touches(row_b.geometry) or row_a.geometry.intersects(row_b.geometry):
                    adjacency[i].append(k)
                    adjacency[k].append(i)

    # 고정 배정: 섬 지역 등 재배치 제외 대상
    fixed_assignment = {}
    # 울릉군 → 칠곡RDC 고정
    if "GSB_OR" in code_to_idx and "칠곡RDC" in rdc_name_to_idx:
        fixed_assignment[code_to_idx["GSB_OR"]] = rdc_name_to_idx["칠곡RDC"]

    return ProblemData(
        sigungu_codes=sigungu_codes,
        sigungu_names=sigungu_names,
        rdc_codes=rdc_codes_list,
        rdc_names=rdc_names_list,
        demand=demand,
        cost=cost_matrix,
        distance=dist_matrix,
        current_rdc_idx=current_rdc_idx,
        adjacency=adjacency,
        fixed_assignment=fixed_assignment,
        n_sigungu=n_s,
        n_rdc=n_r,
    )


# --- 시나리오 생성 ---

def create_scenarios(
    problem: ProblemData,
    target_rdc: str | list[str] = "평택RDC",
    reduction_ratios: list[float] | None = None,
    receiver_buffer: float = 1.2,
) -> list[Scenario]:
    """
    시나리오 생성.

    Args:
        problem: 문제 데이터
        target_rdc: 축소 대상 RDC 이름 (문자열 또는 리스트)
        reduction_ratios: 축소 비율 리스트 (기본: [0, 0.05, 0.10, 0.15, 0.20])
        receiver_buffer: 수용 RDC 상한 배율 (기본 1.2 = 120%)
    """
    if reduction_ratios is None:
        reduction_ratios = [0.0, 0.05, 0.10, 0.15, 0.20]

    if isinstance(target_rdc, str):
        target_rdc = [target_rdc]

    # 현재 RDC별 load 산출
    current_load = [0.0] * problem.n_rdc
    for i in range(problem.n_sigungu):
        j = problem.current_rdc_idx[i]
        current_load[j] += problem.demand[i]

    # 수용 RDC capacity: 전체 수요 균등 분배 기준 × 버퍼
    total_demand = sum(problem.demand)
    equal_share = total_demand / problem.n_rdc  # RDC당 균등 몫

    scenarios = []
    for ratio in reduction_ratios:
        caps = []
        for j, rn in enumerate(problem.rdc_names):
            if rn in target_rdc:
                caps.append(current_load[j] * (1.0 - ratio))
            else:
                caps.append(equal_share * receiver_buffer)
        sid = f"S{int(ratio * 100):02d}"
        scenarios.append(Scenario(scenario_id=sid, capacity=caps))

    return scenarios


# --- 고립 해소 (후처리) ---

def resolve_isolation(problem: ProblemData, assignment: list[int]) -> list[int]:
    """
    고립 시군구를 인접 시군구의 다수 RDC로 재배정.

    고립 판단: 인접 시군구 중 같은 RDC가 없는 경우
    재배정: 인접 시군구에서 가장 많이 배정된 RDC로 변경
    """
    result = list(assignment)
    changed = True

    while changed:
        changed = False
        for i in range(problem.n_sigungu):
            adj = problem.adjacency[i]
            if not adj:
                continue

            my_rdc = result[i]
            adj_rdcs = [result[k] for k in adj]

            # 내 RDC가 인접에 하나도 없으면 고립
            if my_rdc not in adj_rdcs:
                # 인접에서 가장 많은 RDC
                from collections import Counter
                rdc_counts = Counter(adj_rdcs)
                majority_rdc = rdc_counts.most_common(1)[0][0]
                result[i] = majority_rdc
                changed = True

    return result


# --- 배송 비용 산출 ---

def load_price_table(truck_type: str = "3.5T") -> pd.DataFrame:
    """배송 단가표 로드."""
    df = pd.read_csv(DB_DIR / "delivery_price_202511.csv")
    return df[df["truck_type"] == truck_type].copy()


def _distance_to_range(km: float) -> str:
    """거리(km)를 단가표 거리구간으로 변환."""
    bins = [
        (10, "1~10 km"), (20, "11~20 km"), (30, "21~30 km"),
        (40, "31~40 km"), (50, "41~50 km"), (60, "51~60 km"),
        (70, "61~70 km"), (80, "71~80 km"), (90, "81~90 km"),
        (100, "91~100 km"), (120, "101~120 km"), (140, "121~140 km"),
        (160, "141~160 km"), (180, "161~180 km"), (200, "181~200 km"),
        (230, "201~230 km"), (260, "231~260 km"), (290, "261~290 km"),
        (320, "291~320 km"), (350, "321~350 km"),
    ]
    for upper, label in bins:
        if km <= upper:
            return label
    return "321~350 km"  # 최대 구간


def calculate_delivery_cost(
    problem: ProblemData,
    assignment: list[int],
    truck_type: str = "3.5T",
) -> pd.DataFrame:
    """
    배정 결과에 대한 배송 비용 산출.

    각 시군구의 수요(대수) × 해당 RDC-시군구 거리구간 단가 = 비용.

    Returns:
        RDC별 비용 요약 DataFrame
    """
    price_df = load_price_table(truck_type)
    # RDC × 거리구간 → 단가 딕셔너리
    price_map = {}
    for _, row in price_df.iterrows():
        price_map[(row["rdc_name"], row["distance_range"])] = row["price"]

    rdc_costs = {rn: 0.0 for rn in problem.rdc_names}
    rdc_trips = {rn: 0.0 for rn in problem.rdc_names}

    for i in range(problem.n_sigungu):
        j = assignment[i]
        rdc_name = problem.rdc_names[j]
        dist_km = problem.distance[i][j]
        demand = problem.demand[i]  # 3.5T 환산 대수

        dist_range = _distance_to_range(dist_km)
        unit_price = price_map.get((rdc_name, dist_range), 0)

        # 비용 = 수요(대수) × 단가(1대당)
        cost = demand * unit_price
        rdc_costs[rdc_name] += cost
        rdc_trips[rdc_name] += demand

    result = pd.DataFrame({
        "rdc_name": list(rdc_costs.keys()),
        "total_cost": [round(v) for v in rdc_costs.values()],
        "total_trips": [round(v, 1) for v in rdc_trips.values()],
    })
    result["avg_cost_per_trip"] = (result["total_cost"] / result["total_trips"]).round(0).fillna(0).astype(int)

    return result


# --- 결과 생성 ---

def build_result(
    problem: ProblemData,
    scenario: Scenario,
    solver_type: str,
    assignment: list[int],
    status: str,
    runtime_sec: float,
    baseline_cost: float | None = None,
    baseline_distance: float | None = None,
) -> ScenarioResult:
    """solver 출력으로부터 ScenarioResult 생성."""
    # 총 이동시간
    total_cost = sum(
        problem.demand[i] * problem.cost[i][assignment[i]]
        for i in range(problem.n_sigungu)
    )

    # 총 이동거리
    total_distance = sum(
        problem.demand[i] * problem.distance[i][assignment[i]]
        for i in range(problem.n_sigungu)
    )

    # 시간 증가율
    if baseline_cost and baseline_cost > 0:
        cost_increase_pct = (total_cost - baseline_cost) / baseline_cost * 100
    else:
        cost_increase_pct = 0.0

    # 거리 증가율
    if baseline_distance and baseline_distance > 0:
        distance_increase_pct = (total_distance - baseline_distance) / baseline_distance * 100
    else:
        distance_increase_pct = 0.0

    # RDC 요약
    rdc_load = [0.0] * problem.n_rdc
    rdc_count = [0] * problem.n_rdc
    for i in range(problem.n_sigungu):
        j = assignment[i]
        rdc_load[j] += problem.demand[i]
        rdc_count[j] += 1

    rdc_summary = pd.DataFrame({
        "rdc_name": problem.rdc_names,
        "capacity": scenario.capacity,
        "assigned_load": [round(l, 1) for l in rdc_load],
        "sigungu_count": rdc_count,
        "utilization_pct": [round(l / c * 100, 1) if c > 0 else 0 for l, c in zip(rdc_load, scenario.capacity)],
    })

    # 시군구 상세
    rows = []
    for i in range(problem.n_sigungu):
        cur_j = problem.current_rdc_idx[i]
        new_j = assignment[i]
        rows.append({
            "sub_region_code": problem.sigungu_codes[i],
            "sigungu_name": problem.sigungu_names[i],
            "demand": problem.demand[i],
            "current_rdc": problem.rdc_names[cur_j],
            "assigned_rdc": problem.rdc_names[new_j],
            "moved": cur_j != new_j,
            "current_time": problem.cost[i][cur_j],
            "assigned_time": problem.cost[i][new_j],
            "delta_time": round(problem.cost[i][new_j] - problem.cost[i][cur_j], 1),
            "current_distance": problem.distance[i][cur_j],
            "assigned_distance": problem.distance[i][new_j],
            "delta_distance": round(problem.distance[i][new_j] - problem.distance[i][cur_j], 1),
        })
    sigungu_detail = pd.DataFrame(rows)

    # 이동 상세
    moved_detail = sigungu_detail[sigungu_detail["moved"]].copy()

    return ScenarioResult(
        scenario_id=scenario.scenario_id,
        solver_type=solver_type,
        status=status,
        total_cost=round(total_cost, 1),
        total_distance=round(total_distance, 1),
        cost_increase_pct=round(cost_increase_pct, 2),
        distance_increase_pct=round(distance_increase_pct, 2),
        assignment=assignment,
        rdc_summary=rdc_summary,
        sigungu_detail=sigungu_detail,
        moved_detail=moved_detail,
        runtime_sec=round(runtime_sec, 3),
    )
