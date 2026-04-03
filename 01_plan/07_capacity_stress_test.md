# OR-Tools 기반 Capacity Stress Test 모델 설계

- **작성시간**: 2026-04-02 (수정: 04-02 20:00)
- **주제**: 특정 RDC 처리 비중 축소 시 영향도 분석 모델 (Dual Solver)
- **참조**: `00_draft/26_분석방향_전환_capacity_stress_test.md`

---

## 1. 모델 목적

특정 RDC 의존도를 낮출 때의 영향도를 정량적으로 분석.

- 특정 RDC(평택)의 처리량을 5~20% 줄였을 때 어떤 시군구가 이동하는가
- 총 이동시간 증가량, knee point 도출
- 다른 RDC의 흡수 구조 분석

**추가 목적**: SCIP(MIP)와 CP-SAT 두 solver를 병행하여 모델 검증 및 solver 비교.

---

## 2. 문제 유형

**Capacitated Assignment Problem** — RDC 고정, 배정만 결정.

---

## 3. 엔진 아키텍처

### 설계 원칙

- **공통 모듈**: 데이터 로드, 시나리오 생성, 결과 산출은 solver와 무관하게 공통화
- **Solver 엔진**: solver_type 파라미터로 SCIP/CP-SAT 전환
- **결과 비교**: 두 solver 결과를 동일한 포맷으로 출력하여 비교 가능

### 모듈 구조

```
app/01_preproc/
├── stress_test/
│   ├── __init__.py
│   ├── common.py          ← 공통: 데이터 로드, 시나리오 생성, 결과 포맷
│   ├── engine_scip.py     ← SCIP(MIP) solver
│   ├── engine_cpsat.py    ← CP-SAT solver
│   ├── runner.py          ← 실행 엔트리: solver 선택 + 시나리오 루프
│   └── comparator.py      ← 두 solver 결과 비교 검증
```

### 호출 구조

```python
from stress_test.runner import run_stress_test

# 단일 solver 실행
results = run_stress_test(solver_type="scip", scenarios=[...])
results = run_stress_test(solver_type="cpsat", scenarios=[...])

# 양쪽 실행 + 비교
from stress_test.comparator import compare_solvers
comparison = compare_solvers(scenarios=[...])
```

---

## 4. 공통 모듈 (common.py)

### 데이터 로드

```python
def load_problem_data(include_jungbu=True) -> ProblemData:
    """시군구 수요, 비용행렬, 현재 배정, RDC capacity 로드"""
```

### 시나리오 생성

```python
def create_scenarios(
    target_rdc: str | list[str],
    reduction_ratios: list[float],     # [0.0, 0.05, 0.10, 0.15, 0.20]
    receiver_buffer: float = 1.2,      # 수용 RDC 상한 배율
) -> list[Scenario]:
```

### 결과 포맷

```python
@dataclass
class ScenarioResult:
    scenario_id: str
    solver_type: str
    total_cost: float                  # 수요가중 이동시간 합
    cost_increase_pct: float           # Baseline 대비 증가율
    rdc_summary: pd.DataFrame          # RDC별 capacity, 배정수요, utilization
    sigungu_detail: pd.DataFrame       # 시군구별 배정 결과, 이동 여부
    moved_detail: pd.DataFrame         # 이동 시군구 상세
    runtime_sec: float                 # 실행 시간
    status: str                        # optimal / feasible / infeasible
```

---

## 5. SCIP 엔진 (engine_scip.py)

### 역할

- OR-Tools Linear Solver + SCIP backend
- MILP 기반 정석 모델
- **해석 및 검증 기준 모델**

### 구현

```python
def solve_scip(problem: ProblemData, scenario: Scenario) -> ScenarioResult:
    solver = pywraplp.Solver.CreateSolver("SCIP")
    # x_ij: 이진변수
    # 목적: min Σ(d_i × c_ij × x_ij)
    # 제약: 단일배정 + capacity
```

### 특징

- 선형 모델 표현 직관적
- 결과 해석 용이
- 실수(float) 직접 사용 가능

---

## 6. CP-SAT 엔진 (engine_cpsat.py)

### 역할

