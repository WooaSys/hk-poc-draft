# Capacity Stress Test 엔진 작업 목록

- **작성시간**: 2026-04-02
- **주제**: Dual Solver 엔진 구현 (SCIP + CP-SAT)
- **참조 Plan**: `01_plan/07_capacity_stress_test.md`

## 요약

공통 모듈 + SCIP/CP-SAT 엔진 + runner + comparator 순서로 구현. 화면은 별도 작업.

## 작업 목록

- [x] 1. `stress_test/common.py` — 데이터 로드, 시나리오 생성, 결과 포맷
- [x] 2. `stress_test/engine_scip.py` — SCIP solver
- [x] 3. `stress_test/engine_cpsat.py` — CP-SAT solver
- [x] 4. `stress_test/runner.py` — solver 선택 + 시나리오 루프
- [x] 5. `stress_test/comparator.py` — 두 solver 결과 비교
- [x] 6. Phase 1 검증 (전체 247개 시군구 × 4 RDC)
- [x] 7. 결과 문서 작성
