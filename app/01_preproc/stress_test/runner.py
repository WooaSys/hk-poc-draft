"""
Stress Test 실행 모듈 (runner.py)

목적:
    solver_type을 선택하고 시나리오를 순차 실행하여 결과를 반환한다.

사용법:
    from stress_test.runner import run_stress_test

    results = run_stress_test(solver_type="scip", scenarios=scenarios, problem=problem)
    results = run_stress_test(solver_type="cpsat", scenarios=scenarios, problem=problem)
"""

from .common import ProblemData, Scenario, ScenarioResult, resolve_isolation, build_result
from .engine_scip import solve_scip
from .engine_cpsat import solve_cpsat


SOLVER_MAP = {
    "scip": solve_scip,
    "cpsat": solve_cpsat,
}


def run_stress_test(
    problem: ProblemData,
    scenarios: list[Scenario],
    solver_type: str = "scip",
    isolation_penalty: float = 0.0,
) -> list[ScenarioResult]:
    """
    시나리오 루프 실행.

    Args:
        problem: 문제 데이터
        scenarios: 시나리오 리스트
        solver_type: "scip" 또는 "cpsat"
        isolation_penalty: 고립 패널티 강도 (0이면 비활성)

    Returns:
        시나리오별 ScenarioResult 리스트
    """
    if solver_type not in SOLVER_MAP:
        raise ValueError(f"Unknown solver_type: {solver_type}. Use 'scip' or 'cpsat'.")

    solve_fn = SOLVER_MAP[solver_type]

    # Baseline = 실제 운영 상태 (current_rdc_idx 기준)
    baseline_cost = sum(
        problem.demand[i] * problem.cost[i][problem.current_rdc_idx[i]]
        for i in range(problem.n_sigungu)
    )
    baseline_distance = sum(
        problem.demand[i] * problem.distance[i][problem.current_rdc_idx[i]]
        for i in range(problem.n_sigungu)
    )
    print(f"  Baseline (실제 운영): time={round(baseline_cost,1)}, dist={round(baseline_distance,1)}")

    results = []

    for i, scenario in enumerate(scenarios):
        print(f"  [{solver_type}] {scenario.scenario_id} 실행 중...")

        result = solve_fn(
            problem=problem,
            scenario=scenario,
            baseline_cost=baseline_cost,
            baseline_distance=baseline_distance,
        )

        # 고립 해소 후처리
        if isolation_penalty > 0 and result.status in ("optimal", "feasible"):
            fixed_assignment = resolve_isolation(problem, result.assignment)
            if fixed_assignment != result.assignment:
                result = build_result(
                    problem=problem,
                    scenario=scenario,
                    solver_type=result.solver_type,
                    assignment=fixed_assignment,
                    status=result.status,
                    runtime_sec=result.runtime_sec,
                    baseline_cost=baseline_cost,
                    baseline_distance=baseline_distance,
                )

        # 실제 운영 대비 증가율 계산
        if baseline_cost and baseline_cost > 0:
            result.cost_increase_pct = round(
                (result.total_cost - baseline_cost) / baseline_cost * 100, 2
            )
        if baseline_distance and baseline_distance > 0:
            result.distance_increase_pct = round(
                (result.total_distance - baseline_distance) / baseline_distance * 100, 2
            )

        results.append(result)
        print(f"    → {result.status}, time={result.total_cost}(+{result.cost_increase_pct}%), "
              f"dist={result.total_distance}(+{result.distance_increase_pct}%), "
              f"moved={len(result.moved_detail)}, runtime={result.runtime_sec}s")

    return results