- OR-Tools CP-SAT solver
- 동일 문제를 정수 스케일링 후 구현
- **검증 모델 + 대규모 확장 시 성능 비교 대상**

### 구현

```python
def solve_cpsat(problem: ProblemData, scenario: Scenario) -> ScenarioResult:
    model = cp_model.CpModel()
    # x_ij: BoolVar
    # 목적: min Σ(scaled_d_i × scaled_c_ij × x_ij)
    # 제약: 단일배정 + capacity (스케일링된 값)
```

### 스케일링 정책

- demand: ×100 (소수점 2자리 보존)
- time: ×10 (소수점 1자리 보존)
- capacity: demand와 동일 스케일
- 결과 역변환 시 동일 스케일 적용

---

## 7. 비교기 (comparator.py)

### 비교 항목

| 항목 | 설명 |
|---|---|
| solver 상태 | optimal / feasible / infeasible 일치 여부 |
| 목적함수 | total_cost 차이 (스케일 보정 후) |
| 배정 결과 | 시군구별 assigned_rdc 일치율 |
| RDC별 load | 배정 수요 차이 |
| 실행 성능 | runtime 비교 |

### 해석 기준

| 결과 | 해석 |
|---|---|
| 목적값 동일, 배정 동일 | 모델 정상, 완전 일치 |
| 목적값 동일, 배정 일부 차이 | 동률 최적해 (정상) |
| 목적값 차이 | 스케일링/모델 불일치 의심 |
| infeasible 불일치 | 제약조건 구현 오류 |

---

## 8. 시나리오 설계

### 평택RDC 축소

| 시나리오 | capacity | 설명 |
|---|---|---|
| S0 | 100% | Baseline |
| S1 | 95% | 5% 축소 |
| S2 | 90% | 10% 축소 |
| S3 | 85% | 15% 축소 |
| S4 | 80% | 20% 축소 |

### 파라미터

- `target_rdc`: 리스트 (복수 RDC 동시 축소 가능)
- `receiver_buffer`: 수용 RDC 상한 배율 (기본 1.2)
- `include_jungbu`: 중부RDC 포함/제외
- `demand_col`: "daily_demand_3_5t" 또는 "daily_demand_5t"

---

## 9. 입력 데이터

| 데이터 | 파일 | 상태 |
|---|---|---|
| 시군구 수요 | `app/db/sigungu_demand.csv` | ✅ |
| RDC→시군구 비용행렬 | `app/db/cost_matrix.csv` | ✅ |
| 현재 RDC 배정 | `app/db/shipto_master.csv` | ✅ |
| RDC 위치 | `app/db/rdc_locations.json` | ✅ |

---

## 10. 결과 산출

### 시나리오 요약

- 총 이동시간, 비용 증가율
- 평택 최종 처리량, 이동 수요량, 이동 시군구 수

### RDC별 결과

- capacity, 배정 수요, utilization, 증감량

### 시군구별 결과

- current_rdc → assigned_rdc, 이동 여부, 시간 변화

### 비용 증가 곡선

- 축소율 vs 비용 증가율 → knee point 도출

---

## 11. 검증 전략

### 단계별 진행

| 단계 | 규모 | 목적 |
|---|---|---|
| Phase 1 | 시군구 20~30개, RDC 2~3개 | 모델 정확성 검증 |
| Phase 2 | 전체의 10~20% | 스케일링 검증 |
| Phase 3 | 전체 247개 | 본 실행 |

### Solver 운영 전략

| 단계 | 방식 |
|---|---|
| Phase 1 | SCIP + CP-SAT 병행, 결과 비교 |
| Phase 2 | 주력 solver 선정 (해석성 vs 속도 기준) |
| Phase 3 | 보조 solver는 샘플 검증 / 회귀 테스트용 유지 |

---

## 12. 주의사항

- SCIP와 CP-SAT의 스케일링 일관성 확보 (CP-SAT 정수화 시)
- 제주 제외
- 중부RDC 포함/제외 옵션
- target RDC를 리스트로 받아 복수 RDC 동시 축소 대응
- 5T 기준 수요로도 동일 분석 가능하도록 demand 컬럼 선택 지원
