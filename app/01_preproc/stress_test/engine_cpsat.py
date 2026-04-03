"""
CP-SAT Solver 엔진 (engine_cpsat.py)

목적:
    OR-Tools CP-SAT solver를 사용하여
    Capacitated Assignment Problem을 풀고 결과를 반환한다.
    검증 모델 및 대규모 확장 시 성능 비교 대상.

    CP-SAT은 정수 기반이므로 demand/cost를 스케일링하여 정수로 변환.
    스케일링 정책: demand ×100, time ×10

사용법:
    from stress_test.engine_cpsat import solve_cpsat
    result = solve_cpsat(problem, scenario, baseline_cost=None)
"""

import time

from ortools.sat.python import cp_model

from .common import ProblemData, Scenario, ScenarioResult, build_result

# 스케일링 팩터
DEMAND_SCALE = 100   # 소수점 2자리 보존
TIME_SCALE = 10      # 소수점 1자리 보존


def solve_cpsat(
    problem: ProblemData,
    scenario: Scenario,
    baseline_cost: float | None = None,
    baseline_distance: float | None = None,
    isolation_penalty: float = 0.0,
) -> ScenarioResult:
    """
    CP-SAT solver로 Capacitated Assignment 문제 풀기.

    Args:
        problem: 문제 데이터
        scenario: 시나리오 (capacity)
        baseline_cost: Baseline 총비용 (증가율 계산용)
        isolation_penalty: 고립 패널티 강도 (0이면 비활성)

    Returns:
        ScenarioResult
    """
    start = time.time()

    model = cp_model.CpModel()

    n_s = problem.n_sigungu
    n_r = problem.n_rdc

    # 스케일링된 값
    scaled_demand = [int(round(d * DEMAND_SCALE)) for d in problem.demand]
    scaled_cost = [
        [int(round(problem.cost[i][j] * TIME_SCALE)) for j in range(n_r)]
        for i in range(n_s)
    ]
    scaled_capacity = [int(round(c * DEMAND_SCALE)) for c in scenario.capacity]

    # 변수: x[i][j] = 시군구 i를 RDC j에 배정 (BoolVar)
    x = []
    for i in range(n_s):
        row = []
        for j in range(n_r):
            row.append(model.new_bool_var(f"x_{i}_{j}"))
        x.append(row)

    # 제약 1: 단일 배정
    for i in range(n_s):
        model.add_exactly_one(x[i][j] for j in range(n_r))

    # 제약 1.5: 고정 배정 (섬 지역 등)
    for i, j in problem.fixed_assignment.items():
        model.add(x[i][j] == 1)

    # 제약 2: RDC capacity (스케일링된 값)
    for j in range(n_r):
        model.add(
            sum(scaled_demand[i] * x[i][j] for i in range(n_s)) <= scaled_capacity[j]
        )

    # 목적함수: min Σ(scaled_d_i × scaled_c_ij × x_ij)
    model.minimize(
        sum(
            scaled_demand[i] * scaled_cost[i][j] * x[i][j]
            for i in range(n_s)
            for j in range(n_r)
        )
    )

    # 풀기
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 60.0
    result_status = solver.solve(model)

    elapsed = time.time() - start

    # 상태 매핑
    if result_status == cp_model.OPTIMAL:
        status = "optimal"
    elif result_status == cp_model.FEASIBLE:
        status = "feasible"
    else:
        status = "infeasible"

    # 배정 추출
    assignment = []
    if status in ("optimal", "feasible"):
        for i in range(n_s):
            for j in range(n_r):
                if solver.value(x[i][j]):
                    assignment.append(j)
                    break
            else:
                assignment.append(0)
    else:
        assignment = list(problem.current_rdc_idx)  # infeasible 시 현재 배정 유지

    return build_result(
        problem=problem,
        scenario=scenario,
        solver_type="cpsat",
        assignment=assignment,
        status=status,
        runtime_sec=elapsed,
        baseline_cost=baseline_cost,
        baseline_distance=baseline_distance,
    )
