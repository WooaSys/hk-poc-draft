"""
Solver 비교 모듈 (comparator.py)

목적:
    SCIP와 CP-SAT 결과를 비교하여 모델 정확성을 검증한다.

사용법:
    from stress_test.comparator import compare_solvers
    comparison = compare_solvers(problem=problem, scenarios=scenarios)
"""

import pandas as pd

from .common import ProblemData, Scenario, ScenarioResult
from .runner import run_stress_test


def compare_solvers(
    problem: ProblemData,
    scenarios: list[Scenario],
) -> pd.DataFrame:
    """
    두 solver 결과 비교.

    Returns:
        시나리오별 비교 DataFrame
    """
    print("=== SCIP 실행 ===")
    scip_results = run_stress_test(problem, scenarios, solver_type="scip")

    print("\n=== CP-SAT 실행 ===")
    cpsat_results = run_stress_test(problem, scenarios, solver_type="cpsat")

    rows = []
    for sr, cr in zip(scip_results, cpsat_results):
        # 배정 일치율
        match_count = sum(
            1 for a, b in zip(sr.assignment, cr.assignment) if a == b
        )
        match_pct = round(match_count / len(sr.assignment) * 100, 1) if sr.assignment else 0

        # 목적값 차이
        cost_diff = round(abs(sr.total_cost - cr.total_cost), 1)
        cost_diff_pct = round(cost_diff / sr.total_cost * 100, 3) if sr.total_cost > 0 else 0

        rows.append({
            "scenario": sr.scenario_id,
            "scip_status": sr.status,
            "cpsat_status": cr.status,
            "scip_cost": sr.total_cost,
            "cpsat_cost": cr.total_cost,
            "cost_diff": cost_diff,
            "cost_diff_pct": cost_diff_pct,
            "assignment_match_pct": match_pct,
            "scip_moved": len(sr.moved_detail),
            "cpsat_moved": len(cr.moved_detail),
            "scip_runtime": sr.runtime_sec,
            "cpsat_runtime": cr.runtime_sec,
        })

    df = pd.DataFrame(rows)

    print("\n=== 비교 결과 ===")
    print(df.to_string())

    # 판정
    for _, row in df.iterrows():
        sid = row["scenario"]
        if row["scip_status"] != row["cpsat_status"]:
            print(f"  ⚠️ {sid}: 상태 불일치 ({row['scip_status']} vs {row['cpsat_status']})")
        elif row["cost_diff_pct"] > 0.1:
            print(f"  ⚠️ {sid}: 목적값 차이 {row['cost_diff_pct']}% — 스케일링/모델 확인 필요")
        elif row["assignment_match_pct"] < 100:
            print(f"  ℹ️ {sid}: 목적값 동일, 배정 {row['assignment_match_pct']}% 일치 (동률 최적해)")
        else:
            print(f"  ✅ {sid}: 완전 일치")

    return df
