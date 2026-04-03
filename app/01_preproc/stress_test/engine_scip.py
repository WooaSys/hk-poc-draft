"""
SCIP(MIP) Solver 엔진 (engine_scip.py)

목적:
    OR-Tools Linear Solver + SCIP backend를 사용하여
    Capacitated Assignment Problem을 풀고 결과를 반환한다.
    해석 및 검증 기준 모델.

사용법:
    from stress_test.engine_scip import solve_scip
    result = solve_scip(problem, scenario, baseline_cost=None)
"""

import time

from ortools.linear_solver import pywraplp

from .common import ProblemData, Scenario, ScenarioResult, build_result


def solve_scip(
    problem: ProblemData,
    scenario: Scenario,
    baseline_cost: float | None = None,
    baseline_distance: float | None = None,
    isolation_penalty: float = 0.0,
) -> ScenarioResult:
    """
    SCIP solver로 Capacitated Assignment 문제 풀기.

    Args:
        problem: 문제 데이터
        scenario: 시나리오 (capacity)
        baseline_cost: Baseline 총비용 (증가율 계산용)
        isolation_penalty: 고립 패널티 강도 (0이면 비활성)

    Returns:
        ScenarioResult
    """
    start = time.time()

    solver = pywraplp.Solver.CreateSolver("SCIP")
    if not solver:
        return ScenarioResult(
            scenario_id=scenario.scenario_id,
            solver_type="scip",
            status="error_no_solver",
            total_cost=0, cost_increase_pct=0, assignment=[],
        )

    n_s = problem.n_sigungu
    n_r = problem.n_rdc

    # 변수: x[i][j] = 시군구 i를 RDC j에 배정 (이진)
    x = []
    for i in range(n_s):
        row = []
        for j in range(n_r):
            row.append(solver.IntVar(0, 1, f"x_{i}_{j}"))
        x.append(row)

    # 제약 1: 단일 배정
    for i in range(n_s):
        solver.Add(sum(x[i][j] for j in range(n_r)) == 1)

    # 제약 1.5: 고정 배정 (섬 지역 등)
    for i, j in problem.fixed_assignment.items():
        solver.Add(x[i][j] == 1)

    # 제약 2: RDC capacity
    for j in range(n_r):
        solver.Add(
            sum(problem.demand[i] * x[i][j] for i in range(n_s)) <= scenario.capacity[j]
        )

    # 목적함수: min Σ(d_i × c_ij × x_ij)
    objective = solver.Sum(
        problem.demand[i] * problem.cost[i][j] * x[i][j]
        for i in range(n_s)
        for j in range(n_r)
    )
    solver.Minimize(objective)

    # 풀기
    solver.SetTimeLimit(60_000)  # 60초 제한
    result_status = solver.Solve()

    elapsed = time.time() - start

    # 상태 매핑
    if result_status == pywraplp.Solver.OPTIMAL:
        status = "optimal"
    elif result_status == pywraplp.Solver.FEASIBLE:
        status = "feasible"
    else:
        status = "infeasible"

    # 배정 추출
    assignment = []
    if status in ("optimal", "feasible"):
        for i in range(n_s):
            for j in range(n_r):
                if x[i][j].solution_value() > 0.5:
                    assignment.append(j)
                    break
            else:
                assignment.append(0)
    else:
        assignment = list(problem.current_rdc_idx)  # infeasible 시 현재 배정 유지

    return build_result(
        problem=problem,
        scenario=scenario,
        solver_type="scip",
        assignment=assignment,
        status=status,
        runtime_sec=elapsed,
        baseline_cost=baseline_cost,
        baseline_distance=baseline_distance,
    )
